"use client";

import { useState } from "react";

import { BaselineProgress } from "@/components/BaselineProgress";
import { LikertScale } from "@/components/LikertScale";
import { soldierApi } from "@/lib/api/soldier";
import { describeError } from "@/lib/api/utils";

const QUESTIONS = [
  "Часто відчували, що не контролюєте важливі речі у своєму житті?",
  "Часто відчували, що вам важко справлятися з тим, що треба зробити?",
  "Часто відчували впевненість у власній здатності впоратись із труднощами?",
  "Часто відчували, що все йде так, як ви хочете?",
];

const OPTIONS = [
  { value: 0, label: "Ніколи" },
  { value: 1, label: "Майже ніколи" },
  { value: 2, label: "Іноді" },
  { value: 3, label: "Досить часто" },
  { value: 4, label: "Дуже часто" },
];

// Wireframes P0 §5.4 — Baseline PSS-4 Screen.
export default function BaselinePss4Page() {
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
      await soldierApi.submitPss4(answers as number[]);
      window.location.assign("/soldier/baseline/sleep");
    } catch (err) {
      setError(describeError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <BaselineProgress current={2} />
      <h1>PSS-4</h1>
      <p>Останні чотири тижні, наскільки часто ви відчували:</p>
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
