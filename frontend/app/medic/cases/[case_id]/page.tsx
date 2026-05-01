"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

import { medicApi, type MedicCaseDetail } from "@/lib/api/medic";
import { describeError } from "@/lib/api/utils";
import type { CaseStatus } from "@/types/enums";

const CASE_LABEL: Record<CaseStatus, string> = {
  new: "Нове",
  in_review: "У роботі",
  monitoring: "Моніторинг",
  closed: "Закрите",
};

const STATUS_OPTIONS: CaseStatus[] = ["new", "in_review", "monitoring", "closed"];

// Wireframes P0 §7.2 — Medic Detailed Case View.
export default function MedicCaseDetailPage({
  params,
}: {
  params: Promise<{ case_id: string }>;
}) {
  const { case_id } = use(params);
  const [detail, setDetail] = useState<MedicCaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [noteText, setNoteText] = useState("");
  const [busy, setBusy] = useState(false);
  const [statusDraft, setStatusDraft] = useState<CaseStatus | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let cancelled = false;
    medicApi
      .getCase(case_id)
      .then((res) => {
        if (cancelled) return;
        setDetail(res);
        setStatusDraft(res.case_status);
      })
      .catch((err) => {
        if (!cancelled) setError(describeError(err));
      });
    return () => {
      cancelled = true;
    };
  }, [case_id, reload]);

  if (error) return <div className="alert alert--error">{error}</div>;
  if (!detail) return <p>Завантаження…</p>;

  const submitStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!statusDraft || statusDraft === detail.case_status) return;
    setBusy(true);
    setActionMsg(null);
    try {
      await medicApi.updateStatus(case_id, statusDraft);
      setActionMsg("Статус оновлено.");
      setReload((n) => n + 1);
    } catch (err) {
      setActionMsg(describeError(err));
    } finally {
      setBusy(false);
    }
  };

  const submitNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteText.trim()) return;
    setBusy(true);
    setActionMsg(null);
    try {
      await medicApi.addNote(case_id, noteText.trim());
      setNoteText("");
      setActionMsg("Нотатку додано.");
      setReload((n) => n + 1);
    } catch (err) {
      setActionMsg(describeError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <Link href="/medic">← До списку</Link>
      <h1 style={{ marginTop: 12 }}>{detail.user.full_name}</h1>
      <p>
        Кейс: <strong>{CASE_LABEL[detail.case_status]}</strong> · Ризик:{" "}
        <strong>{detail.risk.current_risk_status}</strong>
        {detail.risk.hard_flag && <> · Hard flag: <em>{detail.risk.hard_flag}</em></>}
      </p>
      {detail.risk.explanation_text && (
        <div className="kpi-card">{detail.risk.explanation_text}</div>
      )}

      <h2 style={{ marginTop: 24 }}>Останній daily</h2>
      {detail.latest_daily ? (
        <div className="kpi-card">
          <div>Дата: {detail.latest_daily.checkin_date}</div>
          <div>Сон: {detail.latest_daily.sleep_score}</div>
          <div>Енергія: {detail.latest_daily.energy_score}</div>
          <div>Настрій: {detail.latest_daily.mood_score}</div>
          <div>Концентрація: {detail.latest_daily.concentration_score}</div>
          {detail.latest_daily.comment_text && (
            <div style={{ marginTop: 8 }}>
              Коментар: <em>{detail.latest_daily.comment_text}</em>
            </div>
          )}
        </div>
      ) : (
        <p>Немає даних.</p>
      )}

      <h2 style={{ marginTop: 24 }}>Weekly</h2>
      <div className="kpi-card">
        <div>PHQ-4: {detail.latest_weekly.phq4_total ?? "—"} ({detail.latest_weekly.phq4_at ?? "—"})</div>
        <div>PSS-4: {detail.latest_weekly.pss4_total ?? "—"} ({detail.latest_weekly.pss4_at ?? "—"})</div>
      </div>

      <h2 style={{ marginTop: 24 }}>Cognitive</h2>
      <div className="kpi-card">
        <div>Reaction median: {detail.latest_cognitive.reaction_median_ms ?? "—"} мс ({detail.latest_cognitive.reaction_at ?? "—"})</div>
        <div>Go/No-Go commission: {detail.latest_cognitive.gonogo_commission_errors ?? "—"}</div>
        <div>Go/No-Go omission: {detail.latest_cognitive.gonogo_omission_errors ?? "—"} ({detail.latest_cognitive.gonogo_at ?? "—"})</div>
      </div>

      <h2 style={{ marginTop: 24 }}>AI summary</h2>
      <div className="kpi-card">
        <div>Parse: {detail.latest_ai.parse_status ?? "—"}</div>
        <div>Text risk: {detail.latest_ai.text_risk_level ?? "—"}</div>
        <div>Markers: {detail.latest_ai.markers.length ? detail.latest_ai.markers.join(", ") : "—"}</div>
        {detail.latest_ai.summary_for_system && (
          <div style={{ marginTop: 8 }}><em>{detail.latest_ai.summary_for_system}</em></div>
        )}
      </div>

      <h2 style={{ marginTop: 24 }}>Дії</h2>
      <form onSubmit={submitStatus} style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <select
          value={statusDraft ?? detail.case_status}
          onChange={(e) => setStatusDraft(e.target.value as CaseStatus)}
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {CASE_LABEL[s]}
            </option>
          ))}
        </select>
        <button type="submit" className="btn" disabled={busy}>
          Оновити статус
        </button>
      </form>

      <form onSubmit={submitNote} style={{ marginTop: 16 }}>
        <textarea
          value={noteText}
          onChange={(e) => setNoteText(e.target.value.slice(0, 4000))}
          rows={3}
          placeholder="Нотатка медика"
          style={{ width: "100%", padding: 8 }}
        />
        <button type="submit" className="btn" disabled={busy || !noteText.trim()}>
          Додати нотатку
        </button>
      </form>
      {actionMsg && <p style={{ marginTop: 8 }}>{actionMsg}</p>}

      <h2 style={{ marginTop: 24 }}>Нотатки</h2>
      {detail.notes.length === 0 ? (
        <p>Немає нотаток.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
          {detail.notes.map((n) => (
            <li key={n.id} className="kpi-card">
              <div style={{ fontSize: "0.8125rem", color: "rgba(0,0,0,0.6)" }}>
                {new Date(n.created_at).toLocaleString("uk-UA")}
              </div>
              <div style={{ marginTop: 4 }}>{n.text}</div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
