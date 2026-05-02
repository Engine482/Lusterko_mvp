"use client";

import { useState } from "react";

import { authApi } from "@/lib/api/auth";
import { describeError } from "@/lib/api/utils";

// Sprint 7 — email+password login screen.
export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authApi.login(email, password);
      // /me decides where to send us next (role selection or role home).
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
    <section>
      <h1>Вхід у Lusterko</h1>
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
    </section>
  );
}
