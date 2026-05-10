"use client";

import { useEffect, useState } from "react";

export default function RegisterSentPage() {
  const [email, setEmail] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    setEmail(url.searchParams.get("email") ?? "");
  }, []);

  return (
    <section className="auth-card">
      <h1>Перевірте пошту</h1>
      <p>
        Якщо вказана адреса {email ? <strong>{email}</strong> : "ваша адреса"}{" "}
        ще не зареєстрована, ми надіслали на неї лист із посиланням для
        підтвердження. Перейдіть за ним, щоб задати пароль і завершити
        реєстрацію.
      </p>
      <p className="text-muted" style={{ fontSize: "0.875rem", marginTop: 16 }}>
        Лист не приходить? Перевірте папку «Спам». Посилання дійсне 24 години.
      </p>
      <p style={{ marginTop: 24 }}>
        <a href="/login" className="btn btn--ghost">
          Повернутися на сторінку входу
        </a>
      </p>
    </section>
  );
}
