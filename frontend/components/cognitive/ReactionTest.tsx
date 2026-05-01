"use client";

import { useEffect, useRef, useState } from "react";

const TRIALS = 10;
const MIN_DELAY_MS = 1000;
const MAX_DELAY_MS = 3000;

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
    if (phase === "instructions" || phase === "done") return;
    if (phase === "waiting") {
      cleanupTimer();
      setPhase("too_early");
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
        setPhase("instructions");
      }
    } else if (phase === "too_early") {
      setPhase("instructions");
    }
  };

  if (phase === "done") {
    return (
      <div className="kpi-card">
        <strong>Тест завершено</strong>
        <div>Медіана: {median(reactions)} мс • {reactions.length} спроб</div>
      </div>
    );
  }

  return (
    <div
      onClick={handleClick}
      style={{
        height: 240,
        borderRadius: 8,
        background:
          phase === "ready"
            ? "#1a73e8"
            : phase === "too_early"
              ? "#b00020"
              : "rgba(0,0,0,0.06)",
        color: phase === "ready" || phase === "too_early" ? "white" : "inherit",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "1.25rem",
        cursor: "pointer",
        userSelect: "none",
      }}
    >
      {phase === "instructions" && (
        <span>Натисніть, коли поле стане синім. Спроба {trial + 1}/{TRIALS}.</span>
      )}
      {phase === "waiting" && <span>Чекайте…</span>}
      {phase === "ready" && <span>Натисніть!</span>}
      {phase === "too_early" && <span>Зарано — натисніть, щоб повторити.</span>}
    </div>
  );
}
