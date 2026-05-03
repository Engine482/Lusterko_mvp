"use client";

import { useEffect, useState } from "react";

import { authApi } from "@/lib/api/auth";
import { describeError } from "@/lib/api/utils";

// Surfaces a logout affordance whenever there is an active session.
// Owns its own /me check so it can hide when no session is present
// (e.g. on /login). Until TASK-8405 introduces a unified user menu,
// this stays a sibling of RoleSwitcher in AppShell.
export function LogoutButton() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

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

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await authApi.logout();
    } catch (err) {
      setError(describeError(err));
      setSubmitting(false);
      return;
    }
    // Navigate via full reload so any in-memory client state (and the
    // back/forward cache) is dropped together with the cleared cookie.
    window.location.assign("/login");
  };

  return (
    <>
      <button
        type="button"
        className="logout-button"
        onClick={submit}
        disabled={submitting}
      >
        {submitting ? "Вихід…" : "Вийти"}
      </button>
      {error && <span className="logout-button__error">{error}</span>}
    </>
  );
}
