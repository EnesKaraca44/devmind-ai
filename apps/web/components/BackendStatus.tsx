"use client";

// "use client": bu bileşen TARAYICIDA çalışır (useState/useEffect sadece orada vardır).
// Dosyada bu satır olmazsa Next.js bileşeni varsayılan olarak SUNUCUDA çalıştırır.

import { useEffect, useState } from "react";
import { fetchHealth, type HealthResponse } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

export default function BackendStatus() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    fetchHealth()
      .then((data) => setState({ kind: "ok", data }))
      .catch((error: Error) =>
        setState({ kind: "error", message: error.message }),
      );
  }, []);

  if (state.kind === "loading") {
    return <p data-testid="backend-status">Backend kontrol ediliyor…</p>;
  }
  if (state.kind === "error") {
    return (
      <p data-testid="backend-status" className="text-red-600">
        Backend ulaşılamıyor: {state.message}
      </p>
    );
  }
  return (
    <p data-testid="backend-status" className="text-green-600">
      Backend bağlı: {state.data.service} ({state.data.status})
    </p>
  );
}
