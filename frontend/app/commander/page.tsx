"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  commanderApi,
  type CommanderCaseRow,
  type CommanderSummary,
} from "@/lib/api/commander";
import { humanError } from "@/lib/api/messages";
import { RISK_LABEL } from "@/lib/labels";
import { EmptyState, LoadingState } from "@/components/UiState";
import type { RiskStatus } from "@/types/enums";

type FilterValue = RiskStatus | "all";

const STATUS_LABEL = RISK_LABEL;

const STATUS_BG: Record<RiskStatus, string> = {
  red: "var(--risk-red)",
  yellow: "var(--risk-yellow)",
  green: "var(--risk-green)",
  insufficient_data: "var(--risk-unknown)",
};

const FILTERS: FilterValue[] = ["all", "red", "yellow", "green", "insufficient_data"];

function filterLabel(value: FilterValue): string {
  if (value === "all") return "Усі рівні ризику";
  return STATUS_LABEL[value];
}

export default function CommanderUnitStatePage() {
  const [summary, setSummary] = useState<CommanderSummary | null>(null);
  const [cases, setCases] = useState<CommanderCaseRow[] | null>(null);
  const [filter, setFilter] = useState<FilterValue>("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      commanderApi.dashboardSummary(),
      commanderApi.dashboardCases(filter === "all" ? undefined : { status: filter }),
    ])
      .then(([s, c]) => {
        if (cancelled) return;
        setSummary(s);
        setCases(c.cases);
      })
      .catch((err) => {
        if (!cancelled) setError(humanError(err));
      });
    return () => {
      cancelled = true;
    };
  }, [filter]);

  if (error) return <div className="alert alert--error">{error}</div>;
  if (!summary) return <LoadingState />;

  return (
    <section>
      <h1>Стан підрозділу</h1>
      {summary.unit_id === null && (
        <div className="alert alert--info">
          Вашому акаунту не призначено підрозділ. Зверніться до адміна.
        </div>
      )}

      <ul className="kpi-grid">
        {(Object.keys(STATUS_LABEL) as RiskStatus[]).map((s) => (
          <li
            key={s}
            className="kpi-card"
            style={{ background: STATUS_BG[s], color: "white" }}
          >
            <div style={{ fontSize: "0.75rem", opacity: 0.8 }}>
              {STATUS_LABEL[s]}
            </div>
            <div style={{ fontSize: "1.5rem", fontWeight: 600 }}>
              {summary.counts[s]}
            </div>
          </li>
        ))}
      </ul>

      <label className="case-filter" style={{ marginTop: 24 }}>
        <span>Ризик</span>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as FilterValue)}
        >
          {FILTERS.map((f) => (
            <option key={f} value={f}>
              {filterLabel(f)}
            </option>
          ))}
        </select>
      </label>

      <h2 style={{ marginTop: 24 }}>Військовослужбовці</h2>
      {cases === null && <LoadingState />}
      {cases && cases.length === 0 && (
        <EmptyState
          title="Немає записів за обраним фільтром"
          hint="Спробуйте інший рівень ризику."
        />
      )}
      {cases && cases.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
          {cases.map((c) => (
            <li key={c.user_id} className="kpi-card">
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
                <span style={{ color: STATUS_BG[c.current_risk_status] }}>
                  {STATUS_LABEL[c.current_risk_status]}
                </span>
              </div>
              {c.explanation_text && (
                <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
                  {c.explanation_text}
                </div>
              )}
              <div style={{ marginTop: 8, fontSize: "0.8125rem" }}>
                <Link href={`/commander/cases/${c.user_id}`}>Деталі →</Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
