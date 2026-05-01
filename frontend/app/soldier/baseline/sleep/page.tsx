"use client";

import { useState } from "react";

import { BaselineProgress } from "@/components/BaselineProgress";
import { soldierApi } from "@/lib/api/soldier";
import { describeError } from "@/lib/api/utils";

// Wireframes P0 §5.5 — Baseline Sleep Screen (single 0-10 scale).
export default function BaselineSleepPage() {
  const [score, setScore] = useState<number>(5);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await soldierApi.submitSleep(score);
      window.location.assign("/soldier/baseline/reaction");
    } catch (err) {
      setError(describeError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <BaselineProgress current={3} />
      <h1>Сон</h1>
      <p>Оцініть якість сну за останній тиждень: 0 — дуже погано, 10 — чудово.</p>
      <form onSubmit={submit}>
        <input
          type="range"
          min={0}
          max={10}
          value={score}
          onChange={(e) => setScore(Number(e.target.value))}
          style={{ width: "100%" }}
        />
        <div style={{ fontSize: "1.5rem", textAlign: "center", margin: "8px 0" }}>
          {score}
        </div>
        {error && <div className="alert alert--error">{error}</div>}
        <button type="submit" className="btn" disabled={busy}>
          {busy ? "Збереження…" : "Далі"}
        </button>
      </form>
    </section>
  );
}
