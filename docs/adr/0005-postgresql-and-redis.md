# ADR-0005: PostgreSQL as system of record, Redis for ephemeral state

- Status: Accepted
- Date: 2026-10-08

## Context

Data volume is small. Even decades of household records fit in tens of MB.
However, the system is long-lived, may later host several services, and
runs in containers anyway.

## Decision

- PostgreSQL from day one, one schema per module.
- Redis for rate-limit counters, Casbin policy-change notifications, and
  later caches and job queues. Redis must never hold data we cannot afford
  to lose.

## Consequences

- No future SQLite → PostgreSQL migration.
- Extra containers (about 100 MB RAM for PostgreSQL, a few MB for Redis) on
  a NAS with 4 GB or more.
- Backups need `pg_dump` rather than a file copy.

## Alternatives considered

- **SQLite:** enough for the data volume, but single-writer and awkward if a
  second service needs the data.
