"use client";

import { useEffect, useRef, useState } from "react";

const TRIALS = 30;
const STIMULUS_MS = 800;
const ISI_MS = 600; // inter-stimulus interval
const NO_GO_RATIO = 0.25;

type Stimulus = "go" | "nogo" | null;

type Result = {
  commission: number;
  omission: number;
  validTrials: number;
};

type Props = {
  onComplete: (result: Result) => void;
};

type Trial = { kind: "go" | "nogo"; pressed: boolean };

export function GoNoGoTest({ onComplete }: Props) {
  const [phase, setPhase] = useState<"intro" | "running" | "done">("intro");
  const [stimulus, setStimulus] = useState<Stimulus>(null);
  const [trialIndex, setTrialIndex] = useState(0);
  const trialsRef = useRef<Trial[]>([]);
  const currentKindRef = useRef<"go" | "nogo" | null>(null);
  const pressedThisTrialRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const indexRef = useRef(0);

  const cleanupTimer = () => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => () => cleanupTimer(), []);

  const finalize = () => {
    let commission = 0;
    let omission = 0;
    for (const t of trialsRef.current) {
      if (t.kind === "go" && !t.pressed) omission += 1;
      if (t.kind === "nogo" && t.pressed) commission += 1;
    }
    setPhase("done");
    setStimulus(null);
    onComplete({
      commission,
      omission,
      validTrials: trialsRef.current.length,
    });
  };

  const scheduleNext = () => {
    if (indexRef.current >= TRIALS) {
      finalize();
      return;
    }
    setStimulus(null);
    timerRef.current = setTimeout(() => {
      const kind: "go" | "nogo" = Math.random() < NO_GO_RATIO ? "nogo" : "go";
      currentKindRef.current = kind;
      pressedThisTrialRef.current = false;
      setStimulus(kind);
      timerRef.current = setTimeout(() => {
        trialsRef.current.push({ kind, pressed: pressedThisTrialRef.current });
        indexRef.current += 1;
        setTrialIndex(indexRef.current);
        scheduleNext();
      }, STIMULUS_MS);
    }, ISI_MS);
  };

  const start = () => {
    trialsRef.current = [];
    indexRef.current = 0;
    setTrialIndex(0);
    setPhase("running");
    scheduleNext();
  };

  const handlePress = () => {
    if (phase !== "running" || stimulus === null) return;
    pressedThisTrialRef.current = true;
  };

  if (phase === "intro") {
    return (
      <div>
        <p>
          Натискайте на синій (Go) і не натискайте на червоний (No-Go).
          Усього {TRIALS} спроб. Будьте швидкими і точними.
        </p>
        <button type="button" className="btn" onClick={start}>
          Почати
        </button>
      </div>
    );
  }
  if (phase === "done") {
    return (
      <div className="kpi-card">
        <strong>Тест завершено</strong>
        <div style={{ marginTop: 4 }}>{TRIALS} спроб опрацьовано.</div>
      </div>
    );
  }

  const bg =
    stimulus === "go"
      ? "var(--accent)"
      : stimulus === "nogo"
        ? "var(--status-danger)"
        : "var(--bg-card)";

  return (
    <div>
      <div style={{ marginBottom: 8 }}>
        Спроба {trialIndex + 1}/{TRIALS}
      </div>
      <div
        onClick={handlePress}
        style={{
          height: 240,
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-card)",
          background: bg,
          cursor: "pointer",
          userSelect: "none",
        }}
      />
    </div>
  );
}
