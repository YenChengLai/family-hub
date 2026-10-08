# ADR-0009: Private access to production via Tailscale

- Status: Accepted
- Date: 2026-10-08

## Context

Family members need access from outside the home (for example, entering an
expense at a shop). The NAS holds other private family data. Opening router
ports exposes the NAS to the internet. Some ISPs place customers behind
CGNAT, where inbound connections are impossible anyway.

## Decision

- Production is reachable **only** over Tailscale (the official Synology
  package). No router port forwarding.
- HTTPS uses Tailscale-issued certificates for the `*.ts.net` hostname.
- Tailscale ACLs restrict members' devices to the app's port only.

## Consequences

- No public attack surface for production; works behind CGNAT.
- Every family device needs the Tailscale app. The free plan covers our user
  count.
- Depends on Tailscale's coordination service. Exit path: self-hosted
  Headscale.

## Alternatives considered

- **Synology VPN Server (OpenVPN or L2TP):** requires an open port, a public
  IP, and DDNS; older protocols.
- **Cloudflare Tunnel:** no open port, but the production app becomes
  publicly reachable.
