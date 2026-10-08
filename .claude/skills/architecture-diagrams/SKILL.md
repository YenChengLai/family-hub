---
name: architecture-diagrams
description: Create or update Family Hub's architecture diagrams (Mermaid, C4-style) so they match the code. Use whenever a change adds, removes, or renames a service, container, router, middleware, platform service, module, data store, or deployment piece; when something marked "planned" gets built; or when asked for an architecture diagram.
---

# Architecture diagrams

Diagrams are code. Each diagram has **one source** in `docs/diagrams/<name>.mmd`.
`scripts/diagrams.py` copies it into the Markdown files that embed it, between
`<!-- diagram: <name> -->` and `<!-- /diagram -->`. Never edit an embedded copy.

## The views

| Source | Level | Shows | Embedded in |
|---|---|---|---|
| `system-context.mmd` | C4 L1 | People, Family Hub, external systems, the production/demo boundary | `docs/architecture*.md` |
| `containers.mmd` | C4 L2 | Running processes and data stores in production, and how requests flow | `README*.md`, `docs/architecture*.md` |
| `api-components.mmd` | C4 L3 | Layers inside the API: middleware → routers → dependencies → services → storage | `docs/architecture*.md` |

Add a new view only when a question cannot be answered by these (e.g. a
deployment/CI view in Phase 3). A new source must be embedded somewhere and
added to the table above and to `docs/contributing/diagrams.md`.

## Conventions

- `flowchart` syntax only (C4 Mermaid syntax renders poorly on GitHub).
- Labels in English: one source serves both languages.
- Anything not built yet gets `:::planned` (dashed border) with
  `classDef planned stroke-dasharray: 5 5`. Remove it in the PR that builds it.
- Data stores are cylinders `[( )]`; people are stadiums `([ ])`.
- Show layers and boundaries, not every call. If edges cross, link subgraphs
  instead of nodes.
- Reference rule or ADR IDs in labels where they explain a box (`AUTH-7`, `ADR-0010`).

## Workflow

1. **Collect facts from the code** (do not trust memory or old diagrams):
   - Routers: `grep -rn 'APIRouter(prefix=' apps/api/src`
   - Middleware order: `grep -n 'app.middleware' apps/api/src/family_hub/main.py`
     (registered last = outermost)
   - Platform services and modules: `ls apps/api/src/family_hub/platform apps/api/src/family_hub/modules`
   - Database schemas: `grep -rn '"schema"' apps/api/src`
   - Containers: `deploy/compose/compose*.yml`
2. **Edit** the `.mmd` source(s). Keep the header comment that states the level.
3. **Sync and validate**: `make diagrams`. This rewrites embedded copies, then
   checks sync, code facts (every router prefix and compose service appears in
   the diagrams), and renders each source with mermaid-cli.
4. **Look at the result.** Render PNGs and read them before committing:
   `pnpm exec mmdc -i docs/diagrams/<name>.mmd -o /tmp/<name>.png -b white -s 1.5`.
   Fix crossing edges, unreadable labels, or wrong groupings.
5. **Update the prose** next to the diagram if the explanation changed, in both
   `.md` and `.zh-TW.md` (bump `synced`).
6. Commit sources and embedded copies together. CI runs
   `scripts/diagrams.py --check --render`.

## Troubleshooting

- Render fails with a browser error: set `PUPPETEER_EXECUTABLE_PATH` to a
  local Chrome/Chromium, or run `pnpm rebuild puppeteer` to download one.
- `subgraph` ignores `direction LR` when it has edges to outside nodes. This is
  a Mermaid limitation; accept vertical stacking or restructure.
