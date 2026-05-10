"use client";

import { useEffect, useState } from "react";

import { soldierApi } from "@/lib/api/soldier";
import { humanError } from "@/lib/api/messages";

const SCALES: { key: "sleep_score" | "energy_score" | "mood_score" | "concentration_score"; label: string }[] = [
  { key: "sleep_score", label: "Сон" },
  { key: "energy_score", label: "Енергія" },
  { key: "mood_score", label: "Загальний стан / настрій" },
  { key: "concentration_score", label: "Концентрація" },
];

// Wireframes P0 §5.9 — Daily Check-in (single screen).
export default function DailyCheckinPage() {
  const [scores, setScores] = useState({
    sleep_score: 5,
    energy_score: 5,
    mood_score: 5,
    concentration_score: 5,
  });
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    soldierApi
      .getDailyToday()
      .then((res) => {
        if (cancelled) return;
        if (res.already_submitted) {
          window.location.assign("/soldier/daily/confirmation?already=1");
        }
      })
      .catch((err) => {
        if (!cancelled) setError(humanError(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await soldierApi.submitDaily({
        ...scores,
        comment_text: comment.trim() || null,
      });
      window.location.assign("/soldier/daily/confirmation");
    } catch (err) {
      setError(humanError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <h1>Щоденне опитування</h1>
      <p>Швидко оцініть стан за сьогодні. Кожна шкала: 0 — погано, 10 — чудово.</p>
      <form onSubmit={submit}>
        {SCALES.map((s) => (
          <div key={s.key} style={{ marginBottom: 16 }}>
            <label style={{ display: "block", marginBottom: 4 }}>
              {s.label}: <strong>{scores[s.key]}</strong>
            </label>
            <input
              type="range"
              min={0}
              max={10}
              value={scores[s.key]}
              onChange={(e) =>
                setScores((current) => ({ ...current, [s.key]: Number(e.target.value) }))
              }
              style={{ width: "100%" }}
            />
          </div>
        ))}
        <label style={{ display: "block", marginBottom: 12 }}>
          Коментар (опціонально, до 300 символів)
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value.slice(0, 300))}
            rows={3}
            style={{ width: "100%", padding: 8, marginTop: 4 }}
          />
        </label>
        {error && <div className="alert alert--error">{error}</div>}
        <button type="submit" className="btn" disabled={busy}>
          {busy ? "Збереження…" : "Зберегти"}
        </button>
      </form>
    </section>
  );
}
