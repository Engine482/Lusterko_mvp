"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

// Wireframes P0 §5.10 — Daily Success / Confirmation.
export default function DailyConfirmationPage() {
  const [already, setAlready] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.resolve().then(() => {
      if (cancelled) return;
      const url = new URL(window.location.href);
      setAlready(url.searchParams.get("already") === "1");
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section>
      <h1>{already ? "Ви вже проходили daily сьогодні" : "Дякуємо!"}</h1>
      <p>
        {already
          ? "Поверніться завтра — для daily-check-in ще не настав час."
          : "Дані збережено. Поточний risk-статус та пояснення з’являться, коли буде запущено Risk Engine (Sprint 4)."}
      </p>
      <Link className="btn" href="/soldier">
        На головний екран
      </Link>
    </section>
  );
}
