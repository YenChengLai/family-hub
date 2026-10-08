// Minimal hand-written API helper. Phase 1c replaces this with a client
// generated from the OpenAPI spec (docs/adr/0004-...).

export type Role = "owner" | "adult" | "child";

export interface SessionInfo {
  user: { id: string; email: string; display_name: string };
  memberships: { household_id: string; household_name: string; role: Role }[];
  csrf_token: string;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

// Held in memory only. On reload it is fetched again from /auth/session.
let csrfToken = "";

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") headers["X-CSRF-Token"] = csrfToken || "none";

  const response = await fetch(`/api/v1${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    credentials: "same-origin",
  });
  if (!response.ok) {
    const detail = await response
      .json()
      .then((data: { detail?: unknown }) => (typeof data.detail === "string" ? data.detail : ""))
      .catch(() => "");
    throw new ApiError(response.status, detail || response.statusText);
  }
  return (response.status === 204 ? undefined : await response.json()) as T;
}

function remember(session: SessionInfo): SessionInfo {
  csrfToken = session.csrf_token;
  return session;
}

export async function getSession(): Promise<SessionInfo | null> {
  try {
    return remember(await request<SessionInfo>("GET", "/auth/session"));
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) return null;
    throw err;
  }
}

export async function login(email: string, password: string): Promise<SessionInfo> {
  return remember(await request<SessionInfo>("POST", "/auth/login", { email, password }));
}

export async function logout(): Promise<void> {
  await request<unknown>("POST", "/auth/logout");
  csrfToken = "";
}
