"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { soldierApi, type CompletionSummary, type OnboardingStatus } from "@/lib/api/soldier";
import { humanError } from "@/lib/api/messages";
import { relativeDayLabel } from "@/lib/dates";

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
        if (!cancelled) setError(humanError(err));
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

  const baselineDone = onboarding.baseline_completed;
  const allDone =
    baselineDone && !summary.daily_due && !summary.weekly_due && !summary.cognitive_due;

  return (
    <section>
      <h1>Привіт</h1>
      <p className="text-muted">{todayLabel}</p>

      <h2 style={{ marginTop: 24 }}>До виконання</h2>
      {!baselineDone && (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
          <li className="kpi-card">
            <strong>Завершіть базовий профіль</strong>
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
        </ul>
      )}

      {baselineDone && allDone && (
        <p>На сьогодні все виконано.</p>
      )}

      {baselineDone && !allDone && (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
          {summary.daily_due && (
            <li className="kpi-card">
              <strong>Щоденне опитування</strong>
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

          {summary.weekly_due && (
            <li className="kpi-card">
              <strong>Щотижнева переоцінка</strong>
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

          {summary.cognitive_due && (
            <li className="kpi-card">
              <strong>Когнітивні завдання</strong>
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
      )}

      {baselineDone && (
        <>
          <h2 style={{ marginTop: 24 }}>Виконано</h2>
          <ul
            className="kpi-card"
            style={{ listStyle: "none", padding: "var(--space-3) var(--space-4)", display: "grid", gap: 4 }}
          >
            {!summary.daily_due && <li>Щоденне опитування — сьогодні</li>}
            {!summary.weekly_due && <li>Щотижнева переоцінка — виконано</li>}
            {!summary.cognitive_due && <li>Когнітивні завдання — виконано</li>}
            {summary.daily_due && summary.weekly_due && summary.cognitive_due && (
              <li className="text-muted">Сьогодні нічого не виконано.</li>
            )}
          </ul>

          <h2 style={{ marginTop: 24 }}>Наступні задачі</h2>
          <ul
            className="kpi-card"
            style={{ listStyle: "none", padding: "var(--space-3) var(--space-4)", display: "grid", gap: 4 }}
          >
            <li>
              Щоденне опитування:{" "}
              <strong>{relativeDayLabel(summary.daily_next_due_at)}</strong>
            </li>
            <li>
              Щотижнева переоцінка:{" "}
              <strong>{relativeDayLabel(summary.weekly_next_due_at)}</strong>
            </li>
            <li>
              Когнітивні завдання:{" "}
              <strong>{relativeDayLabel(summary.cognitive_next_due_at)}</strong>
            </li>
          </ul>
        </>
      )}

      <p style={{ marginTop: 24, fontSize: "0.875rem" }}>
        <Link href="/soldier/summary">Перейти до підсумку</Link>
      </p>
    </section>
  );
}
