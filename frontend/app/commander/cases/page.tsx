"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  commanderApi,
  type CommanderCaseRow,
} from "@/lib/api/commander";
import { describeError } from "@/lib/api/utils";
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
        if (!cancelled) setError(describeError(err));
      });
    return () => {
      cancelled = true;
    };
  }, [filter, name]);

  if (error) return <div className="alert alert--error">{error}</div>;

  return (
    <section>
      <h1>Кейси підрозділу</h1>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        {FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            className="btn"
            onClick={() => setFilter(f)}
            style={{ opacity: filter === f ? 1 : 0.5 }}
          >
            {f === "all" ? "Всі" : STATUS_LABEL[f]}
          </button>
        ))}
        <input
          type="search"
          placeholder="Пошук за іменем"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ flex: 1, minWidth: 200, padding: 8 }}
        />
      </div>

      {cases === null && <p style={{ marginTop: 12 }}>Завантаження…</p>}
      {cases && cases.length === 0 && <p style={{ marginTop: 12 }}>Немає кейсів.</p>}
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
