"use client";

import { useEffect, useState } from "react";

import { RegisterCta } from "@/components/RegisterCta";
import { authApi } from "@/lib/api/auth";
import { humanError } from "@/lib/api/messages";

const ROLE_HOME: Record<string, string> = {
  soldier: "/soldier",
  commander: "/commander",
  medic_psych: "/medic",
  admin: "/admin",
};

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    authApi
      .me()
      .then((me) => {
        if (cancelled) return;
        if (me.role_selection_required) {
          window.location.replace("/role");
        } else if (me.active_role) {
          window.location.replace(ROLE_HOME[me.active_role]);
        }
      })
      .catch(() => {
        // Not authenticated — stay on the login form.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authApi.login(email, password);
      const me = await authApi.me();
      if (me.role_selection_required) {
        window.location.assign("/role");
        return;
      }
      window.location.assign(me.active_role ? ROLE_HOME[me.active_role] : "/");
    } catch (err) {
      setError(humanError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-card">
      <h1>Люстерко</h1>
      <p className="auth-card__intro">
        Люстерко — MVP системи моніторингу психологічного стану особового
        складу.
      </p>
      <h2>Вхід</h2>
      <form className="form-grid" onSubmit={submit} noValidate>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <label>
          Пароль
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        <button type="submit" className="btn" disabled={loading}>
          {loading ? "Вхід..." : "Увійти"}
        </button>
        {error && <div className="alert alert--error">{error}</div>}
      </form>
      <p style={{ marginTop: 24 }}>
        <a href="/forgot-password">Забули пароль?</a>
      </p>
      <RegisterCta variant="link" />
      <div className="disclaimer">
        Демо-версія. Дані використовуються лише для демонстрації MVP. Система не
        є медичним діагностичним інструментом.
      </div>
    </section>
  );
}
