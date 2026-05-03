"use client";

import { useEffect, useState } from "react";

import { adminApi, type AdminUnit } from "@/lib/api/admin";
import { humanError } from "@/lib/api/messages";
import type { Role } from "@/types/enums";

const ALL_ROLES: Role[] = ["soldier", "commander", "medic_psych", "admin"];

// Wireframes P0 §8.3 — Create User Screen.
export default function AdminCreateUserPage() {
  const [units, setUnits] = useState<AdminUnit[]>([]);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [unitId, setUnitId] = useState<string>("");
  const [roles, setRoles] = useState<Role[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [createdId, setCreatedId] = useState<string | null>(null);

  useEffect(() => {
    adminApi
      .listUnits()
      .then((res) => setUnits(res.items))
      .catch((err) => setError(humanError(err)));
  }, []);

  const toggleRole = (role: Role) => {
    setRoles((current) =>
      current.includes(role) ? current.filter((r) => r !== role) : [...current, role],
    );
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (roles.length === 0) {
      setError("Призначте хоча б одну роль.");
      return;
    }
    setError(null);
    try {
      const res = await adminApi.createUser({
        full_name: fullName,
        email,
        unit_id: unitId || null,
        roles,
      });
      setCreatedId(res.user.id);
    } catch (err) {
      setError(humanError(err));
    }
  };

  if (createdId) {
    return (
      <section>
        <h1>Користувача створено</h1>
        <p>
          Перейдіть до <a href={`/admin/users/${createdId}`}>картки користувача</a> та видайте
          інвайт.
        </p>
      </section>
    );
  }

  return (
    <section>
      <h1>Новий користувач</h1>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Повне ім&apos;я
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </label>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Підрозділ
          <select value={unitId} onChange={(e) => setUnitId(e.target.value)}>
            <option value="">— без підрозділу —</option>
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </label>
        <fieldset>
          <legend>Ролі</legend>
          {ALL_ROLES.map((role) => (
            <label key={role} style={{ display: "flex", flexDirection: "row", gap: 6 }}>
              <input
                type="checkbox"
                checked={roles.includes(role)}
                onChange={() => toggleRole(role)}
              />
              {role}
            </label>
          ))}
        </fieldset>
        {error && <div className="alert alert--error">{error}</div>}
        <button type="submit" className="btn">
          Створити користувача
        </button>
      </form>
    </section>
  );
}
