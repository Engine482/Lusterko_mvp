// Mirror of `backend/app/core/constants.py`.
// Source of truth: `Lusterko_API_Contracts_v1.md` §2 + `Lusterko_DB_Schema_v1.md`.

export type Role = "soldier" | "commander" | "medic_psych" | "admin";
export const ROLES: readonly Role[] = ["soldier", "commander", "medic_psych", "admin"] as const;

export type RiskStatus = "green" | "yellow" | "red" | "insufficient_data";
export const RISK_STATUSES: readonly RiskStatus[] = [
  "green",
  "yellow",
  "red",
  "insufficient_data",
] as const;

export type TextRiskLevel = "none" | "low" | "medium" | "high" | "unknown";

export type ParseStatus = "success" | "failed" | "partial" | "skipped";

export type LanguageDetected = "uk" | "ru" | "mixed" | "unknown";

export type CaseStatus = "new" | "in_review" | "monitoring" | "closed";

export type InviteStatus = "pending" | "used" | "expired" | "revoked";

export type UserStatus = "active" | "inactive";

export type ErrorCode =
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "INVALID_INVITE"
  | "INVITE_EXPIRED"
  | "ROLE_SELECTION_REQUIRED"
  | "VALIDATION_ERROR"
  | "NOT_FOUND"
  | "CONFLICT"
  | "DAILY_ALREADY_SUBMITTED"
  | "BASELINE_NOT_COMPLETE"
  | "INVALID_ACTIVE_ROLE"
  | "INSUFFICIENT_SCOPE"
  | "AI_PARSE_FAILED"
  | "INTERNAL_ERROR";
