import type { CaseStatus, Role, RiskStatus } from "@/types/enums";

// Canonical Ukrainian labels per UX appendix §11.
// Spec calls for the short forms: Військовий / Командир / Психолог.
export const ROLE_LABEL: Record<Role, string> = {
  soldier: "Військовий",
  commander: "Командир",
  medic_psych: "Психолог",
  admin: "Адміністратор",
};

export const RISK_LABEL: Record<RiskStatus, string> = {
  green: "Норма",
  yellow: "Потребує уваги",
  red: "Високий ризик",
  insufficient_data: "Недостатньо даних",
};

export const CASE_STATUS_LABEL: Record<CaseStatus, string> = {
  new: "Пріоритетні",
  in_review: "В роботі",
  monitoring: "Моніторинг",
  closed: "Закриті",
};
