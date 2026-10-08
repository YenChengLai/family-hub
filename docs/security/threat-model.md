# Threat Model

[繁體中文](threat-model.zh-TW.md)

> Living document. Update it in any PR that changes authentication,
> authorization, network exposure, data storage, or dependencies.

## Assets

| Asset | Why it matters |
|---|---|
| Household financial data | Private. Leaks embarrass, can enable fraud or social engineering |
| User credentials and sessions | Grant access to everything above |
| The NAS itself | Also holds family photos and documents unrelated to this app |
| Repository and build pipeline | Public. A compromise ships malicious code into our home |

## Environments and trust boundaries

| Environment | Exposure | Data |
|---|---|---|
| Production (NAS) | Tailscale only. No router port forwarding | Real |
| Public demo (later) | Internet | Fictional only. Separate infrastructure. No path to the NAS |
| Local dev | localhost | Fictional only |

**Hard rule:** real data never leaves production; the public demo never runs
on the NAS ([ADR-0010](../adr/0010-isolated-public-demo.md)).

## Threat actors

| Actor | Applies to |
|---|---|
| Internet attacker or bot | Demo; production only if exposure rules are broken |
| Compromised or lost device on the tailnet | Production |
| Curious household member (e.g. a child later) | Production |
| Malicious demo visitor | Demo |
| Supply-chain attacker (dependency, image, CI action) | All |

## Threats and controls

| Threat (STRIDE) | Control |
|---|---|
| **Spoofing:** credential stuffing, brute force | Argon2id hashing; 10 login attempts per IP per minute; 5 failures lock an account for 15 minutes; identical responses for unknown e-mail and wrong password; no self-registration (AUTH-1 to AUTH-4). TOTP or passkeys later |
| **Spoofing:** stolen session | `__Host-` cookie with `HttpOnly`, `Secure`, `SameSite=Lax`; only the token hash is stored; server-side revocation on logout; 14-day idle and 60-day absolute timeouts; a new token on every login (AUTH-5, AUTH-6) |
| **Tampering:** CSRF | Same-origin deployment, no CORS, `SameSite` cookies, and a session-bound HMAC token in `X-CSRF-Token` on every state-changing request (AUTH-7) |
| **Tampering:** injection | Pydantic validation on every input; SQLAlchemy parameterized queries only; no raw SQL string building |
| **Repudiation** | Append-only audit log of every write, with actor, time, before and after |
| **Information disclosure:** cross-household access | `household_id` on every row; every query scoped by the caller's household; tests that try cross-tenant access |
| **Information disclosure:** personal ledger read by spouse | Ownership check in the service layer (FIN-5), with tests |
| **Information disclosure:** secrets in a public repo | `.env` git-ignored; gitleaks in pre-commit and CI; fictional seed data only |
| **Information disclosure:** XSS | React escaping by default; strict Content-Security-Policy; no `dangerouslySetInnerHTML` |
| **Denial of service** | Edge and app rate limits; request size limits; pagination caps |
| **Elevation of privilege** | Casbin deny-by-default; permission checks declared on every endpoint; a test that fails if any route lacks one |
| **Supply chain** | Lockfiles (uv, pnpm); Dependabot; pip-audit, pnpm audit; Trivy image scan; GitHub Actions pinned to commit SHAs |
| **Container breakout to NAS** | Non-root containers; read-only root filesystem where possible; no Docker socket mounts; only required volumes mounted |
| **Data loss** | Nightly encrypted `pg_dump`; off-site copy; restore rehearsed and documented |

## Security headers

`Strict-Transport-Security`, `Content-Security-Policy`,
`X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`,
`Permissions-Policy` (deny unused features), `frame-ancestors 'none'`.

## Residual risks (accepted for now)

- Tailscale's coordination server is a third party. Mitigation path:
  self-hosted Headscale.
- A single NAS is a single point of failure for availability. Backups cover
  data, not uptime.
- Per-IP login limits depend on the real client IP. A misconfigured proxy
  makes all users share one limit (see [identity.md](../platform/identity.md#deployment-notes)).
- Expired session rows are not yet deleted. They cannot be used, but the
  table grows until a cleanup job exists.
