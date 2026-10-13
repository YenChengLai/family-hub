# Documentation

[繁體中文](index.zh-TW.md)

| Document | What it answers |
|---|---|
| [Vision & scope](vision.md) | Why this exists, who it is for, what is in and out of scope, roadmap |
| [Architecture](architecture.md) | How the system is structured and how modules plug in |
| [Development](development.md) | Setting up, running, and checking the code locally; CI |
| [Identity](platform/identity.md) | Accounts, login, sessions, CSRF, and rate limits (rules `AUTH-*`) |
| [Authorization](platform/authorization.md) | Roles, permissions, per-route access rules (rules `AUTHZ-*`) |
| [Audit log](platform/audit.md) | What is recorded and how it is protected (rules `AUDIT-*`) |
| [Finance module](modules/finance.md) | Domain model and business rules for shared and personal ledgers |
| [Threat model](security/threat-model.md) | What we protect, from whom, and how |
| [ADRs](adr/README.md) | Why each significant decision was made |
| [Documentation guide](contributing/documentation.md) | How docs are written, translated, and kept in sync with code |

## Generated reference

Produced from the code by `make generate` and verified in CI. English only. Do
not edit them by hand.

| Reference | Contents |
|---|---|
| [openapi.json](reference/openapi.json) | The API contract (OpenAPI 3) |
| [permissions.md](reference/permissions.md) | Permissions by role, and the access rule of every route |
| [configuration.md](reference/configuration.md) | Every `FH_*` environment variable |
| [database.md](reference/database.md) | ER diagram of every table |
