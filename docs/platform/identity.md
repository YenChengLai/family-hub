# Identity: Accounts, Login, and Sessions

[繁體中文](identity.zh-TW.md)

How people get accounts, log in, and stay logged in. Decisions behind this
are in [ADR-0007](../adr/0007-cookie-session-auth.md).

## Concepts

| Concept | Meaning |
|---|---|
| **User** | A person with an e-mail (stored lower-case), display name, and password hash |
| **Household** | A tenant. All domain data belongs to exactly one household |
| **Membership** | Links a user to a household with a role: `owner`, `adult`, or `child` |
| **Session** | A server-side login record. The browser holds a random token in a cookie |

All tables live in the `platform` PostgreSQL schema.

## Rules

| ID | Rule |
|---|---|
| AUTH-1 | **No self-registration.** Households and members are created with the admin CLI. An in-app invitation flow may come later. |
| AUTH-2 | Passwords are 12–128 characters, with no composition rules (NIST SP 800-63B). Stored as Argon2id hashes; hashes are upgraded on login when parameters change. |
| AUTH-3 | A failed login never reveals whether the e-mail exists. Unknown e-mail and wrong password return the same 401 response, and take the same time (a dummy hash is verified). |
| AUTH-4 | **Rate limits.** At most 10 login attempts per client IP per minute. After 5 failed attempts for one account within 15 minutes, that account cannot log in until the window ends, even with the right password. A successful login resets the account's failure count. Limits are stored in Redis and fail closed. |
| AUTH-5 | The session token has 256 bits of randomness. Only its SHA-256 hash is stored. The cookie is `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`, without `Domain`, and named with the `__Host-` prefix. |
| AUTH-6 | A session ends after 14 days without use, 60 days after login, or immediately on logout. Logout revokes the session on the server, so a copied token stops working. Logging in again from the same browser revokes its previous session. |
| AUTH-7 | **CSRF.** Every state-changing request (not `GET`/`HEAD`/`OPTIONS`) must carry an `X-CSRF-Token` header. When the request has a session cookie, the header must equal `HMAC-SHA256(FH_SECRET_KEY, session token)`. Login only requires the header to be present. |
| AUTH-8 | Every API response carries `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`, and a restrictive `Content-Security-Policy`. |

## API

| Method & path | Auth | Purpose |
|---|---|---|
| `POST /api/v1/auth/login` | Public, rate-limited | Start a session. Returns user, memberships, and the CSRF token |
| `POST /api/v1/auth/logout` | Optional | Revoke the current session and clear the cookie. Always 204 |
| `GET /api/v1/auth/session` | Session | Current user, memberships, and CSRF token. 401 if not logged in |

The CSRF token is returned in the response body and kept in memory by the
web app. After a page reload the app calls `GET /auth/session` to get it
again.

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as API
    participant R as Redis
    participant P as PostgreSQL
    B->>A: POST /auth/login (X-CSRF-Token present)
    A->>R: count attempt per IP, check account lock
    A->>P: verify password (Argon2id)
    A->>P: insert session (token hash)
    A-->>B: Set-Cookie __Host-fh_session; body: csrf_token
    B->>A: POST /... (cookie + X-CSRF-Token)
    A->>A: header == HMAC(secret, token)?
    A->>P: session valid, not idle, not expired?
```

## Administration

```sh
uv run family-hub create-household --name "Our Family" --owner-email you@example.com --owner-name You
uv run family-hub add-member --household-id <id> --email partner@example.com --name Partner --role adult
```

Both prompt for the password. `seed-dev` creates fictional accounts and only
runs when `FH_ENVIRONMENT=development`.

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `FH_SECRET_KEY` | insecure dev value | Required in production, at least 32 random characters. Changing it invalidates all CSRF tokens; users simply reload |
| `FH_COOKIE_SECURE` | `true` | Must be `true` in production. Set `false` only for plain-HTTP local development |
| `FH_SESSION_IDLE_TIMEOUT` | 14 days | ISO 8601 duration, e.g. `P14D` |
| `FH_SESSION_ABSOLUTE_TIMEOUT` | 60 days | ISO 8601 duration, e.g. `P60D` |

## Deployment notes

- **Client IP behind a proxy.** The per-IP limit uses the connection's client
  address. Behind Caddy, run uvicorn with `--proxy-headers` and
  `--forwarded-allow-ips` set to the proxy's address. Otherwise every request
  appears to come from the proxy and all users share one limit.
- **Expired sessions** remain in the table until a cleanup job exists
  (planned with background jobs). They cannot be used.
