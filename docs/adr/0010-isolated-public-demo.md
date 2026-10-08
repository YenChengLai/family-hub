# ADR-0010: Public demo is fully isolated from production

- Status: Accepted
- Date: 2026-10-08

## Context

The project is a portfolio piece. Interviewers should be able to try it.
Production holds real family data on a NAS that must stay private
([ADR-0009](0009-private-access-via-tailscale.md)).

## Decision

The public demo **never runs on the NAS** and never touches real data. It is
the same code deployed to separate infrastructure.

Phase 1 (with the MVP):
- `docker compose up` locally with fictional seed data.
- Screenshots and GIFs in the README.

Phase 2 (once stable):
- Deploy to free-tier cloud services (for example Cloud Run, Neon, Upstash,
  Cloudflare Pages). Check limits before launch.
- "Try the demo" creates an **ephemeral sandbox household** per visitor,
  with seed data and no sign-up or e-mail.
- Sandboxes expire after 24 hours; a nightly job wipes everything.
- Per-IP sandbox creation limits plus Cloudflare Turnstile.
- Sensitive features (password change, invites) disabled; data volume caps.

## Consequences

- A compromise of the demo cannot reach the home network.
- The sandbox design exercises multi-tenancy, RBAC, rate limiting, and data
  lifecycle in public.
- Free-tier limits and cold starts may make the demo slow. That is
  acceptable.

## Alternatives considered

- **Demo on the NAS behind Cloudflare Tunnel:** a container escape would
  expose family data. Rejected.
- **Frontend-only demo with a mocked API:** zero risk, but it shows none of
  the backend work. May be used as a supplement.
