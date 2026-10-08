# Audit Log

[繁體中文](audit.zh-TW.md)

A permanent record of who changed what, and when. It answers "who edited this
expense?" between family members, and supports investigation after an incident.

## Rules

| ID | Rule |
|---|---|
| AUDIT-1 | Every write made through the API or the admin CLI records an audit event **in the same transaction** as the change, so the change and its record commit or roll back together. Unchanged values are not recorded. |
| AUDIT-2 | The log is **append-only, enforced by PostgreSQL**: a trigger rejects every `UPDATE` and `DELETE` on `platform.audit_events`, whatever the application does. |
| AUDIT-3 | Events never contain secrets. Fields named `password`, `password_hash`, `token`, `token_hash`, or `secret` are dropped before writing. |
| AUDIT-4 | Events store user and household IDs **without foreign keys**, so they outlive the rows they describe. |

## Event fields

| Field | Meaning |
|---|---|
| `occurred_at` | Database time of the write |
| `source` | `api` or `cli` |
| `actor_user_id` | Who did it. Empty for CLI actions |
| `household_id` | The household affected. Empty for account events such as login |
| `action` | `<area>.<entity>.<verb>`, e.g. `platform.household.update` |
| `entity_type`, `entity_id` | What changed |
| `before`, `after` | Changed fields only (JSON) |

## Recorded actions

| Action | Source | Household |
|---|---|---|
| `auth.login`, `auth.logout` | api | — |
| `platform.household.create` | cli | ✓ |
| `platform.member.add` | cli | ✓ |
| `platform.household.update` | api | ✓ |

Owners read their household's events through
`GET /api/v1/households/{household_id}/audit-events` (see
[authorization.md](authorization.md#household-api)). Account events (login,
logout) are not shown there because they belong to no household.

## Not yet covered

- Failed logins are not audited; they are counted by the rate limiter
  ([identity.md](identity.md), AUTH-4).
- Retention: events are kept forever for now.
