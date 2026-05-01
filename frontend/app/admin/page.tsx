"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { adminApi } from "@/lib/api/admin";
import { describeError } from "@/lib/api/utils";

// Wireframes P0 §8.1 — Admin Dashboard.
export default function AdminDashboardPage() {
  const [counts, setCounts] = useState<{
    total: number;
    active: number;
    inactive: number;
    units: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      adminApi.listUsers({ page_size: 1 }),
      adminApi.listUsers({ status: "active", page_size: 1 }),
      adminApi.listUsers({ status: "inactive", page_size: 1 }),
      adminApi.listUnits(),
    ])
      .then(([all, active, inactive, units]) =>
        setCounts({
          total: all.total,
          active: active.total,
          inactive: inactive.total,
          units: units.items.length,
        }),
      )
      .catch((err) => setError(describeError(err)));
  }, []);

  return (
    <section>
      <h1>Адміністрування</h1>
      {error && <div className="alert alert--error">{error}</div>}
      {counts && (
        <div className="kpi-row">
          <div className="kpi-card">
            <div>Усього користувачів</div>
            <strong style={{ fontSize: "1.5rem" }}>{counts.total}</strong>
          </div>
          <div className="kpi-card">
            <div>Активних</div>
            <strong style={{ fontSize: "1.5rem" }}>{counts.active}</strong>
          </div>
          <div className="kpi-card">
            <div>Деактивованих</div>
            <strong style={{ fontSize: "1.5rem" }}>{counts.inactive}</strong>
          </div>
          <div className="kpi-card">
            <div>Підрозділів</div>
            <strong style={{ fontSize: "1.5rem" }}>{counts.units}</strong>
          </div>
        </div>
      )}
      <nav style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
        <Link className="btn" href="/admin/users">
          Користувачі
        </Link>
        <Link className="btn btn--ghost" href="/admin/users/new">
          Створити користувача
        </Link>
        <Link className="btn btn--ghost" href="/admin/units">
          Підрозділи
        </Link>
        <Link className="btn btn--ghost" href="/admin/audit">
          Audit log
        </Link>
      </nav>
    </section>
  );
}
