"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { soldierApi, type CompletionSummary } from "@/lib/api/soldier";
import { describeError } from "@/lib/api/utils";

// Wireframes P0 §5.15 — Completion Summary.
export default function SoldierSummaryPage() {
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
        if (!cancelled) setError(describeError(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) return <div className="alert alert--error">{error}</div>;
  if (!summary) return <p>Завантаження…</p>;

  return (
    <section>
      <h1>Підсумок</h1>
      <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
        <li className="kpi-card">
          Daily: {summary.daily_due ? "Потрібно пройти" : "Виконано"}
        </li>
        <li className="kpi-card">
          Weekly: {summary.weekly_due ? "Потрібно пройти" : "Виконано"}
        </li>
        <li className="kpi-card">
          Cognitive: {summary.cognitive_due ? "Потрібно пройти" : "Виконано"}
        </li>
        <li className="kpi-card">
          Поточний risk: {summary.last_risk_status ?? "ще не обчислюється"}
        </li>
      </ul>
      <p style={{ marginTop: 16 }}>
        <Link href="/soldier">Повернутися на головний</Link>
      </p>
    </section>
  );
}
