# ADR-0007: Server-side sessions in HttpOnly cookies

- Status: Accepted
- Date: 2026-10-08

## Context

The frontend and API are served from the same origin. Tokens stored in
`localStorage` can be stolen by any XSS. We want sessions that can be
revoked immediately (for example, a lost phone).

## Decision

- Server-side sessions identified by a random ID in a cookie with
  `HttpOnly; Secure; SameSite=Lax` (or `Strict` if it does not hurt UX).
- Session ID rotated on login; idle and absolute timeouts.
- CSRF protection on state-changing requests (token or required custom
  header).
- Passwords hashed with Argon2id.
- Keep the login flow behind an interface, so an OIDC provider can replace
  it later if non-Python services need single sign-on.

## Consequences

- Immediate revocation and no token-refresh complexity.
- Session lookups hit the store on each request. This is negligible at our
  scale.

## Alternatives considered

- **JWT access + refresh tokens:** stateless, but harder to revoke, and the
  usual `localStorage` storage is XSS-exposed.
- **Dedicated identity provider (Authentik, Keycloak):** heavy for a NAS
  (1–2 GB RAM). Revisit when a second, independent service needs SSO.
