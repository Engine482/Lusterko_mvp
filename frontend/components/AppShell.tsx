import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <span className="app-shell__brand">Люстерко</span>
        {/* Role switcher placeholder. Wired in Sprint 1 (TASK-1404). */}
      </header>
      <main className="app-shell__main">{children}</main>
    </div>
  );
}
