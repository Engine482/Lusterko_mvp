"use client";

import { useEffect, useState } from "react";

import { authApi } from "@/lib/api/auth";
import { humanError } from "@/lib/api/messages";

// Demo open-registration entry: tester submits an email, backend mails a
// confirmation link, /register/sent renders the "check inbox" copy.
export default function RegisterPage() {
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    authApi
      .config()
      .then((res) => {
        if (!cancelled) setAllowed(res.open_registration_enabled);
      })
      .catch(() => {
        if (!cancelled) setAllowed(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await authApi.demoRegisterStart(email.trim());
      if (res.email_dispatch === "failed") {
        // Backend issued the registration but the mailer surfaced an SMTP
        // error. Show an honest message instead of the «Перевірте пошту»
        // success screen — P0.3 fix for the prod silent-success bug.
        setError(
          "Не вдалося надіслати лист підтвердження. Спробуйте ще раз або зверніться до адміністратора.",
        );
        setSubmitting(false);
        return;
      }
      window.location.assign(
        `/register/sent?email=${encodeURIComponent(email.trim())}`,
      );
    } catch (err) {
      setError(humanError(err));
      setSubmitting(false);
    }
  };

  if (allowed === false) {
    return (
      <section className="auth-card">
        <h1>Реєстрація недоступна</h1>
        <p>
          Demo-реєстрація наразі вимкнена. Зверніться до адміністратора по
          інвайт або поверніться на{" "}
          <a href="/login">сторінку входу</a>.
        </p>
      </section>
    );
  }

  return (
    <section className="auth-card">
      <h1>Demo-реєстрація</h1>
      <p>
        Введіть email — ми надішлемо лист із підтвердженням. Після переходу за
        посиланням ви задасте пароль і отримаєте тестовий акаунт із трьома
        ролями: військовослужбовець, командир, психолог.
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
        <button type="submit" className="btn" disabled={submitting}>
          {submitting ? "Надсилаємо…" : "Надіслати підтвердження"}
        </button>
        {error && <div className="alert alert--error">{error}</div>}
      </form>
      <p style={{ marginTop: 24, fontSize: "0.875rem" }}>
        Уже маєте акаунт? <a href="/login">Увійти</a>
      </p>
    </section>
  );
}
