# Vision & Scope

[繁體中文](vision.zh-TW.md)

## Vision

One private place where a family runs its shared everyday systems — money,
time, and errands — designed around how this family actually works, and
built so a new system can be added without reworking what exists.

## Users

| User | Today | Notes |
|---|---|---|
| Two adults (spouses) | Primary users | Use it on iPhone and on the web |
| Child | Future | Restricted role, added when old enough |
| Demo visitor | Future | Isolated sandbox only, never production (see [ADR-0010](adr/0010-isolated-public-demo.md)) |

## Goals

1. Show, at any moment, the month's total shared spending and how much each
   adult has paid.
2. Let each adult keep a private personal ledger.
3. Make adding a new module (calendar, shopping list, …) a matter of adding
   a package, not changing the platform.
4. Be safe to run at home and safe to publish as open source.
5. Cost close to nothing to run.

## Non-goals (for now)

- Bank or credit-card synchronization.
- Importing history from other apps. Past entries are typed in manually.
- Native iOS app. The PWA covers iPhone.
- Syncing with the iPhone Calendar app. A read-only ICS feed may come later.
- Any public exposure of the production instance.

## Roadmap

Each phase ships something usable before the next starts.

| Phase | Deliverable |
|---|---|
| 0. Design | This documentation set |
| 1. Platform skeleton | Monorepo, CI, auth, households, RBAC, audit log, generated docs |
| 2. Finance MVP | Shared ledger (observation mode) and personal ledger, see [finance.md](modules/finance.md) |
| 3. Home deployment | Docker Compose on the NAS, Tailscale access, backups with a tested restore |
| 4. Local demo | `docker compose up` with fictional seed data, screenshots in README |
| Later | Splits & settlements, income, AI-suggested categories, calendar, shopping list, cloud sandbox demo |
