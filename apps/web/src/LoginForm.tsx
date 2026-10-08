import { useState, type FormEvent } from "react";

import { ApiError, login, type SessionInfo } from "./api";

const MESSAGES: Record<number, string> = {
  401: "Email 或密碼不正確",
  429: "嘗試次數過多，請稍後再試",
};

export function LoginForm({ onLogin }: { onLogin: (session: SessionInfo) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      onLogin(await login(email, password));
    } catch (err) {
      setError((err instanceof ApiError && MESSAGES[err.status]) || "登入失敗，請稍後再試");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h1>Family Hub</h1>
      <label>
        Email
        <input
          type="email"
          autoComplete="username"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </label>
      <label>
        密碼
        <input
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <button type="submit" disabled={busy}>
        {busy ? "登入中…" : "登入"}
      </button>
    </form>
  );
}
