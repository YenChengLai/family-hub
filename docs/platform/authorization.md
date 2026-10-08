# Authorization: Roles, Permissions, and Access Rules

[繁體中文](authorization.zh-TW.md)

Who may do what. The design is in [ADR-0006](../adr/0006-casbin-rbac-with-domains.md)
and [ADR-0012](../adr/0012-code-defined-policies-roles-from-memberships.md).

## Rules

| ID | Rule |
|---|---|
| AUTHZ-1 | **Deny by default.** A permission nobody declared is never granted. |
| AUTHZ-2 | **Every route declares exactly one access rule:** `public`, `authenticated`, or `require_permission("<permission>")`. The API refuses to start if a route has none, more than one, or names an unknown permission. The set of public routes is pinned by a test. |
| AUTHZ-3 | **Roles inherit:** `owner` ⊇ `adult` ⊇ `child`. A permission granted to `child` is also held by `adult` and `owner`. |
| AUTHZ-4 | **Modules declare their own permissions** as `<module>.<resource>.<action>` and grant them to roles. Startup fails on a badly named, duplicated, or undeclared permission, or a feature-module route outside `/<module>`. |
| AUTHZ-5 | **Household-scoped routes include `{household_id}`.** The caller's role is read from `memberships` on every request. A caller who is not a member gets **404**, the same as for a household that does not exist, so IDs cannot be probed. A member without the permission gets 403. |

Ownership rules (for example, a personal ledger is visible only to its owner,
FIN-5) are not roles. They are checked in each module's service layer.

## Access rules

| Rule | Who passes | Used for |
|---|---|---|
| `public` | Anyone | Health checks, login, logout |
| `authenticated` | Any logged-in user | `GET /auth/session` |
| `require_permission(p)` | Members of `{household_id}` whose role holds `p` | Everything household-scoped |

## Platform permissions

| Permission | owner | adult | child |
|---|:-:|:-:|:-:|
| `platform.household.read` | ✓ | ✓ | ✓ |
| `platform.household.manage` | ✓ | — | — |
| `platform.audit.read` | ✓ | — | — |

Feature-module permissions are listed in each module's doc, for example
[finance.md](../modules/finance.md#permissions-initial).

## Household API

| Method & path | Permission | Purpose |
|---|---|---|
| `GET /api/v1/households/{household_id}` | `platform.household.read` | Name, time zone, members and their roles |
| `PATCH /api/v1/households/{household_id}` | `platform.household.manage` | Rename, change time zone (IANA name). Audited |
| `GET /api/v1/households/{household_id}/audit-events` | `platform.audit.read` | Latest audit events, newest first (`limit` 1–200, default 50) |

## Adding a module's permissions

```python
FINANCE = Module(
    name="finance",
    routers=(router,),  # every route starts with /finance
    permissions=(Permission("finance.transaction.create", "Record a transaction"),),
    grants={Role.ADULT: frozenset({"finance.transaction.create"})},  # owner inherits
)
```

Append the descriptor to `MODULES` in `apps/api/src/family_hub/modules/__init__.py`,
then protect each route with `Depends(require_permission("finance.transaction.create"))`.
