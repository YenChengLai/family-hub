# Instructions for AI assistants

This file guides Claude Code (and other AI assistants) working in this repo.

## Project

Family Hub: a self-hosted household platform (finance first). Read
`docs/architecture.md` and the relevant `docs/modules/*.md` before changing
code. Decisions and their reasons are in `docs/adr/`.

## Non-negotiables

- **Public repository.** Never commit secrets, real names, real amounts, or
  any real household data. Seed and test data are fictional.
- **Docs move with code.** Any change to behaviour, business rules,
  endpoints, permissions, or deployment updates the matching docs in the
  same change. Follow `docs/contributing/documentation.md`.
- **Bilingual.** English docs are canonical. Update the `.zh-TW.md`
  translation in the same change and bump its `synced` date. Write the
  translation in Traditional Chinese (Taiwan usage).
- **Never hand-edit generated files** (`packages/api-client`,
  `docs/reference/`). Regenerate them.
- **Security by default.** Every endpoint declares a permission. Every query
  is scoped to the caller's household. No raw SQL string building. Update
  `docs/security/threat-model.md` when the attack surface changes.
- **Module boundaries.** No cross-module table access. See the module
  contract in `docs/architecture.md`.
- **Architecture diagrams** live in `docs/diagrams/*.mmd`. When a change
  affects services, routers, middleware, modules, or data stores, follow the
  `architecture-diagrams` skill and run `make diagrams`.
- **Significant decisions** get a new ADR. Do not edit accepted ADRs;
  supersede them.

## Commands

`make check` runs everything CI runs (lint, typecheck, tests, docs check).
See `docs/development.md` for setup and the full command list.

## Conventions

- Code, identifiers, commit messages: English.
- Dates `YYYY-MM-DD`. Money as integer minor units plus an ISO 4217 code.
- Business rules are referenced by ID (e.g. `FIN-2`) in tests.
