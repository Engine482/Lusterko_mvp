"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { adminApi, type AdminUser } from "@/lib/api/admin";
import { humanError } from "@/lib/api/messages";
import { ROLE_LABEL } from "@/lib/labels";
import type { Role, UserStatus } from "@/types/enums";

const STATUS_LABEL: Record<UserStatus, string> = {
  active: "Активний",
  inactive: "Деактивований",
};

const ROLES: Role[] = ["soldier", "commander", "medic_psych", "admin"];
const STATUSES: UserStatus[] = ["active", "inactive"];

// Wireframes P0 §8.2 — Users List.
export default function AdminUsersPage() {
  const [items, setItems] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<UserStatus | "">("");
  const [filterRole, setFilterRole] = useState<Role | "">("");

  useEffect(() => {
    let cancelled = false;
    adminApi
      .listUsers({
        status: filterStatus || undefined,
        role: filterRole || undefined,
        page_size: 100,
      })
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        if (!cancelled) setError(humanError(err));
      });
    return () => {
      cancelled = true;
    };
  }, [filterStatus, filterRole]);

  return (
    <section>
      <h1>Користувачі</h1>
      <div style={{ display: "flex", gap: 12, marginBottom: 12, flexWrap: "wrap" }}>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as UserStatus | "")}
        >
          <option value="">Усі статуси</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {STATUS_LABEL[s]}
            </option>
          ))}
        </select>
        <select
          value={filterRole}
          onChange={(e) => setFilterRole(e.target.value as Role | "")}
          aria-label="Фільтр за роллю"
        >
          <option value="">Усі ролі</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {ROLE_LABEL[r]}
            </option>
          ))}
        </select>
        <Link className="btn" href="/admin/users/new">
          + Новий користувач
        </Link>
      </div>
      {error && <div className="alert alert--error">{error}</div>}
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Ім&apos;я</th>
              <th>Email</th>
              <th>Ролі</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.id}>
                <td>{u.full_name}</td>
                <td>{u.email}</td>
                <td>{u.roles.map((r) => ROLE_LABEL[r]).join(", ")}</td>
                <td>{STATUS_LABEL[u.status]}</td>
                <td>
                  <Link href={`/admin/users/${u.id}`}>Відкрити</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p style={{ fontSize: "0.875rem", marginTop: 8 }}>Всього: {total}</p>
    </section>
  );
}
