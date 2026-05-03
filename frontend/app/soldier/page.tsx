"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { soldierApi, type CompletionSummary, type OnboardingStatus } from "@/lib/api/soldier";
import { describeError } from "@/lib/api/utils";

const STEP_LABEL: Record<string, string> = {
  phq4: "PHQ-4",
  pss4: "PSS-4",
  sleep: "Сон",
  reaction_test: "Тест реакції",
  go_no_go: "Go / No-Go",
};

const STEP_PATH: Record<string, string> = {
  phq4: "/soldier/baseline/phq4",
  pss4: "/soldier/baseline/pss4",
  sleep: "/soldier/baseline/sleep",
  reaction_test: "/soldier/baseline/reaction",
  go_no_go: "/soldier/baseline/gonogo",
};

// Wireframes P0 §5.1 — Soldier Home with due-state.
export default function SoldierHomePage() {
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
  const [summary, setSummary] = useState<CompletionSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([soldierApi.onboardingStatus(), soldierApi.completionSummary()])
      .then(([ob, cs]) => {
        if (cancelled) return;
        setOnboarding(ob);
        setSummary(cs);
      })
      .catch((err) => {
        if (!cancelled) setError(describeError(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) return <div className="alert alert--error">{error}</div>;
  if (!onboarding || !summary) return <p>Завантаження…</p>;

  const todayLabel = new Date().toLocaleDateString("uk-UA", {
    day: "numeric",
    month: "long",
    weekday: "long",
  });

  return (
    <section>
      <h1>Привіт</h1>
      <p className="text-muted">{todayLabel}</p>

      <h2 style={{ marginTop: 24 }}>До виконання</h2>
      <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
        {!onboarding.baseline_completed && (
          <li className="kpi-card">
            <strong>Завершіть baseline</strong>
            <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
              {onboarding.steps.filter((s) => s.completed).length} з 5 кроків
            </div>
            {onboarding.next_required_step && (
              <Link
                className="btn"
                style={{ marginTop: 8, display: "inline-block" }}
                href={STEP_PATH[onboarding.next_required_step]}
              >
                Продовжити: {STEP_LABEL[onboarding.next_required_step]}
              </Link>
            )}
          </li>
        )}

        {onboarding.baseline_completed && summary.daily_due && (
          <li className="kpi-card">
            <strong>Daily check-in</strong>
            <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
              4 короткі шкали і опціональний коментар.
            </div>
            <Link
              className="btn"
              style={{ marginTop: 8, display: "inline-block" }}
              href="/soldier/daily"
            >
              Пройти
            </Link>
          </li>
        )}

        {onboarding.baseline_completed && !summary.daily_due && (
          <li className="kpi-card">
            <strong>Daily — виконано</strong>
            <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
              Поверніться завтра.
            </div>
          </li>
        )}

        {onboarding.baseline_completed && summary.weekly_due && (
          <li className="kpi-card">
            <strong>Щотижневе перепроходження</strong>
            <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
              PHQ-4 + PSS-4. Займе кілька хвилин.
            </div>
            <Link
              className="btn"
              style={{ marginTop: 8, display: "inline-block" }}
              href="/soldier/weekly"
            >
              Пройти
            </Link>
          </li>
        )}

        {onboarding.baseline_completed && summary.cognitive_due && (
          <li className="kpi-card">
            <strong>Когнітивні задачі</strong>
            <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
              Тест реакції та Go / No-Go.
            </div>
            <Link
              className="btn"
              style={{ marginTop: 8, display: "inline-block" }}
              href="/soldier/cognitive"
            >
              До задач
            </Link>
          </li>
        )}
      </ul>

      <p style={{ marginTop: 24, fontSize: "0.875rem" }}>
        <Link href="/soldier/summary">Перейти до підсумку</Link>
      </p>
    </section>
  );
}
