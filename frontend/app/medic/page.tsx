"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { medicApi, type MedicCaseRow } from "@/lib/api/medic";
import { humanError } from "@/lib/api/messages";
import { CASE_STATUS_LABEL, RISK_LABEL } from "@/lib/labels";
import { EmptyState, LoadingState } from "@/components/UiState";
import type { CaseStatus } from "@/types/enums";

// P0.6: Тільки активно-небезпечні рівні (Норма / Недостатньо даних не є кейсом).
type RiskFilter = "all" | "red" | "yellow";
type CaseTab = "new" | "in_review" | "closed";

const RISK_FILTERS: RiskFilter[] = ["all", "red", "yellow"];

const CASE_TABS: { key: CaseTab; label: string; backendStatus: CaseStatus }[] = [
  { key: "new", label: "Нові", backendStatus: "new" },
  { key: "in_review", label: "В роботі", backendStatus: "in_review" },
  { key: "closed", label: "Закриті", backendStatus: "closed" },
];

function riskFilterLabel(value: RiskFilter): string {
  if (value === "all") return "Усі рівні ризику";
  return RISK_LABEL[value];
}

export default function MedicCasesListPage() {
  const [cases, setCases] = useState<MedicCaseRow[] | null>(null);
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [tab, setTab] = useState<CaseTab>("new");
  const [error, setError] = useState<string | null>(null);

  const filtersKey = `${tab}|${riskFilter}`;
  const [trackedKey, setTrackedKey] = useState(filtersKey);
  if (trackedKey !== filtersKey) {
    setTrackedKey(filtersKey);
    setCases(null);
    setError(null);
  }

  useEffect(() => {
    let cancelled = false;
    const status = CASE_TABS.find((t) => t.key === tab)!.backendStatus;
    medicApi
      .listCases({
        case_status: status,
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
  }, [riskFilter, tab]);

  if (error) return <div className="alert alert--error">{error}</div>;

  return (
    <section>
      <h1>Кейси</h1>

      <nav
        className="case-tabs"
        role="tablist"
        aria-label="Статус кейсу"
      >
        {CASE_TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            className="case-tab"
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <label className="case-filter">
        <span>Ризик</span>
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value as RiskFilter)}
        >
          {RISK_FILTERS.map((f) => (
            <option key={f} value={f}>
              {riskFilterLabel(f)}
            </option>
          ))}
        </select>
      </label>

      {cases === null && <LoadingState />}
      {cases && cases.length === 0 && (
        <EmptyState
          title="Жодного кейсу за обраними фільтрами"
          hint="Спробуйте інший статус або рівень ризику."
        />
      )}
      {cases && cases.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
          {cases.map((c) => (
            <li key={c.case_id} className="kpi-card">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "baseline",
                  gap: 8,
                  flexWrap: "wrap",
                }}
              >
                <strong>{c.full_name}</strong>
                <span>{RISK_LABEL[c.current_risk_status]}</span>
              </div>
              <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
                Статус кейсу: {CASE_STATUS_LABEL[c.case_status]} · відкрито{" "}
                {new Date(c.opened_at).toLocaleString("uk-UA")}
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
