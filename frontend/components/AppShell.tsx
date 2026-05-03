import type { ReactNode } from "react";

import { AppFooter } from "./AppFooter";
import { LogoutButton } from "./LogoutButton";
import { RoleSwitcher } from "./RoleSwitcher";
import { SettingsLink } from "./SettingsLink";

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
          <SettingsLink />
          <LogoutButton />
        </div>
      </header>
      <main className="app-shell__main">{children}</main>
      <AppFooter />
    </div>
  );
}
