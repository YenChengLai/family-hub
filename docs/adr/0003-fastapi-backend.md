# ADR-0003: FastAPI for the backend

- Status: Accepted
- Date: 2026-10-08

## Context

The author works in Python daily and uses FastAPI professionally. The
backend must expose a well-typed HTTP API for a separate frontend.

## Decision

Use FastAPI with SQLAlchemy 2.0 (async), Alembic for migrations, Pydantic v2
for schemas and settings, and uv for dependency and workspace management.

## Consequences

- OpenAPI is generated from the code, which enables the generated frontend
  client.
- Authentication, admin features, and RBAC are not built in. The platform
  layer must provide them, using established libraries rather than
  hand-rolled cryptography.

## Alternatives considered

- **Django (+ Django Ninja):** batteries included (auth, admin, ORM), but
  less flexible and outside the author's daily practice.
