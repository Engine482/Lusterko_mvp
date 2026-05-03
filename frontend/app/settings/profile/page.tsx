"use client";

import { useEffect, useState } from "react";

import { authApi } from "@/lib/api/auth";
import { localizeSettingsError } from "@/lib/api/messages";

// EPIC-84 / TASK-8403 — display name change.
export default function SettingsProfilePage() {
  const [fullName, setFullName] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    let cancelled = false;
    authApi
      .me()
      .then((me) => {
        if (cancelled) return;
        setFullName(me.user.full_name);
        setLoaded(true);
      })
      .catch(() => {
        if (cancelled) return;
        // Hand off to login if the session is gone.
        window.location.assign("/login");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(false);
    try {
      const res = await authApi.updateProfile(fullName);
      setFullName(res.user.full_name);
      setSuccess(true);
    } catch (err) {
      setError(localizeSettingsError(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (!loaded) {
    return <p>Завантаження…</p>;
  }

  return (
    <form className="form-grid" onSubmit={submit} noValidate>
      <h2>Профіль</h2>
      <label>
        Імʼя
        <input
          type="text"
          value={fullName}
          onChange={(e) => {
            setFullName(e.target.value);
            setSuccess(false);
          }}
          autoComplete="name"
          required
          maxLength={200}
        />
      </label>
      <button type="submit" className="btn" disabled={submitting}>
        {submitting ? "Збереження…" : "Зберегти"}
      </button>
      {success && <div className="alert alert--success" role="status">Імʼя оновлено.</div>}
      {error && <div className="alert alert--error" role="alert">{error}</div>}
    </form>
  );
}
