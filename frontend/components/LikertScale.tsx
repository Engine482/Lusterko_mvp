"use client";

type Props = {
  label: string;
  value: number | null;
  options: { value: number; label: string }[];
  onChange: (value: number) => void;
};

export function LikertScale({ label, value, options, onChange }: Props) {
  return (
    <div className="likert-scale">
      <p className="likert-scale__question">{label}</p>
      <div className="likert-scale__options" role="radiogroup" aria-label={label}>
        {options.map((opt) => (
          <label key={opt.value} className="likert-scale__option">
            <input
              type="radio"
              checked={value === opt.value}
              onChange={() => onChange(opt.value)}
            />
            <span>{opt.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
