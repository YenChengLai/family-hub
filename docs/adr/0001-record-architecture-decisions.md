# ADR-0001: Record architecture decisions

- Status: Accepted
- Date: 2026-10-08

## Context

This project is long-lived, is maintained part-time, and doubles as a
portfolio. Future me, collaborators, and reviewers need to know *why* things
are the way they are, not only *what* they are.

## Decision

Record every significant decision as an ADR in `docs/adr/`, numbered
sequentially, using the sections Context / Decision / Consequences /
Alternatives considered. ADRs are immutable once accepted. A changed decision
gets a new ADR that supersedes the old one, and the old one's status is
updated to `Superseded by ADR-NNNN`.

## Consequences

- Decisions are reviewable in pull requests like code.
- A small writing cost for each significant change.

## Alternatives considered

- **Wiki or chat history:** drifts from the code and is not reviewed.
