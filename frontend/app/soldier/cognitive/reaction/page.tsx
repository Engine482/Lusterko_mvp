"use client";

import Link from "next/link";
import { useState } from "react";

import { ReactionTest } from "@/components/cognitive/ReactionTest";
import { soldierApi } from "@/lib/api/soldier";
import { humanError } from "@/lib/api/messages";

// Wireframes P0 §5.13 — periodic Reaction Test (cognitive context).
export default function CognitiveReactionPage() {
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const onDone = async (result: { medianMs: number; validTrials: number }) => {
    try {
      await soldierApi.submitCognitiveReaction(result.medianMs, result.validTrials);
      setDone(true);
    } catch (err) {
      setError(humanError(err));
    }
  };

  if (done) {
    return (
      <section>
        <h1>Готово</h1>
        <p>Результат збережено.</p>
        <Link className="btn" href="/soldier/cognitive">До задач</Link>
      </section>
    );
  }

  return (
    <section>
      <h1>Тест реакції</h1>
      <p>10 спроб. Натискайте, як тільки поле стає синім.</p>
      <ReactionTest onComplete={onDone} />
      {error && <div className="alert alert--error" style={{ marginTop: 12 }}>{error}</div>}
    </section>
  );
}
