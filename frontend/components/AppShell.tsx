import type { ReactNode } from "react";

import { LogoutButton } from "./LogoutButton";
import { RoleSwitcher } from "./RoleSwitcher";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <span className="app-shell__brand">Люстерко</span>
        <div className="app-shell__user-area">
          <RoleSwitcher />
          <LogoutButton />
        </div>
      </header>
      <main className="app-shell__main">{children}</main>
    </div>
  );
}
