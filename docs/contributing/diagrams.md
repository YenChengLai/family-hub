# Architecture Diagrams

[繁體中文](diagrams.zh-TW.md)

The architecture diagrams are Mermaid source files, kept in sync with the docs
and checked against the code in CI.

## Where they are

| Diagram | Shows | Appears in |
|---|---|---|
| System context | Users, Family Hub, external systems, production/demo isolation | [Architecture](../architecture.md) |
| Containers | Processes and data stores in production | [README](../../README.md), [Architecture](../architecture.md) |
| API components | Layers inside the API process | [Architecture](../architecture.md) |

A dashed border means planned, not yet built.

## How it works

- Each diagram has one source: `docs/diagrams/<name>.mmd`.
- Markdown files embed it between `<!-- diagram: <name> -->` and
  `<!-- /diagram -->`. `make diagrams` rewrites those blocks.
- Labels are English only, so both languages share one source.

## Checks

`scripts/diagrams.py --check` (pre-commit, `make docs-check`, CI) fails when:

- An embedded copy differs from its source.
- A source is not embedded anywhere, or a document embeds an unknown name.
- An API router prefix or a Docker Compose service is missing from the diagrams.

CI also renders every source with mermaid-cli, so syntax errors fail the build.

## Updating

Run `make diagrams` after editing a source. The full workflow and conventions
are in [`.claude/skills/architecture-diagrams/SKILL.md`](../../.claude/skills/architecture-diagrams/SKILL.md),
which AI assistants follow and humans can read.
