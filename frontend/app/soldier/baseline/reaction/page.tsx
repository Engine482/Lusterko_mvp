"use client";

import { useState } from "react";

import { BaselineProgress } from "@/components/BaselineProgress";
import { ReactionTest } from "@/components/cognitive/ReactionTest";
import { soldierApi } from "@/lib/api/soldier";
import { describeError } from "@/lib/api/utils";

// Wireframes P0 §5.6 — Baseline Reaction Test.
export default function BaselineReactionPage() {
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const onDone = async (result: { medianMs: number; validTrials: number }) => {
    try {
      await soldierApi.submitReactionTest(result.medianMs, result.validTrials);
      setSubmitted(true);
      window.location.assign("/soldier/baseline/gonogo");
    } catch (err) {
      setError(describeError(err));
    }
  };

  return (
    <section>
      <BaselineProgress current={4} />
      <h1>Тест реакції</h1>
      <p>10 спроб. Натискайте, як тільки поле стає синім.</p>
      {!submitted && <ReactionTest onComplete={onDone} />}
      {error && <div className="alert alert--error" style={{ marginTop: 12 }}>{error}</div>}
    </section>
  );
}
