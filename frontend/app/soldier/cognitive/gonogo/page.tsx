"use client";

import Link from "next/link";
import { useState } from "react";

import { GoNoGoTest } from "@/components/cognitive/GoNoGoTest";
import { soldierApi } from "@/lib/api/soldier";
import { humanError } from "@/lib/api/messages";

// Wireframes P0 §5.14 — periodic Go / No-Go (cognitive context).
export default function CognitiveGoNoGoPage() {
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const onDone = async (r: { commission: number; omission: number; validTrials: number }) => {
    try {
      await soldierApi.submitCognitiveGoNoGo(r.commission, r.omission, r.validTrials);
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
      <h1>Go / No-Go</h1>
      <p>Натискайте на синій (Go) і утримуйтесь на червоному (No-Go).</p>
      <GoNoGoTest onComplete={onDone} />
      {error && <div className="alert alert--error" style={{ marginTop: 12 }}>{error}</div>}
    </section>
  );
}
