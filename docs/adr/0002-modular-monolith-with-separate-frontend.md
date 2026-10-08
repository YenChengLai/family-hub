# ADR-0002: Modular monolith with a separate frontend

- Status: Accepted
- Date: 2026-10-08

## Context

We start with one module (finance) and expect more (calendar, shopping
list, and others not yet known). Each new module must plug in easily and
reuse authentication, households, and permissions. It runs on one NAS for a
household of 2–3 users. The project is also a portfolio piece, where a
clear API boundary is valuable.

## Decision

- Backend: one deployable FastAPI service containing a shared **platform**
  and independent **modules**, following the module contract in
  [architecture.md](../architecture.md).
- Frontend: a separate React SPA/PWA consuming the versioned HTTP API.
- Code lives in one monorepo.

## Consequences

- One process, one database, and one deploy keep operations cheap.
- Module rules (own schema, no cross-module table access) keep the option of
  extracting a module into its own service later.
- The separate frontend means two toolchains (uv and pnpm) and an API
  contract to maintain. We mitigate this with a generated client
  ([ADR-0004](0004-react-typescript-pwa-with-generated-client.md)).

## Alternatives considered

- **Microservices from day one:** too much operational overhead for this
  scale.
- **Server-rendered monolith (Django + HTMX):** less code, but a weaker API
  boundary and a less app-like experience on iPhone. Rejected in favour of
  the FastAPI stack ([ADR-0003](0003-fastapi-backend.md)).
