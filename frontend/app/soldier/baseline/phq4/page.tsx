"use client";

import { useState } from "react";

import { BaselineProgress } from "@/components/BaselineProgress";
import { LikertScale } from "@/components/LikertScale";
import { soldierApi } from "@/lib/api/soldier";
import { humanError } from "@/lib/api/messages";

const QUESTIONS = [
  "Відчуття пригніченості або безнадії",
  "Втрата інтересу або задоволення",
  "Відчуття тривоги, напруження",
  "Неможливість зупинити або контролювати тривогу",
];

const OPTIONS = [
  { value: 0, label: "Зовсім ні" },
  { value: 1, label: "Кілька днів" },
  { value: 2, label: "Більше половини днів" },
  { value: 3, label: "Майже щодня" },
];

// Wireframes P0 §5.3 — Baseline PHQ-4 Screen.
export default function BaselinePhq4Page() {
  const [answers, setAnswers] = useState<(number | null)[]>([null, null, null, null]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (answers.some((a) => a === null)) {
      setError("Дайте відповідь на всі питання.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await soldierApi.submitPhq4(answers as number[]);
      window.location.assign("/soldier/baseline/pss4");
    } catch (err) {
      setError(humanError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <BaselineProgress current={1} />
      <h1>PHQ-4</h1>
      <p>Останні два тижні наскільки часто вас турбували такі стани?</p>
      <form onSubmit={submit}>
        {QUESTIONS.map((q, i) => (
          <LikertScale
            key={i}
            label={q}
            value={answers[i]}
            options={OPTIONS}
            onChange={(v) =>
              setAnswers((current) => {
                const next = [...current];
                next[i] = v;
                return next;
              })
            }
          />
        ))}
        {error && <div className="alert alert--error">{error}</div>}
        <button type="submit" className="btn" disabled={busy}>
          {busy ? "Збереження…" : "Далі"}
        </button>
      </form>
    </section>
  );
}
