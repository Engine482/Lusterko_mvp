"use client";

import { useEffect, useRef, useState } from "react";

const TRIALS = 10;
const MIN_DELAY_MS = 1000;
const MAX_DELAY_MS = 3000;
const INTER_TRIAL_PAUSE_MS = 700;

type Phase = "instructions" | "waiting" | "ready" | "too_early" | "done";

type Result = { medianMs: number; validTrials: number };

type Props = {
  onComplete: (result: Result) => void;
};

function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return Math.round((sorted[mid - 1] + sorted[mid]) / 2);
  }
  return Math.round(sorted[mid]);
}

export function ReactionTest({ onComplete }: Props) {
  const [phase, setPhase] = useState<Phase>("instructions");
  const [trial, setTrial] = useState(0);
  const [reactions, setReactions] = useState<number[]>([]);
  const stimulusAtRef = useRef<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cleanupTimer = () => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => () => cleanupTimer(), []);

  const startTrial = () => {
    setPhase("waiting");
    const delay = MIN_DELAY_MS + Math.random() * (MAX_DELAY_MS - MIN_DELAY_MS);
    timerRef.current = setTimeout(() => {
      stimulusAtRef.current = performance.now();
      setPhase("ready");
    }, delay);
  };

  const handleClick = () => {
    if (phase === "done") return;
    if (phase === "instructions") {
      // First-tap kicks off the whole sequence; subsequent trials auto-advance.
      startTrial();
      return;
    }
    if (phase === "too_early") {
      // Premature click — restart this trial automatically after a short beat.
      timerRef.current = setTimeout(startTrial, INTER_TRIAL_PAUSE_MS);
      return;
    }
    if (phase === "waiting") {
      cleanupTimer();
      setPhase("too_early");
      timerRef.current = setTimeout(startTrial, INTER_TRIAL_PAUSE_MS);
      return;
    }
    if (phase === "ready" && stimulusAtRef.current !== null) {
      const rt = performance.now() - stimulusAtRef.current;
      stimulusAtRef.current = null;
      const next = [...reactions, rt];
      setReactions(next);
      const nextTrial = trial + 1;
      if (nextTrial >= TRIALS) {
        setPhase("done");
        onComplete({ medianMs: median(next), validTrials: next.length });
      } else {
        setTrial(nextTrial);
        setPhase("waiting");
        const delay = MIN_DELAY_MS + Math.random() * (MAX_DELAY_MS - MIN_DELAY_MS);
        timerRef.current = setTimeout(() => {
          stimulusAtRef.current = performance.now();
          setPhase("ready");
        }, INTER_TRIAL_PAUSE_MS + delay);
      }
    }
  };

  if (phase === "done") {
    return (
      <div className="kpi-card" role="status">
        <strong>Тест завершено</strong>
        <div>Медіана: {median(reactions)} мс • {reactions.length} спроб</div>
      </div>
    );
  }

  const label =
    phase === "instructions"
      ? `Почати — ${TRIALS} спроб поспіль`
      : phase === "waiting"
        ? `Чекайте сигналу… (${trial + 1}/${TRIALS})`
        : phase === "ready"
          ? `Натисніть! (${trial + 1}/${TRIALS})`
          : "Зарано — повторюємо спробу";

  const ariaHint =
    phase === "instructions"
      ? "Після старту спроби йтимуть автоматично. Натискайте, щойно поле стане синім."
      : phase === "ready"
        ? "Стимул показано — натисніть зараз."
        : phase === "waiting"
          ? "Очікування сигналу. Не натискайте, доки поле не стане синім."
          : "Передчасне натискання. Спроба повториться автоматично.";

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-live="polite"
      aria-label={ariaHint}
      style={{
        width: "100%",
        minHeight: 240,
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-card)",
        background:
          phase === "ready"
            ? "var(--accent)"
            : phase === "too_early"
              ? "var(--status-danger)"
              : "var(--bg-card)",
        color:
          phase === "ready"
            ? "var(--accent-fg)"
            : phase === "too_early"
              ? "var(--text-on-status)"
              : "var(--text-primary)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "1.25rem",
        cursor: "pointer",
        userSelect: "none",
        padding: 16,
        touchAction: "manipulation",
        font: "inherit",
      }}
    >
      {label}
    </button>
  );
}
