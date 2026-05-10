"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const NAV: { href: string; label: string }[] = [
  { href: "/settings/profile", label: "Профіль" },
  { href: "/settings/security", label: "Зміна паролю" },
];

export default function SettingsLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <section className="settings">
      <h1>Налаштування</h1>
      <nav className="settings__nav" aria-label="Розділи налаштувань">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            aria-current={pathname === item.href ? "page" : undefined}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="settings__body">{children}</div>
    </section>
  );
}
