# Documentation

[繁體中文](index.zh-TW.md)

| Document | What it answers |
|---|---|
| [Vision & scope](vision.md) | Why this exists, who it is for, what is in and out of scope, roadmap |
| [Architecture](architecture.md) | How the system is structured and how modules plug in |
| [Development](development.md) | Setting up, running, and checking the code locally; CI |
| [Identity](platform/identity.md) | Accounts, login, sessions, CSRF, and rate limits (rules `AUTH-*`) |
| [Finance module](modules/finance.md) | Domain model and business rules for shared and personal ledgers |
| [Threat model](security/threat-model.md) | What we protect, from whom, and how |
| [ADRs](adr/README.md) | Why each significant decision was made |
| [Documentation guide](contributing/documentation.md) | How docs are written, translated, and kept in sync with code |

Generated references (API, database ERD, permissions, configuration) will
appear under `docs/reference/` once the code exists. They are produced from
the code and verified in CI. Do not edit them by hand.
