"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  commanderApi,
  type CommanderCaseRow,
} from "@/lib/api/commander";
import { humanError } from "@/lib/api/messages";
import { EmptyState, LoadingState } from "@/components/UiState";
import type { RiskStatus } from "@/types/enums";

const STATUS_LABEL: Record<RiskStatus, string> = {
  green: "Green",
  yellow: "Yellow",
  red: "Red",
  insufficient_data: "Недостатньо даних",
};

type FilterValue = RiskStatus | "all";

const FILTERS: FilterValue[] = ["all", "red", "yellow", "green", "insufficient_data"];

// Wireframes P0 §6.2 — Commander Cases List with name search + status filter.
export default function CommanderCasesPage() {
  const [cases, setCases] = useState<CommanderCaseRow[] | null>(null);
  const [filter, setFilter] = useState<FilterValue>("all");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    commanderApi
      .dashboardCases({
        status: filter === "all" ? undefined : filter,
        name: name.trim() || undefined,
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
  }, [filter, name]);

  if (error) return <div className="alert alert--error">{error}</div>;

  return (
    <section>
      <h1>Кейси підрозділу</h1>
      <div className="row">
        {FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            className="chip"
            aria-pressed={filter === f}
            onClick={() => setFilter(f)}
          >
            {f === "all" ? "Всі" : STATUS_LABEL[f]}
          </button>
        ))}
        <input
          type="search"
          placeholder="Пошук за іменем"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{
            flex: 1,
            minWidth: 200,
            padding: "10px 12px",
            background: "var(--bg-card)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-strong)",
            borderRadius: "var(--radius-input)",
            minHeight: "var(--tap-target)",
          }}
        />
      </div>

      {cases === null && <div style={{ marginTop: 12 }}><LoadingState /></div>}
      {cases && cases.length === 0 && (
        <div style={{ marginTop: 12 }}>
          <EmptyState
            title="Жодного кейсу"
            hint="Спробуйте змінити фільтр або очистити пошук за іменем."
          />
        </div>
      )}
      {cases && cases.length > 0 && (
        <div className="table-wrap" style={{ marginTop: 12 }}>
          <table className="table">
            <thead>
              <tr>
                <th>Боєць</th>
                <th>Статус</th>
                <th>Останній daily</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.user_id}>
                  <td>{c.full_name}</td>
                  <td>{STATUS_LABEL[c.current_risk_status]}</td>
                  <td>{c.last_daily_at ? new Date(c.last_daily_at).toLocaleString("uk-UA") : "—"}</td>
                  <td>
                    <Link href={`/commander/cases/${c.user_id}`}>Відкрити</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
