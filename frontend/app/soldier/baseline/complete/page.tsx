"use client";

import Link from "next/link";

// Wireframes P0 §5.8 — Baseline Completion Screen.
export default function BaselineCompletePage() {
  return (
    <section>
      <h1>Базовий профіль сформовано</h1>
      <p>
        Дякуємо. Ми зафіксували вашу персональну норму. З цього моменту короткі
        щоденні перевірки порівнюватимуться саме з вашим базовим профілем.
      </p>
      <Link className="btn" href="/soldier">
        Повернутися на головну
      </Link>
    </section>
  );
}
