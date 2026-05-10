"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { LikertScale } from "@/components/LikertScale";
import { soldierApi } from "@/lib/api/soldier";
import { humanError } from "@/lib/api/messages";

const PHQ4_QUESTIONS = [
  "Відчуття пригніченості або безнадії",
  "Втрата інтересу або задоволення",
  "Відчуття тривоги, напруження",
  "Неможливість зупинити або контролювати тривогу",
];

const PHQ4_OPTIONS = [
  { value: 0, label: "Зовсім ні" },
  { value: 1, label: "Кілька днів" },
  { value: 2, label: "Більше половини днів" },
  { value: 3, label: "Майже щодня" },
];

const PSS4_QUESTIONS = [
  "Часто відчували, що не контролюєте важливі речі у своєму житті?",
  "Часто відчували, що вам важко справлятися з тим, що треба зробити?",
  "Часто відчували впевненість у власній здатності впоратись із труднощами?",
  "Часто відчували, що все йде так, як ви хочете?",
];

const PSS4_OPTIONS = [
  { value: 0, label: "Ніколи" },
  { value: 1, label: "Майже ніколи" },
  { value: 2, label: "Іноді" },
  { value: 3, label: "Досить часто" },
  { value: 4, label: "Дуже часто" },
];

type Step = "phq4" | "pss4" | "done";

// Wireframes P0 §5.11 — Weekly Reassessment (PHQ-4 then PSS-4 in one flow).
export default function WeeklyReassessmentPage() {
  const [step, setStep] = useState<Step>("phq4");
  const [phq4, setPhq4] = useState<(number | null)[]>([null, null, null, null]);
  const [pss4, setPss4] = useState<(number | null)[]>([null, null, null, null]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [eligible, setEligible] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    soldierApi
      .completionSummary()
      .then((cs) => {
        if (cancelled) return;
        setEligible(cs.weekly_due);
      })
      .catch((err) => {
        if (!cancelled) setError(humanError(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const submitPhq4 = async (e: React.FormEvent) => {
    e.preventDefault();
    if (phq4.some((a) => a === null)) {
      setError("Дайте відповідь на всі питання.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await soldierApi.submitWeeklyPhq4(phq4 as number[]);
      setStep("pss4");
    } catch (err) {
      setError(humanError(err));
    } finally {
      setBusy(false);
    }
  };

  const submitPss4 = async (e: React.FormEvent) => {
    e.preventDefault();
    if (pss4.some((a) => a === null)) {
      setError("Дайте відповідь на всі питання.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await soldierApi.submitWeeklyPss4(pss4 as number[]);
      setStep("done");
    } catch (err) {
      setError(humanError(err));
    } finally {
      setBusy(false);
    }
  };

  if (eligible === false) {
    return (
      <section>
        <h1>Щотижнева переоцінка</h1>
        <p>Наступна доступна за тиждень після попередньої.</p>
        <Link className="btn" href="/soldier">Повернутися на головну</Link>
      </section>
    );
  }

  if (step === "done") {
    return (
      <section>
        <h1>Готово</h1>
        <p>Щотижневі результати збережено.</p>
        <Link className="btn" href="/soldier">Повернутися на головну</Link>
      </section>
    );
  }

  return (
    <section>
      <h1>Щотижнева переоцінка</h1>
      <p>Крок {step === "phq4" ? 1 : 2} з 2.</p>
      {step === "phq4" && (
        <form onSubmit={submitPhq4}>
          <h2>PHQ-4</h2>
          {PHQ4_QUESTIONS.map((q, i) => (
            <LikertScale
              key={i}
              label={q}
              value={phq4[i]}
              options={PHQ4_OPTIONS}
              onChange={(v) =>
                setPhq4((current) => {
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
      )}
      {step === "pss4" && (
        <form onSubmit={submitPss4}>
          <h2>PSS-4</h2>
          {PSS4_QUESTIONS.map((q, i) => (
            <LikertScale
              key={i}
              label={q}
              value={pss4[i]}
              options={PSS4_OPTIONS}
              onChange={(v) =>
                setPss4((current) => {
                  const next = [...current];
                  next[i] = v;
                  return next;
                })
              }
            />
          ))}
          {error && <div className="alert alert--error">{error}</div>}
          <button type="submit" className="btn" disabled={busy}>
            {busy ? "Збереження…" : "Зберегти результати"}
          </button>
        </form>
      )}
    </section>
  );
}
