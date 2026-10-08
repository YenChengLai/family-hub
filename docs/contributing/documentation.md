# Documentation Guide

[繁體中文](documentation.zh-TW.md)

How docs in this repository are written and kept in sync with the code.
The reasoning is in [ADR-0011](../adr/0011-bilingual-docs-as-code.md).

## Kinds of docs

| Kind | Location | Written by | Languages |
|---|---|---|---|
| Overview, architecture, module design | `docs/*.md`, `docs/modules/` | Hand | English + zh-TW |
| Decisions | `docs/adr/` | Hand | English + zh-TW |
| Security | `docs/security/` | Hand | English + zh-TW |
| Operations runbooks | `docs/operations/` | Hand | English + zh-TW |
| Reference (API, ERD, permissions, config) | `docs/reference/` | **Generated** | English only |

## Rules

1. **Docs change in the same PR as the code.** If a PR changes behaviour, a
   business rule, an endpoint, a permission, or the deployment, it updates
   the matching doc.
2. **Docs first for features.** Update the module doc before or with the
   implementation, not after.
3. **English is canonical.** Write or change the English doc first, then
   update the `.zh-TW.md` translation in the same PR and bump its `synced`
   date.
4. **Never hand-edit generated docs.** Change the code and regenerate.
5. **Business rules have IDs** (e.g. `FIN-2`). Tests reference them in their
   names or docstrings so rules and tests can be traced both ways.
6. **Significant decisions get an ADR.** "Significant" means hard to
   reverse, or something a newcomer would ask "why?" about.

## Translation header

Every translation starts with:

```
<!-- translation-of: docs/path/to/file.md | synced: YYYY-MM-DD -->
```

If the English file changed after the `synced` date, the translation is
stale.

## Planned CI checks

These checks will be added with the code skeleton:

- Regenerate reference docs and fail on `git diff`.
- Every English doc has a `.zh-TW.md` counterpart with a valid header.
- Internal Markdown links resolve.
