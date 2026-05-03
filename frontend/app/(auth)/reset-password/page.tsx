"use client";

import { useState } from "react";

import { authApi } from "@/lib/api/auth";
import { describeError } from "@/lib/api/utils";

const MIN_PASSWORD = 12;

function readTokenFromUrl(): string {
  if (typeof window === "undefined") return "";
  const url = new URL(window.location.href);
  return url.searchParams.get("token") ?? "";
}

// Sprint 7 — Reset Password screen. Token comes in from the email link;
// successful submit logs the user in and redirects to their role home.
export default function ResetPasswordPage() {
  const [token, setToken] = useState<string>(readTokenFromUrl);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Паролі не співпадають.");
      return;
    }
    if (password.length < MIN_PASSWORD) {
      setError(`Пароль має містити мінімум ${MIN_PASSWORD} символів.`);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await authApi.passwordReset(token, password);
      const me = await authApi.me();
      if (me.role_selection_required) {
        window.location.assign("/role");
        return;
      }
      const home: Record<string, string> = {
        soldier: "/soldier",
        commander: "/commander",
        medic_psych: "/medic",
        admin: "/admin",
      };
      window.location.assign(me.active_role ? home[me.active_role] : "/");
    } catch (err) {
      setError(describeError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-card">
      <h1>Новий пароль</h1>
      <p>
        Задайте новий пароль для свого акаунта. Після збереження ви увійдете
        автоматично; усі попередні сесії будуть припинені.
      </p>
      <form className="form-grid" onSubmit={submit} noValidate>
        <label>
          Токен скидання
          <input
            type="text"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            required
            minLength={10}
          />
        </label>
        <label>
          Новий пароль (мінімум {MIN_PASSWORD} символів)
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
            minLength={MIN_PASSWORD}
          />
        </label>
        <label>
          Підтвердження
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            autoComplete="new-password"
            required
            minLength={MIN_PASSWORD}
          />
        </label>
        <button type="submit" className="btn" disabled={loading}>
          {loading ? "Збереження..." : "Зберегти пароль"}
        </button>
        {error && <div className="alert alert--error">{error}</div>}
      </form>
      <p style={{ marginTop: 24 }}>
        <a href="/login">Назад до входу</a>
      </p>
    </section>
  );
}
