"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { soldierApi, type CompletionSummary } from "@/lib/api/soldier";
import { humanError } from "@/lib/api/messages";
import { RISK_LABEL } from "@/lib/labels";

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
        if (!cancelled) setError(humanError(err));
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
          Щоденне опитування: {summary.daily_due ? "Потрібно пройти" : "Виконано"}
        </li>
        <li className="kpi-card">
          Щотижнева переоцінка: {summary.weekly_due ? "Потрібно пройти" : "Виконано"}
        </li>
        <li className="kpi-card">
          Когнітивні завдання: {summary.cognitive_due ? "Потрібно пройти" : "Виконано"}
        </li>
        <li className="kpi-card">
          Поточний ризик:{" "}
          {summary.last_risk_status
            ? RISK_LABEL[summary.last_risk_status]
            : "ще не обчислюється"}
        </li>
      </ul>
      <p style={{ marginTop: 16 }}>
        <Link href="/soldier">Повернутися на головну</Link>
      </p>
    </section>
  );
}
