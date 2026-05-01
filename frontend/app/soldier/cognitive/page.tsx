"use client";

import Link from "next/link";

// Wireframes P0 §5.12 — Cognitive Task Launcher.
export default function CognitiveLauncherPage() {
  return (
    <section>
      <h1>Когнітивні задачі</h1>
      <p>Виконуються двічі на тиждень. Оберіть задачу.</p>
      <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 12 }}>
        <li className="kpi-card">
          <strong>Тест реакції</strong>
          <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
            10 спроб. Натисніть на синій сигнал якомога швидше.
          </div>
          <Link
            className="btn"
            style={{ marginTop: 8, display: "inline-block" }}
            href="/soldier/cognitive/reaction"
          >
            Розпочати
          </Link>
        </li>
        <li className="kpi-card">
          <strong>Go / No-Go</strong>
          <div style={{ fontSize: "0.875rem", marginTop: 4 }}>
            30 спроб. Натискайте на синій (Go) і утримуйтесь на червоному (No-Go).
          </div>
          <Link
            className="btn"
            style={{ marginTop: 8, display: "inline-block" }}
            href="/soldier/cognitive/gonogo"
          >
            Розпочати
          </Link>
        </li>
      </ul>
    </section>
  );
}
