"use client";

import { useEffect, useState } from "react";

import { adminApi, type AdminUnit } from "@/lib/api/admin";
import { describeError } from "@/lib/api/utils";

// Wireframes P0 §8.5 — Units Screen.
export default function AdminUnitsPage() {
  const [items, setItems] = useState<AdminUnit[]>([]);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  const reload = () => {
    adminApi
      .listUnits()
      .then((res) => setItems(res.items))
      .catch((err) => setError(describeError(err)));
  };

  useEffect(() => {
    let cancelled = false;
    adminApi
      .listUnits()
      .then((res) => {
        if (!cancelled) setItems(res.items);
      })
      .catch((err) => {
        if (!cancelled) setError(describeError(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminApi.createUnit({ name, code: code || null });
      setName("");
      setCode("");
      reload();
    } catch (err) {
      setError(describeError(err));
    }
  };

  return (
    <section>
      <h1>Підрозділи</h1>
      {error && <div className="alert alert--error">{error}</div>}
      <form className="form-grid" onSubmit={create} style={{ marginBottom: 16 }}>
        <label>
          Назва
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          Код (опціонально)
          <input value={code} onChange={(e) => setCode(e.target.value)} />
        </label>
        <button type="submit" className="btn">
          Додати підрозділ
        </button>
      </form>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Назва</th>
              <th>Код</th>
            </tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.code ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
