import type { ReactNode } from "react";

import { AppFooter } from "./AppFooter";
import { AppNav } from "./AppNav";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <span className="app-shell__brand">Люстерко</span>
        <AppNav />
      </header>
      <main className="app-shell__main">{children}</main>
      <AppFooter />
    </div>
  );
}
