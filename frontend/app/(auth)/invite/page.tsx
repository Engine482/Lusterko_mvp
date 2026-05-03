"use client";

import { useState } from "react";

import { authApi } from "@/lib/api/auth";
import { describeError } from "@/lib/api/utils";

// Sprint 7 — Invite Landing: user lands here from the email link, sets a
// password (and optionally fixes their full name), and ends up logged in.
const MIN_PASSWORD = 12;

function readTokenFromUrl(): string {
  if (typeof window === "undefined") return "";
  const url = new URL(window.location.href);
  return (
    url.searchParams.get("token") ?? url.searchParams.get("invite_token") ?? ""
  );
}

export default function InviteLandingPage() {
  const [token, setToken] = useState<string>(readTokenFromUrl);
  const [fullName, setFullName] = useState("");
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
      await authApi.acceptInvite({
        token,
        full_name: fullName.trim() || undefined,
        password,
      });
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
      <h1>Вхід за інвайтом</h1>
      <p>
        Встановіть пароль для свого акаунта в Люстерку. Email — це той, на який
        вам надійшло запрошення.
      </p>
      <form className="form-grid" onSubmit={submit} noValidate>
        <label>
          Інвайт-токен
          <input
            type="text"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="вставте токен"
            required
            minLength={10}
          />
        </label>
        <label>
          Повне ім&apos;я
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Прізвище Ім'я"
            autoComplete="name"
          />
        </label>
        <label>
          Пароль (мінімум {MIN_PASSWORD} символів)
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
          Підтвердження паролю
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
          {loading ? "Встановлення..." : "Встановити пароль і увійти"}
        </button>
        {error && <div className="alert alert--error">{error}</div>}
      </form>
      <p style={{ fontSize: "0.875rem", marginTop: 24 }}>
        Інвайт одноразовий і має термін дії. Після успішного входу токен стає
        недійсним.
      </p>
    </section>
  );
}
