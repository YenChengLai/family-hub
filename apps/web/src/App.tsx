import { useEffect, useState } from "react";

import { getSession, logout, type SessionInfo } from "./api";
import { LoginForm } from "./LoginForm";

const ROLE_LABELS = { owner: "管理者", adult: "成員", child: "小孩" } as const;

type State = { kind: "loading" } | { kind: "error" } | { kind: "ready"; session: SessionInfo | null };

export function App() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    getSession()
      .then((session) => setState({ kind: "ready", session }))
      .catch(() => setState({ kind: "error" }));
  }, []);

  if (state.kind === "loading") return <main className="center">載入中…</main>;
  if (state.kind === "error") return <main className="center">無法連線到伺服器</main>;
  if (!state.session) {
    return (
      <main className="center">
        <LoginForm onLogin={(session) => setState({ kind: "ready", session })} />
      </main>
    );
  }

  const { user, memberships } = state.session;
  return (
    <main className="center">
      <section className="card">
        <h1>嗨，{user.display_name}</h1>
        <ul>
          {memberships.map((m) => (
            <li key={m.household_id}>
              {m.household_name}（{ROLE_LABELS[m.role]}）
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={() => logout().finally(() => setState({ kind: "ready", session: null }))}
        >
          登出
        </button>
      </section>
    </main>
  );
}
