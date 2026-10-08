# ADR-0011: Bilingual docs-as-code, aligned with the code

- Status: Accepted
- Date: 2026-10-08

## Context

Docs must stay accurate as the code changes. Readers include the family
(Traditional Chinese) and international reviewers (English).

## Decision

- Docs live in `docs/` as Markdown and are reviewed in the same PR as the
  code they describe.
- **English is canonical.** Each hand-written doc `x.md` has a translation
  `x.zh-TW.md` whose first line is
  `<!-- translation-of: <path> | synced: YYYY-MM-DD -->`.
- **Generated references are English-only** and never hand-edited: OpenAPI
  spec, database ERD, permission matrix, configuration reference. CI
  regenerates them and fails on `git diff`.
- CI checks that every English doc has a translation, and that internal
  links resolve.
- A PR template checklist and the repo `CLAUDE.md` require doc updates
  alongside code changes.
- Published with MkDocs Material and its i18n plugin when there is enough to
  publish. Until then, read on GitHub.

See [documentation guide](../contributing/documentation.md).

## Consequences

- Drift in generated docs is impossible to merge. Drift in hand-written docs
  is caught by review and the checklist.
- Translations add work. AI assistants draft translations; a human reviews
  them.
