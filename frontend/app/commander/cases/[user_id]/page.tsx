"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

import {
  commanderApi,
  type CommanderCaseCard,
} from "@/lib/api/commander";
import { humanError } from "@/lib/api/messages";
import { RISK_LABEL as STATUS_LABEL } from "@/lib/labels";

// Wireframes P0 §6.3 — Commander Case Card. Field policy enforced server-side
// per RBAC §6.2 — this UI only renders what the API returns.
export default function CommanderCaseCardPage({
  params,
}: {
  params: Promise<{ user_id: string }>;
}) {
  const { user_id } = use(params);
  const [card, setCard] = useState<CommanderCaseCard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    commanderApi
      .caseCard(user_id)
      .then((res) => {
        if (!cancelled) setCard(res);
      })
      .catch((err) => {
        if (!cancelled) setError(humanError(err));
      });
    return () => {
      cancelled = true;
    };
  }, [user_id]);

  if (error) return <div className="alert alert--error">{error}</div>;
  if (!card) return <p>Завантаження…</p>;

  return (
    <section>
      <Link href="/commander/cases">← До списку</Link>
      <h1 style={{ marginTop: 12 }}>{card.full_name}</h1>
      <p>Поточний статус: <strong>{STATUS_LABEL[card.current_risk_status]}</strong></p>
      {card.calculated_at && (
        <p className="text-muted" style={{ fontSize: "0.875rem" }}>
          Оновлено: {new Date(card.calculated_at).toLocaleString("uk-UA")}
        </p>
      )}
      {card.explanation_text && (
        <div className="kpi-card" style={{ marginTop: 12 }}>
          <strong>Пояснення</strong>
          <p style={{ marginTop: 4 }}>{card.explanation_text}</p>
        </div>
      )}

      <h2 style={{ marginTop: 24 }}>Динаміка (14 днів)</h2>
      {card.recent_status_trend.length === 0 ? (
        <p>Поки що немає подій.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 4 }}>
          {card.recent_status_trend.map((entry, idx) => (
            <li key={idx} style={{ display: "flex", justifyContent: "space-between" }}>
              <span>{STATUS_LABEL[entry.status]}</span>
              <span className="text-muted" style={{ fontSize: "0.8125rem" }}>
                {entry.at ? new Date(entry.at).toLocaleString("uk-UA") : "—"} · {entry.source}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
