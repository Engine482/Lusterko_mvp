import Link from "next/link";
import type { ReactNode } from "react";

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <section className="settings">
      <h1>Налаштування</h1>
      <nav className="settings__nav" aria-label="Розділи налаштувань">
        <Link href="/settings/profile">Профіль</Link>
        <Link href="/settings/security">Безпека</Link>
      </nav>
      <div className="settings__body">{children}</div>
    </section>
  );
}
