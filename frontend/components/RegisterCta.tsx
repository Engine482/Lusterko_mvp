"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { authApi } from "@/lib/api/auth";

type Variant = "primary" | "link";

type Props = {
  variant?: Variant;
};

// Renders a "Зареєструватися" affordance only when DEMO_OPEN_REGISTRATION
// is enabled on the backend. Hides itself silently if the flag is off so
// invite-only deployments stay clean.
export function RegisterCta({ variant = "primary" }: Props) {
  const [enabled, setEnabled] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    authApi
      .config()
      .then((res) => {
        if (!cancelled) setEnabled(res.open_registration_enabled);
      })
      .catch(() => {
        if (!cancelled) setEnabled(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!enabled) return null;

  if (variant === "link") {
    return (
      <p style={{ marginTop: 16, fontSize: "0.875rem" }}>
        Немає акаунта? <Link href="/register">Зареєструватися</Link>
      </p>
    );
  }
  return (
    <p style={{ marginTop: 12 }}>
      <Link href="/register" className="btn btn--ghost">
        Зареєструватися
      </Link>
    </p>
  );
}
