"use client";

import { useEffect, useState } from "react";

import { authApi } from "@/lib/api/auth";
import { describeError } from "@/lib/api/utils";

// Wireframes P0 §4.1 — Invite Landing Screen.
export default function InviteLandingPage() {
  const [token, setToken] = useState<string>("");
  const [redirectUrl, setRedirectUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.resolve().then(() => {
      if (cancelled) return;
      const url = new URL(window.location.href);
      const t = url.searchParams.get("token") ?? url.searchParams.get("invite_token");
      if (t) setToken(t);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const start = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await authApi.start(token);
      setRedirectUrl(res.redirect_url);
      window.location.assign(res.redirect_url);
    } catch (err) {
      setError(describeError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section>
      <h1>Вхід за інвайтом</h1>
      <p>Введіть або підтвердіть інвайт-токен, отриманий від адміністратора.</p>
      <form className="form-grid" onSubmit={start}>
        <label>
          Invite token
          <input
            type="text"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="вставте токен"
            required
            minLength={10}
          />
        </label>
        <button type="submit" className="btn" disabled={loading}>
          {loading ? "Перенаправлення..." : "Увійти через Google"}
        </button>
        {error && <div className="alert alert--error">{error}</div>}
        {redirectUrl && (
          <div className="alert alert--ok">
            Якщо нічого не сталось, відкрийте: <a href={redirectUrl}>{redirectUrl}</a>
          </div>
        )}
      </form>
      <p style={{ fontSize: "0.875rem", marginTop: 24 }}>
        Інвайт одноразовий і має термін дії. Після успішного входу токен стає недійсним.
      </p>
    </section>
  );
}
