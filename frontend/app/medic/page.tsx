"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { medicApi, type MedicCaseRow } from "@/lib/api/medic";
import { humanError } from "@/lib/api/messages";
import { CASE_STATUS_LABEL, RISK_LABEL } from "@/lib/labels";
import { EmptyState, LoadingState } from "@/components/UiState";
import type { CaseStatus, RiskStatus } from "@/types/enums";

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
        if (!cancelled) setError(humanError(err));
      });
    return () => {
      cancelled = true;
    };
  }, [riskFilter, caseFilter]);

  if (error) return <div className="alert alert--error">{error}</div>;

  return (
    <section>
      <h1>Пріоритетні кейси</h1>
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
              {f === "open" ? "Відкриті" : CASE_STATUS_LABEL[f]}
            </button>
          ))}
        </div>
      </div>

      {cases === null && <LoadingState />}
      {cases && cases.length === 0 && (
        <EmptyState
          title="Жодного активного кейсу"
          hint="Підберіть інший фільтр ризику або статус кейсу."
        />
      )}
      {cases && cases.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
          {cases.map((c) => (
            <li key={c.case_id} className="kpi-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <strong>{c.full_name}</strong>
                <span>{RISK_LABEL[c.current_risk_status]}</span>
              </div>
              <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
                Статус кейсу: {CASE_STATUS_LABEL[c.case_status]} · відкрито {new Date(c.opened_at).toLocaleString("uk-UA")}
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
