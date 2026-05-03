"use client";

type Props = {
  label: string;
  value: number | null;
  options: { value: number; label: string }[];
  onChange: (value: number) => void;
};

export function LikertScale({ label, value, options, onChange }: Props) {
  return (
    <fieldset
      style={{
        border: "1px solid var(--border)",
        background: "var(--bg-card)",
        borderRadius: "var(--radius-card)",
        padding: "12px 16px",
        marginBottom: 12,
      }}
    >
      <legend style={{ padding: "0 6px" }}>{label}</legend>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {options.map((opt) => (
          <label
            key={opt.value}
            style={{ display: "flex", alignItems: "center", gap: 8 }}
          >
            <input
              type="radio"
              checked={value === opt.value}
              onChange={() => onChange(opt.value)}
            />
            <span>{opt.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
