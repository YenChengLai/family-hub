import { useEffect, useState } from "react";

type ApiStatus = "checking" | "ok" | "unreachable";

export function App() {
  const [status, setStatus] = useState<ApiStatus>("checking");

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/v1/health", { signal: controller.signal })
      .then((res) => setStatus(res.ok ? "ok" : "unreachable"))
      .catch((err: unknown) => {
        if (!(err instanceof DOMException && err.name === "AbortError")) setStatus("unreachable");
      });
    return () => controller.abort();
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "1.5rem" }}>
      <h1>Family Hub</h1>
      <p>API: {status}</p>
    </main>
  );
}
