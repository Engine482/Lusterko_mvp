"use client";

import { useState } from "react";

import { authApi } from "@/lib/api/auth";
import { humanError } from "@/lib/api/messages";

const MIN_PASSWORD = 12;

function readTokenFromUrl(): string {
  if (typeof window === "undefined") return "";
  const url = new URL(window.location.href);
  return url.searchParams.get("token") ?? "";
}

export default function RegisterConfirmPage() {
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
      await authApi.demoRegisterConfirm({
        token,
        full_name: fullName.trim(),
        password,
      });
      // Tester gets three roles → role-selection screen handles the next hop.
      window.location.assign("/role");
    } catch (err) {
      setError(humanError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-card">
      <h1>Завершення реєстрації</h1>
      <p>
        Введіть ім&apos;я і задайте пароль. Після збереження ви відразу зайдете
        в систему з трьома демо-ролями.
      </p>
      <form className="form-grid" onSubmit={submit} noValidate>
        <label>
          Токен підтвердження
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
            required
            maxLength={200}
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
          {loading ? "Створення…" : "Завершити реєстрацію"}
        </button>
        {error && <div className="alert alert--error">{error}</div>}
      </form>
    </section>
  );
}
