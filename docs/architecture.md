# Architecture

[繁體中文](architecture.zh-TW.md)

## Overview

Family Hub is a **modular monolith** with a **separate frontend**
([ADR-0002](adr/0002-modular-monolith-with-separate-frontend.md)). One
FastAPI process hosts a shared *platform* and any number of feature
*modules*. A React PWA talks to it via a typed client generated from the
OpenAPI spec.

> Diagrams are generated from `docs/diagrams/*.mmd` (labels in English for a single source).
> Edit the source, then run `make diagrams`. A dashed border means planned, not yet built.

### System context

Who uses the system, and the hard boundary between production and the public demo.

<!-- diagram: system-context -->
```mermaid
%% C4 level 1: who uses Family Hub and what it talks to. Dashed = planned.
flowchart LR
  family(["Family members<br/>2 adults, children later"])
  developer(["Developer<br/>with AI assistants"])
  visitor(["Demo visitor<br/>e.g. an interviewer"])

  subgraph home["Home · Tailscale only · no path to the demo"]
    hub["Family Hub<br/>production · real data"]
  end

  github["GitHub<br/>code · CI · Dependabot"]

  subgraph cloud["Public cloud · no path to home (ADR-0010)"]
    demo["Public demo<br/>fictional, ephemeral sandboxes"]:::planned
  end

  family -- "iPhone PWA, web" --> hub
  developer -- "pull requests" --> github
  github -. "deploys" .-> demo
  visitor -- "tries it" --> demo

  classDef planned stroke-dasharray: 5 5
```
<!-- /diagram -->

### Containers

The processes that run in production and how requests flow between them.

<!-- diagram: containers -->
```mermaid
%% C4 level 2: the running pieces in production. Dashed = planned.
flowchart LR
  subgraph devices["Family devices"]
    phone["iPhone<br/>PWA on home screen"]
    browser["Web browser"]
  end

  subgraph tailnet["Tailscale private network"]
    subgraph nas["Synology DS923+ · Docker Compose"]
      caddy["Caddy<br/>TLS · static files · reverse proxy"]:::planned
      web["Web app<br/>React + TypeScript PWA"]
      api["API<br/>FastAPI · platform + modules"]
      postgres[("PostgreSQL<br/>one schema per module")]
      redis[("Redis<br/>rate limits · ephemeral state")]
    end
  end

  phone -- "HTTPS" --> caddy
  browser -- "HTTPS" --> caddy
  caddy -- "/" --> web
  caddy -- "/api/*" --> api
  api -- "SQL" --> postgres
  api -- "counters" --> redis

  legend["Dashed border = planned"]:::legend

  classDef planned stroke-dasharray: 5 5
  classDef legend fill:none,stroke:none,font-style:italic
```
<!-- /diagram -->

The frontend and API share one origin (`/` and `/api`). This lets us use
`SameSite` session cookies without CORS ([ADR-0007](adr/0007-cookie-session-auth.md)).

## Repository layout

```
family-hub/
├── apps/
│   ├── api/                    # FastAPI service (uv)
│   │   ├── src/family_hub/
│   │   │   ├── platform/       # auth, users, households, rbac, audit
│   │   │   ├── modules/
│   │   │   │   └── finance/    # one package per module
│   │   │   ├── cli.py          # admin commands (no self-registration)
│   │   │   └── main.py         # app factory, module registration
│   │   ├── migrations/         # Alembic
│   │   └── tests/
│   └── web/                    # React + TS + Vite PWA (pnpm)
├── packages/
│   └── api-client/             # generated from OpenAPI, never hand-edited
├── deploy/                     # compose files, Caddyfile, backup scripts
└── docs/
```

## Platform

The platform owns everything that every module needs:

| Concern | Responsibility |
|---|---|
| Identity | Users, password hashing (Argon2id), sessions, CSRF. See [identity.md](platform/identity.md) |
| Tenancy | Households and memberships. Every domain row carries `household_id` |
| Authorization | Per-route access rules; Casbin RBAC with roles read from memberships. See [authorization.md](platform/authorization.md) |
| Audit | Append-only log of who changed what, when. See [audit.md](platform/audit.md) |
| Rate limiting | Redis-backed limits, stricter for auth endpoints |
| Module registry | Mounts each module's routers and registers its permissions from the explicit `MODULES` list |

### Inside the API

Every request passes through the same layers. Each layer only calls the one
below it.

