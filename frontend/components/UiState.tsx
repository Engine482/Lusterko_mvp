import type { ReactNode } from "react";

type LoadingProps = { label?: string };

export function LoadingState({ label = "Завантаження…" }: LoadingProps) {
  return (
    <p role="status" aria-live="polite" className="text-muted">
      {label}
    </p>
  );
}

type EmptyProps = {
  title: string;
  hint?: string;
  action?: ReactNode;
};

export function EmptyState({ title, hint, action }: EmptyProps) {
  return (
    <div className="kpi-card" style={{ textAlign: "center", padding: "32px 24px" }}>
      <strong>{title}</strong>
      {hint && (
        <p className="text-muted" style={{ marginTop: 8 }}>
          {hint}
        </p>
      )}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}
