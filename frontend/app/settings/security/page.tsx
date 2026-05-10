"use client";

import { useState } from "react";

import { authApi } from "@/lib/api/auth";
import { localizeSettingsError } from "@/lib/api/messages";

const MIN_PASSWORD = 12;

// EPIC-84 / TASK-8404 — in-session password change. Mirrors reset-password
// page validation rules (length policy + confirm match) so the UX is uniform.
export default function SettingsSecurityPage() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const reset = () => {
    setCurrent("");
    setNext("");
    setConfirm("");
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(false);
    if (next !== confirm) {
      setError("Паролі не співпадають.");
      return;
    }
    if (next.length < MIN_PASSWORD) {
      setError(`Пароль має містити мінімум ${MIN_PASSWORD} символів.`);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await authApi.passwordChange(current, next);
      setSuccess(true);
      reset();
    } catch (err) {
      setError(localizeSettingsError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="form-grid" onSubmit={submit} noValidate>
      <h2>Зміна паролю</h2>
      <label>
        Поточний пароль
        <input
          type="password"
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
          autoComplete="current-password"
          required
        />
      </label>
      <label>
        Новий пароль (мінімум {MIN_PASSWORD} символів)
        <input
          type="password"
          value={next}
          onChange={(e) => setNext(e.target.value)}
          autoComplete="new-password"
          required
          minLength={MIN_PASSWORD}
        />
      </label>
      <label>
        Підтвердіть новий пароль
        <input
          type="password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          autoComplete="new-password"
          required
          minLength={MIN_PASSWORD}
        />
      </label>
      <button type="submit" className="btn" disabled={submitting}>
        {submitting ? "Збереження…" : "Змінити пароль"}
      </button>
      {success && (
        <div className="alert alert--success" role="status">
          Пароль змінено
        </div>
      )}
      {error && <div className="alert alert--error" role="alert">{error}</div>}
    </form>
  );
}
