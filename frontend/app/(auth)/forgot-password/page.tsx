"use client";

import { useState } from "react";

import { authApi } from "@/lib/api/auth";
import { describeError } from "@/lib/api/utils";

// Sprint 7 — anti-enumeration "forgot password" form. Backend always
// returns the same envelope; we render the same neutral confirmation
// regardless of whether the email matched a real account.
export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authApi.passwordForgot(email);
      setSubmitted(true);
    } catch (err) {
      setError(describeError(err));
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <section>
        <h1>Запит надіслано</h1>
        <p>
          Якщо введена адреса зареєстрована в Lusterko — на неї надійде лист
          із посиланням для скидання паролю. Посилання дійсне 1 годину.
        </p>
        <p>
          <a href="/login">Повернутись до входу</a>
        </p>
      </section>
    );
  }

  return (
    <section>
      <h1>Забули пароль?</h1>
      <p>
        Введіть email, на який зареєстровано акаунт. Ми надішлемо посилання
        для скидання паролю.
      </p>
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
        <button type="submit" className="btn" disabled={loading}>
          {loading ? "Надсилаємо..." : "Надіслати посилання"}
        </button>
        {error && <div className="alert alert--error">{error}</div>}
      </form>
      <p style={{ marginTop: 24 }}>
        <a href="/login">Назад до входу</a>
      </p>
    </section>
  );
}
