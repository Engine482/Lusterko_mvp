"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { medicApi, type MedicCaseRow } from "@/lib/api/medic";
import { describeError } from "@/lib/api/utils";
import type { CaseStatus, RiskStatus } from "@/types/enums";

const RISK_LABEL: Record<RiskStatus, string> = {
  green: "Green",
  yellow: "Yellow",
  red: "Red",
  insufficient_data: "Недостатньо даних",
};

const CASE_LABEL: Record<CaseStatus, string> = {
  new: "Нове",
  in_review: "У роботі",
  monitoring: "Моніторинг",
  closed: "Закрите",
};

type RiskFilter = RiskStatus | "all";
type CaseFilter = CaseStatus | "open";

const RISK_FILTERS: RiskFilter[] = ["all", "red", "yellow", "insufficient_data", "green"];
const CASE_FILTERS: CaseFilter[] = ["open", "new", "in_review", "monitoring", "closed"];

// Wireframes P0 §7.1 — Medic Priority Cases List.
export default function MedicCasesListPage() {
  const [cases, setCases] = useState<MedicCaseRow[] | null>(null);
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [caseFilter, setCaseFilter] = useState<CaseFilter>("open");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    medicApi
      .listCases({
        case_status: caseFilter === "open" ? undefined : caseFilter,
        risk: riskFilter === "all" ? undefined : riskFilter,
      })
      .then((res) => {
        if (!cancelled) setCases(res.cases);
      })
      .catch((err) => {
        if (!cancelled) setError(describeError(err));
      });
    return () => {
      cancelled = true;
    };
  }, [riskFilter, caseFilter]);

  if (error) return <div className="alert alert--error">{error}</div>;

  return (
    <section>
      <h1>Medic — Priority Cases</h1>
      <div className="stack" style={{ marginBottom: 16 }}>
        <div className="row">
          <span className="text-muted" style={{ alignSelf: "center" }}>Ризик:</span>
          {RISK_FILTERS.map((f) => (
            <button
              key={f}
              type="button"
              className="chip"
              aria-pressed={riskFilter === f}
              onClick={() => setRiskFilter(f)}
            >
              {f === "all" ? "Всі" : RISK_LABEL[f]}
            </button>
          ))}
        </div>
        <div className="row">
          <span className="text-muted" style={{ alignSelf: "center" }}>Кейс:</span>
          {CASE_FILTERS.map((f) => (
            <button
              key={f}
              type="button"
              className="chip"
              aria-pressed={caseFilter === f}
              onClick={() => setCaseFilter(f)}
            >
              {f === "open" ? "Відкриті" : CASE_LABEL[f]}
            </button>
          ))}
        </div>
      </div>

      {cases === null && <p>Завантаження…</p>}
      {cases && cases.length === 0 && <p>Немає кейсів.</p>}
      {cases && cases.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
          {cases.map((c) => (
            <li key={c.case_id} className="kpi-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <strong>{c.full_name}</strong>
                <span>{RISK_LABEL[c.current_risk_status]}</span>
              </div>
              <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
                Статус кейсу: {CASE_LABEL[c.case_status]} · відкрито {new Date(c.opened_at).toLocaleString("uk-UA")}
              </div>
              <Link
                style={{ marginTop: 8, display: "inline-block" }}
                href={`/medic/cases/${c.case_id}`}
              >
                Відкрити →
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
