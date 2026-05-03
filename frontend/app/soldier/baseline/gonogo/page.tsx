"use client";

import { useState } from "react";

import { BaselineProgress } from "@/components/BaselineProgress";
import { GoNoGoTest } from "@/components/cognitive/GoNoGoTest";
import { soldierApi } from "@/lib/api/soldier";
import { humanError } from "@/lib/api/messages";

// Wireframes P0 §5.7 — Baseline Go / No-Go.
export default function BaselineGoNoGoPage() {
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const onDone = async (r: { commission: number; omission: number; validTrials: number }) => {
    try {
      await soldierApi.submitGoNoGo(r.commission, r.omission, r.validTrials);
      setSubmitted(true);
      const completion = await soldierApi.completeBaseline();
      if (completion.baseline_completed) {
        window.location.assign("/soldier/baseline/complete");
      }
    } catch (err) {
      setError(humanError(err));
    }
  };

  return (
    <section>
      <BaselineProgress current={5} />
      <h1>Go / No-Go</h1>
      <p>Натискайте на синій (Go) і утримуйтесь на червоному (No-Go).</p>
      {!submitted && <GoNoGoTest onComplete={onDone} />}
      {error && <div className="alert alert--error" style={{ marginTop: 12 }}>{error}</div>}
    </section>
  );
}
