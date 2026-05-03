"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { authApi } from "@/lib/api/auth";

// Renders the Settings entry-point only when there is an active session.
// Mirrors LogoutButton's /me gate; both will collapse into a single user
// menu under TASK-8702 (lightweight redesign of AppShell header).
export function SettingsLink() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    authApi
      .me()
      .then(() => {
        if (!cancelled) setAuthenticated(true);
      })
      .catch(() => {
        if (!cancelled) setAuthenticated(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!authenticated) return null;
  return (
    <Link className="settings-link" href="/settings/profile">
      Налаштування
    </Link>
  );
}
