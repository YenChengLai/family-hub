# ADR-0006: Casbin RBAC with domains for authorization

- Status: Accepted; policy storage and watcher superseded by [ADR-0012](0012-code-defined-policies-roles-from-memberships.md)
- Date: 2026-10-08

## Context

Users belong to a household and hold a role within it. Modules define their
own permissions. The author already uses Casbin at work.

## Decision

Use pycasbin with the **RBAC with domains** model, where the domain is the
household:

```ini
[request_definition]
r = sub, dom, obj, act
[policy_definition]
p = sub, dom, obj, act
[role_definition]
g = _, _, _
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = g(r.sub, p.sub, r.dom) && r.dom == p.dom && keyMatch(r.obj, p.obj) && r.act == p.act
```

- Policies are stored in PostgreSQL via the SQLAlchemy adapter.
- Each module declares its permissions and default grants. The platform
  registers them at startup.
- Endpoints declare `require_permission(...)`. Default is deny.
- When policies change, a Redis watcher tells every worker to reload.
- Resource ownership (e.g. personal ledgers) is **not** modelled in Casbin.
  The service layer checks it.

## Consequences

- Industry-standard, well-understood model; matches the author's
  professional experience.
- Multi-worker deployments need the watcher, or permissions go stale.

## Alternatives considered

- **Hand-rolled role/permission tables:** simple, but reinvents a solved
  problem.
- **External policy engine (OPA, Oso Cloud):** overkill for this scale.
