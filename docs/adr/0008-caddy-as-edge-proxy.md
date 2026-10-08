# ADR-0008: Caddy as the edge proxy

- Status: Accepted
- Date: 2026-10-08

## Context

We need one component to serve the built frontend, proxy `/api` to FastAPI,
terminate TLS, and set security headers. The author uses Nginx at work. The
scale is a household.

## Decision

Use Caddy.

- Automatic HTTPS, including certificates for `*.ts.net` names from
  Tailscale.
- A short, readable Caddyfile with secure TLS defaults.
- Primary rate limiting lives in the application, which knows the user and
  endpoint. Edge rate limiting is optional and needs the `caddy-ratelimit`
  plugin (custom build).

## Consequences

- Less configuration and certificate maintenance.
- Edge rate limiting is not built in.
- The proxy is a thin, replaceable layer. Swapping it touches only
  `deploy/`.

## When to revisit

Switch to Nginx (or a cloud load balancer or ingress) if we need mature edge
rate limiting, high traffic handling, or an environment standardised on
Nginx.

## Alternatives considered

- **Nginx:** industry standard with built-in `limit_req`, but more verbose
  configuration and manual certificate handling.
- **Traefik:** label-based discovery shines with many services; unnecessary
  for one.
