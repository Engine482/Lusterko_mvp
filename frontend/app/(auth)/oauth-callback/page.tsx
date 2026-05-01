"use client";

import { useEffect, useState } from "react";

import { authApi } from "@/lib/api/auth";
import { describeError } from "@/lib/api/utils";
import type { Role } from "@/types/enums";

const HOME_PATH: Record<Role, string> = {
  soldier: "/soldier",
  commander: "/commander",
  medic_psych: "/medic",
  admin: "/admin",
};

// Wireframes P0 §4.2 — OAuth Callback / Redirect State.
// In dev-stub mode the backend redirects browser straight here after consuming
// the invite. We just probe /auth/me and route to the right home.
export default function OAuthCallbackPage() {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authApi
      .me()
      .then((me) => {
        if (me.role_selection_required) {
          window.location.assign("/role");
          return;
        }
        if (me.active_role) {
          window.location.assign(HOME_PATH[me.active_role]);
        }
      })
      .catch((err) => setError(describeError(err)));
  }, []);

  return (
    <section>
      <h1>Завершуємо вхід…</h1>
      {!error && <p>Будь ласка, зачекайте.</p>}
      {error && (
        <>
          <div className="alert alert--error">{error}</div>
          <p>
            <a href="/invite">Спробувати ще раз</a>
          </p>
        </>
      )}
    </section>
  );
}
