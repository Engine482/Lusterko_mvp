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
      <h1>{already ? "Ви вже пройшли щоденне опитування сьогодні" : "Дякуємо!"}</h1>
      <p>
        {already
          ? "Поверніться завтра — час наступного опитування ще не настав."
          : "Дані збережено."}
      </p>
      <Link className="btn" href="/soldier">
        Повернутися на головну
      </Link>
    </section>
  );
}
