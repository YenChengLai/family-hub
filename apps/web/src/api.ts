// Session helpers on top of the client generated from the OpenAPI spec
// (packages/api-client, regenerated with `make generate`).

import { authCurrentSession, authLogin, authLogout, type SessionOut } from "@family-hub/api-client";
import { client } from "@family-hub/api-client/client";

export type { Role, SessionOut as SessionInfo } from "@family-hub/api-client";

// Same origin as the page; the session cookie travels automatically.
client.setConfig({ baseUrl: "", credentials: "same-origin" });

// Held in memory only. On reload it is fetched again from /auth/session.
let csrfToken = "";

// Every state-changing request carries the CSRF token (AUTH-7).
client.interceptors.request.use((request) => {
  if (request.method !== "GET" && request.method !== "HEAD") {
    request.headers.set("X-CSRF-Token", csrfToken || "none");
  }
  return request;
});

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

function fail(response: Response | undefined, error: unknown): never {
  const detail =
    typeof error === "object" && error !== null && "detail" in error && typeof error.detail === "string"
      ? error.detail
      : "";
  throw new ApiError(response?.status ?? 0, detail || response?.statusText || "Network error");
}

function remember(session: SessionOut): SessionOut {
  csrfToken = session.csrf_token;
  return session;
}

export async function getSession(): Promise<SessionOut | null> {
  const { data, error, response } = await authCurrentSession();
  if (response?.status === 401) return null;
  if (!data) fail(response, error);
  return remember(data);
}

export async function login(email: string, password: string): Promise<SessionOut> {
  const { data, error, response } = await authLogin({ body: { email, password } });
  if (!data) fail(response, error);
  return remember(data);
}

export async function logout(): Promise<void> {
  const { error, response } = await authLogout();
  if (!response?.ok) fail(response, error);
  csrfToken = "";
}
