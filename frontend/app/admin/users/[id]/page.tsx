"use client";

import { useEffect, useState } from "react";

import { adminApi, type AdminUser, type IssuedInvite } from "@/lib/api/admin";
import { humanError } from "@/lib/api/messages";
import type { Role } from "@/types/enums";

const ALL_ROLES: Role[] = ["soldier", "commander", "medic_psych", "admin"];

type Props = { params: Promise<{ id: string }> };

// Wireframes P0 §8.4 — User Profile / Edit User.
export default function AdminUserProfilePage({ params }: Props) {
  const [id, setId] = useState<string | null>(null);
  const [user, setUser] = useState<AdminUser | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [invite, setInvite] = useState<IssuedInvite | null>(null);

  useEffect(() => {
    params.then((p) => setId(p.id));
  }, [params]);

  const reload = (uid: string) => {
    adminApi
      .getUser(uid)
      .then((res) => {
        setUser(res.user);
        setRoles(res.user.roles);
      })
      .catch((err) => setError(humanError(err)));
  };

  useEffect(() => {
    if (id) reload(id);
  }, [id]);

  if (!id || !user) return <p>Завантаження…</p>;

  const toggleRole = (role: Role) => {
    setRoles((current) =>
      current.includes(role) ? current.filter((r) => r !== role) : [...current, role],
    );
  };

  const saveRoles = async () => {
    try {
      await adminApi.setRoles(id, roles);
      reload(id);
    } catch (err) {
      setError(humanError(err));
    }
  };

  const generateInvite = async () => {
    setError(null);
    try {
      const res = await adminApi.issueInvite(id);
      setInvite(res);
    } catch (err) {
      setError(humanError(err));
    }
  };

  const toggleStatus = async () => {
    try {
      if (user.status === "active") {
        await adminApi.deactivate(id);
      } else {
        await adminApi.reactivate(id);
      }
      reload(id);
    } catch (err) {
      setError(humanError(err));
    }
  };

  return (
    <section>
      <h1>{user.full_name}</h1>
      <p>{user.email} — {user.status}</p>

      {error && <div className="alert alert--error">{error}</div>}

      <h2>Ролі</h2>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        {ALL_ROLES.map((role) => (
          <label key={role}>
            <input
              type="checkbox"
              checked={roles.includes(role)}
              onChange={() => toggleRole(role)}
            />{" "}
            {role}
          </label>
        ))}
      </div>
      <button type="button" className="btn" onClick={saveRoles} style={{ marginTop: 8 }}>
        Зберегти ролі
      </button>

      <h2 style={{ marginTop: 24 }}>Інвайт</h2>
      <button type="button" className="btn btn--ghost" onClick={generateInvite}>
        Видати новий інвайт
      </button>
      {invite && (
        <div className="alert alert--ok" style={{ marginTop: 8, wordBreak: "break-all" }}>
          <div>
            <strong>Token:</strong> {invite.token}
          </div>
          <div>Дійсний до: {new Date(invite.expires_at).toLocaleString()}</div>
          <div>
            Передайте посилання користувачу:{" "}
            <code>/invite?token={invite.token}</code>
          </div>
        </div>
      )}

      <h2 style={{ marginTop: 24 }}>Небезпечна зона</h2>
      <button type="button" className="btn btn--danger" onClick={toggleStatus}>
        {user.status === "active" ? "Деактивувати" : "Реактивувати"}
      </button>
    </section>
  );
}
