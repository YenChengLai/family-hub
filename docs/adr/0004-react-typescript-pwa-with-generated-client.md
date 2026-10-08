# ADR-0004: React + TypeScript PWA with a generated API client

- Status: Accepted
- Date: 2026-10-08

## Context

The UI must work on iPhone and on the web. Running cost must stay near zero.
The author prefers Python and wants to write as little hand-maintained
TypeScript as possible.

## Decision

- React + TypeScript + Vite, shipped as an installable PWA.
- Generate the TypeScript API client and types from FastAPI's OpenAPI spec
  into `packages/api-client`. Never edit generated code by hand.
- TanStack Query for server state.

## Consequences

- No Apple Developer Program fee and no App Store review.
- Backend schema changes surface as frontend type errors at build time.
- iOS PWA limits apply: web push needs the app installed to the home screen;
  offline support is limited.

## Alternatives considered

- **Native app (Flutter, React Native):** needs a paid Apple developer
  account for long-term installs on iPhone.
- **Vue or Svelte:** viable, but a smaller ecosystem and less common in the
  job market.
- **Python UI frameworks (Reflex, NiceGUI):** not a real frontend/backend
  separation; weaker portfolio value.