<!-- diagram: api-components -->
```mermaid
%% C4 level 3: layers inside the API process. Each layer only calls the one below.
%% Dashed = planned.
flowchart TB
  request(["HTTP request · /api/v1/..."])

  subgraph middleware["1 · Middleware, outermost first"]
    direction LR
    headers["Security headers<br/>no-store · CSP (AUTH-8)"] --> csrf["CSRF check<br/>X-CSRF-Token (AUTH-7)"]
  end

  subgraph routers["2 · Routers"]
    direction LR
    health["/health"]
    auth["/auth<br/>login · logout · session"]
    households_router["/households/{id}<br/>household · audit events"]
    module_router["/finance, other modules"]:::planned
  end

  subgraph dependencies["3 · Request dependencies"]
    direction LR
    principal["Principal<br/>cookie → user"]
    permission["Access rule per route<br/>public · authenticated ·<br/>require_permission (AUTHZ-2)"]
    limiter["Rate limiter<br/>(AUTH-4)"]
    db["DB session<br/>1 transaction / request"]
  end

  subgraph services["4 · Services"]
    direction LR
    subgraph platform["Platform"]
      identity["identity"]
      households["households"]
      authz["authz<br/>module registry · Casbin"]
      audit["audit log<br/>append-only (AUDIT-2)"]
    end
    subgraph modules["Modules"]
      finance["finance"]:::planned
    end
  end

  subgraph stores["5 · Storage"]
    direction LR
    postgres[("PostgreSQL")]
    redis[("Redis")]
  end

  cli["Admin CLI<br/>family-hub"]

  request --> middleware --> routers --> dependencies --> services --> stores
  cli --> services

  classDef planned stroke-dasharray: 5 5
```
<!-- /diagram -->

### Roles

Roles are scoped to a household. Initial roles:

| Role | Intended for |
|---|---|
| `owner` | Manages the household, members, and roles |
| `adult` | Full use of the modules |
| `child` | Restricted. Exact permissions defined when needed |

Roles inherit: `owner` ⊇ `adult` ⊇ `child` (AUTHZ-3).

## Module contract

A module is a Python package under `modules/` that exposes one
`Module` descriptor, listed in `MODULES` (`modules/__init__.py`). The platform
consumes nothing else. The platform itself is described the same way
(`platform/module.py`).

| Part | Description |
|---|---|
| `name` | Unique slug, e.g. `finance`. Used for the URL prefix `/api/v1/<name>` and the DB schema |
| `routers` | FastAPI `APIRouter`s; every route starts with `/<name>` |
| `permissions` | Permissions the module defines, e.g. `finance.transaction.create` |
| `grants` | Which built-in roles get which permissions (inheritance applies) |
| models | SQLAlchemy models in the module's own PostgreSQL schema |

Rules that keep modules independent and extractable:

1. **No cross-module table access.** A module never joins or writes another
   module's tables. It calls the other module's service interface instead.
2. **One PostgreSQL schema per module** (`platform`, `finance`, …).
3. **Versioned API.** All routes live under `/api/v1/`.
4. **Authorization is declared, not hand-coded.** Every route declares one
   access rule, usually `require_permission("<module>.<resource>.<action>")`.
   The API refuses to start otherwise (AUTHZ-2).
5. **Ownership is checked in the service layer.** RBAC answers "may this role
   do this action". Rules like "only the owner sees a personal ledger" are
   checked in the module's service code.

The frontend mirrors this. Each module is a route folder plus a navigation
entry.

## API contract

FastAPI generates `openapi.json`. A TypeScript client and types are
generated from it into `packages/api-client`. Pydantic schemas are the single
source of truth for request and response shapes. CI regenerates the client
and fails if it differs from what is committed.

## Data

- **PostgreSQL** is the system of record ([ADR-0005](adr/0005-postgresql-and-redis.md)).
- **Redis** holds rate-limit counters, the Casbin policy-change channel, and
  later caches and background jobs. It holds nothing that cannot be lost.
- Money is stored as integer minor units plus an ISO 4217 currency code.
- Uploaded files (future) live on the filesystem, not in the database.

## Environments

| Environment | Where | Data | Reachability |
|---|---|---|---|
| Local dev | MacBook | Fictional seed | localhost |
| Production | Synology DS923+ | Real family data | Tailscale only ([ADR-0009](adr/0009-private-access-via-tailscale.md)) |
| Public demo (later) | Free-tier cloud, fully separate | Fictional, ephemeral sandboxes | Public ([ADR-0010](adr/0010-isolated-public-demo.md)) |
