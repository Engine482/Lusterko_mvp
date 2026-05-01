"use client";

import { useEffect, useState } from "react";

import { adminApi, type AuditLogItem } from "@/lib/api/admin";
import { describeError } from "@/lib/api/utils";

// Wireframes P0 §8.6 — Audit Log Screen.
export default function AdminAuditPage() {
  const [items, setItems] = useState<AuditLogItem[]>([]);
  const [eventType, setEventType] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    adminApi
      .listAuditLogs({ event_type: eventType || undefined, page_size: 100 })
      .then((res) => {
        if (!cancelled) setItems(res.items);
      })
      .catch((err) => {
        if (!cancelled) setError(describeError(err));
      });
    return () => {
      cancelled = true;
    };
  }, [eventType]);

  return (
    <section>
      <h1>Audit log</h1>
      <div style={{ marginBottom: 12 }}>
        <input
          placeholder="Фільтр за event_type"
          value={eventType}
          onChange={(e) => setEventType(e.target.value)}
        />
      </div>
      {error && <div className="alert alert--error">{error}</div>}
      <table className="table">
        <thead>
          <tr>
            <th>Час</th>
            <th>Подія</th>
            <th>Actor</th>
            <th>Target</th>
            <th>Деталі</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row) => (
            <tr key={row.id}>
              <td>{new Date(row.created_at).toLocaleString()}</td>
              <td>{row.event_type}</td>
              <td>{row.actor_user_id ?? "—"}</td>
              <td>{row.target_user_id ?? "—"}</td>
              <td>
                <code style={{ fontSize: "0.75rem" }}>
                  {JSON.stringify(row.metadata_json)}
                </code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
