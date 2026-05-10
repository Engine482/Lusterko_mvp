"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { soldierApi, type CompletionSummary } from "@/lib/api/soldier";
import { humanError } from "@/lib/api/messages";

export default function CognitiveLauncherPage() {
  const [summary, setSummary] = useState<CompletionSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    soldierApi
      .completionSummary()
      .then((res) => {
        if (!cancelled) setSummary(res);
      })
      .catch((err) => {
        if (!cancelled) setError(humanError(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) return <div className="alert alert--error">{error}</div>;
  if (!summary) return <p>Завантаження…</p>;

  const allDone = !summary.reaction_test_due && !summary.go_no_go_due;

  return (
    <section>
      <h1>Когнітивні завдання</h1>
      <p>Виконуються двічі на тиждень. Оберіть задачу.</p>
      {allDone ? (
        <p>На сьогодні когнітивні завдання виконано. Поверніться пізніше.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 12 }}>
          {summary.reaction_test_due && (
            <li className="kpi-card">
              <strong>Тест реакції</strong>
              <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
                10 спроб. Натисніть на синій сигнал якомога швидше.
              </div>
              <Link
                className="btn"
                style={{ marginTop: 8, display: "inline-block" }}
                href="/soldier/cognitive/reaction"
              >
                Розпочати
              </Link>
            </li>
          )}
          {summary.go_no_go_due && (
            <li className="kpi-card">
              <strong>Go / No-Go</strong>
              <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
                30 спроб. Натискайте на синій (Go) і утримуйтесь на червоному (No-Go).
              </div>
              <Link
                className="btn"
                style={{ marginTop: 8, display: "inline-block" }}
                href="/soldier/cognitive/gonogo"
              >
                Розпочати
              </Link>
            </li>
          )}
        </ul>
      )}
      <p style={{ marginTop: 24, fontSize: "0.875rem" }}>
        <Link href="/soldier">Повернутися на головну</Link>
      </p>
    </section>
  );
}
