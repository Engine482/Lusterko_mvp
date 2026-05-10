"use client";

import { useEffect, useState } from "react";

import { authApi, type AuthMe } from "@/lib/api/auth";
import { humanError } from "@/lib/api/messages";
import { ROLE_LABEL } from "@/lib/labels";
import type { Role } from "@/types/enums";

const ROLE_DESCRIPTION: Record<Role, string> = {
  soldier:
    "Проходити базовий профіль, щоденні опитування та когнітивні завдання.",
  commander: "Бачити стан підрозділу і пріоритетні кейси.",
  medic_psych: "Працювати з ризиковими кейсами і додавати нотатки.",
  admin: "Створювати користувачів, видавати інвайти, керувати ролями.",
};

const HOME_PATH: Record<Role, string> = {
  soldier: "/soldier",
  commander: "/commander",
  medic_psych: "/medic",
  admin: "/admin",
};

// Wireframes P0 §4.3 — Role Selection Screen.
export default function RoleSelectionPage() {
  const [me, setMe] = useState<AuthMe | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authApi
      .me()
      .then((res) => {
        // Bounce only when there is literally no choice to make: a single
        // role and an active session. Multi-role users who reach /role via
        // the «Змінити роль» menu item must always see the picker, even
        // when `role_selection_required` is false (they've already picked
        // once and are explicitly switching).
        if (res.roles.length <= 1 && res.active_role) {
          window.location.assign(HOME_PATH[res.active_role]);
          return;
        }
        setMe(res);
      })
      .catch((err) => setError(humanError(err)));
  }, []);

  const choose = async (role: Role) => {
    try {
      await authApi.selectRole(role);
      window.location.assign(HOME_PATH[role]);
    } catch (err) {
      setError(humanError(err));
    }
  };

  if (error) return <div className="alert alert--error">{error}</div>;
  if (!me) return <p>Завантаження…</p>;

  return (
    <section className="auth-card" style={{ maxWidth: 540 }}>
      <h1>Оберіть роль</h1>
      <p className="text-muted">
        У вас декілька ролей. Активна роль визначає доступні дані та інтерфейс.
      </p>
      <div className="stack" style={{ marginTop: 16 }}>
        {me.roles.map((role) => (
          <button
            key={role}
            type="button"
            className="btn btn--ghost"
            style={{ textAlign: "left", padding: "14px 18px", flexDirection: "column", alignItems: "flex-start" }}
            onClick={() => choose(role)}
          >
            <strong>{ROLE_LABEL[role]}</strong>
            <div className="text-muted" style={{ fontSize: "0.875rem", marginTop: 4 }}>
              {ROLE_DESCRIPTION[role]}
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
