"use client";

import { useEffect, useState } from "react";

import { authApi, type AuthMe } from "@/lib/api/auth";
import { humanError } from "@/lib/api/messages";
import { ROLE_LABEL } from "@/lib/labels";
import type { Role } from "@/types/enums";

const HOME_PATH: Record<Role, string> = {
  soldier: "/soldier",
  commander: "/commander",
  medic_psych: "/medic",
  admin: "/admin",
};

export function RoleSwitcher() {
  const [me, setMe] = useState<AuthMe | null>(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authApi
      .me()
      .then(setMe)
      .catch((err) => setError(humanError(err)));
  }, []);

  if (!me) {
    return error ? <span className="role-switcher__error">{error}</span> : null;
  }
  if (me.roles.length <= 1) {
    return (
      <span className="role-switcher__static">
        {me.active_role ? ROLE_LABEL[me.active_role] : "—"}
      </span>
    );
  }

  const switchRole = async (role: Role) => {
    try {
      await authApi.selectRole(role);
      window.location.assign(HOME_PATH[role]);
    } catch (err) {
      setError(humanError(err));
    }
  };

  return (
    <div className="role-switcher">
      <button
        type="button"
        className="role-switcher__current"
        aria-label="Перемкнути активну роль"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        {me.active_role ? ROLE_LABEL[me.active_role] : "Оберіть роль"} ▾
      </button>
      {open && (
        <ul className="role-switcher__menu" role="menu">
          {me.roles.map((role) => (
            <li key={role} role="none">
              <button type="button" role="menuitem" onClick={() => switchRole(role)}>
                {ROLE_LABEL[role]}
              </button>
            </li>
          ))}
        </ul>
      )}
      {error && <span className="role-switcher__error">{error}</span>}
    </div>
  );
}
