import Link from "next/link";

export const APP_VERSION = "v0.1.0";

export function AppFooter() {
  return (
    <footer className="app-shell__footer">
      <div className="app-shell__footer__line">
        <span>Люстерко MVP · Volodymyr Motornyi · 2026</span>
        <span aria-hidden="true" className="text-muted">·</span>
        <Link href="/about">Про систему</Link>
      </div>
      <span className="app-shell__footer__badge" aria-label="Версія збірки">
        P0 · {APP_VERSION} · demo
      </span>
    </footer>
  );
}
