# ADR-0012: Code-defined policies; roles read from memberships per request

- Status: Accepted
- Date: 2026-10-08
- Supersedes: the policy storage and Redis watcher parts of [ADR-0006](0006-casbin-rbac-with-domains.md)

## Context

ADR-0006 planned to store Casbin policies in PostgreSQL through the
SQLAlchemy adapter, and to keep workers in sync with a Redis watcher.
Implementing it showed two problems:

- **Two sources of truth.** Role assignments already live in the
  `memberships` table. Copying them into Casbin's `g` rules means every
  membership change must update both, or they drift.
- **Stale caches across processes.** The admin CLI adds members from a
  separate process. Each API worker holds its own in-memory enforcer, so a
  watcher would be required for correctness, not just performance.

Meanwhile nothing needs runtime-editable policies: permissions and their
grants to built-in roles are part of each module's code.

## Decision

- **Permission policies (`p`) are code.** Each module declares its
  permissions and grants in its `Module` descriptor. The platform builds an
  in-memory Casbin enforcer from them at startup. Policy changes are reviewed
  in pull requests.
- **The role hierarchy (`g`) is code:** `owner` ⊇ `adult` ⊇ `child`.
- **A user's role in a household is read from `memberships` on every
  request** (one indexed query). The household boundary is enforced by that
  lookup: non-members get 404.
- Casbin evaluates `role → permission`, including inheritance.

## Consequences

- One source of truth for membership; role changes apply on the next
  request in every process, with no watcher and no cache invalidation.
- No `casbin_rule` table and no adapter dependency.
- One extra query per household-scoped request. Negligible at our scale, and
  cacheable later if needed.
- Per-household custom roles or permissions are not possible. If they are
  ever needed, a new ADR will introduce stored policies.

## Alternatives considered

- **ADR-0006 as written (adapter + watcher):** rejected for the reasons in
  Context.
- **No Casbin, a plain dictionary:** would work today, but Casbin keeps the
  model familiar, handles inheritance, and leaves room for ABAC matchers.
