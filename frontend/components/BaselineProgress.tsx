type Props = {
  current: 1 | 2 | 3 | 4 | 5;
};

export function BaselineProgress({ current }: Props) {
  const total = 5;
  return (
    <div style={{ marginBottom: 16 }}>
      <div className="text-muted" style={{ fontSize: "0.875rem" }}>
        Крок {current} / {total}
      </div>
      <div
        style={{
          height: 6,
          background: "var(--border)",
          borderRadius: 3,
          marginTop: 4,
        }}
      >
        <div
          style={{
            width: `${(current / total) * 100}%`,
            height: "100%",
            background: "var(--accent)",
            borderRadius: 3,
            transition: "width 200ms",
          }}
        />
      </div>
    </div>
  );
}
