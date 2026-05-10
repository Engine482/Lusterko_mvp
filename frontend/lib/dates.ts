// Human-friendly Ukrainian relative date for due-state copy. Inputs are
// `YYYY-MM-DD` strings from the backend (timezone-naive dates), which we
// compare against today in the local browser timezone.

const PLURAL_DAYS = (n: number) => {
  // Ukrainian plural for "день": 1 → день, 2-4 → дні, 5+ → днів.
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return "день";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return "дні";
  return "днів";
};

export function relativeDayLabel(iso: string | null): string {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return iso;
  const target = new Date(y, m - 1, d);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diffMs = target.getTime() - today.getTime();
  const diffDays = Math.round(diffMs / 86_400_000);
  if (diffDays <= 0) return "сьогодні";
  if (diffDays === 1) return "завтра";
  return `через ${diffDays} ${PLURAL_DAYS(diffDays)}`;
}
