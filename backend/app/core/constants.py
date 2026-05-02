"""Shared enum-like literals used across modules.

Mirrors `Lusterko_API_Contracts_v1.md` §2 and `Lusterko_DB_Schema_v1.md`
allowed-value sets. We intentionally use Literal + tuple constants instead of
SQL enum types so migrations stay light (DB Schema §1).
"""

from __future__ import annotations

from typing import Final, Literal

# --- Roles --------------------------------------------------------------------
Role = Literal["soldier", "commander", "medic_psych", "admin"]
ROLES: Final[tuple[Role, ...]] = ("soldier", "commander", "medic_psych", "admin")

# --- Risk ---------------------------------------------------------------------
RiskStatus = Literal["green", "yellow", "red", "insufficient_data"]
RISK_STATUSES: Final[tuple[RiskStatus, ...]] = (
    "green",
    "yellow",
    "red",
    "insufficient_data",
)

# --- AI text layer ------------------------------------------------------------
TextRiskLevel = Literal["none", "low", "medium", "high", "unknown"]
TEXT_RISK_LEVELS: Final[tuple[TextRiskLevel, ...]] = (
    "none",
    "low",
    "medium",
    "high",
    "unknown",
)

ParseStatus = Literal["success", "failed", "partial", "skipped"]
PARSE_STATUSES: Final[tuple[ParseStatus, ...]] = ("success", "failed", "partial", "skipped")

LanguageDetected = Literal["uk", "ru", "mixed", "unknown"]
LANGUAGES_DETECTED: Final[tuple[LanguageDetected, ...]] = ("uk", "ru", "mixed", "unknown")

# --- Case review --------------------------------------------------------------
CaseStatus = Literal["new", "in_review", "monitoring", "closed"]
CASE_STATUSES: Final[tuple[CaseStatus, ...]] = ("new", "in_review", "monitoring", "closed")

# --- Invites ------------------------------------------------------------------
InviteStatus = Literal["pending", "used", "expired", "revoked"]
INVITE_STATUSES: Final[tuple[InviteStatus, ...]] = ("pending", "used", "expired", "revoked")

# --- Users / sessions ---------------------------------------------------------
UserStatus = Literal["active", "inactive"]
USER_STATUSES: Final[tuple[UserStatus, ...]] = ("active", "inactive")

SessionStatus = Literal["active", "revoked", "expired"]
SESSION_STATUSES: Final[tuple[SessionStatus, ...]] = ("active", "revoked", "expired")

# --- Identity providers (P0: Google only) -------------------------------------
IdentityProvider = Literal["google"]
IDENTITY_PROVIDERS: Final[tuple[IdentityProvider, ...]] = ("google",)

# --- Baseline step codes ------------------------------------------------------
BaselineStep = Literal["phq4", "pss4", "sleep", "reaction_test", "go_no_go"]
BASELINE_STEPS: Final[tuple[BaselineStep, ...]] = (
    "phq4",
    "pss4",
    "sleep",
    "reaction_test",
    "go_no_go",
)

# --- Cognitive test context ---------------------------------------------------
TestContext = Literal["baseline", "cognitive"]
TEST_CONTEXTS: Final[tuple[TestContext, ...]] = ("baseline", "cognitive")

# --- AI markers ---------------------------------------------------------------
AIMarker = Literal[
    "sleep_issue",
    "fatigue",
    "low_mood",
    "anxiety_tension",
    "concentration_problem",
    "irritability",
    "post_stress_reaction",
    "acute_distress",
]
AI_MARKERS: Final[tuple[AIMarker, ...]] = (
    "sleep_issue",
    "fatigue",
    "low_mood",
    "anxiety_tension",
    "concentration_problem",
    "irritability",
    "post_stress_reaction",
    "acute_distress",
)

# --- Risk hard flags ----------------------------------------------------------
HardFlag = Literal[
    "severe_functional_cluster",
    "severe_cognitive_drop",
    "acute_distress",
    "repeated_high_text_risk",
]
HARD_FLAGS: Final[tuple[HardFlag, ...]] = (
    "severe_functional_cluster",
    "severe_cognitive_drop",
    "acute_distress",
    "repeated_high_text_risk",
)

# --- Risk rule domains --------------------------------------------------------
RiskDomain = Literal["functional", "emotional", "cognitive", "text"]
RISK_DOMAINS: Final[tuple[RiskDomain, ...]] = (
    "functional",
    "emotional",
    "cognitive",
    "text",
)

# --- Risk source event types --------------------------------------------------
RiskSourceEvent = Literal[
    "daily_checkin",
    "weekly_phq4",
    "weekly_pss4",
    "reaction_test",
    "go_no_go",
    "baseline_completion",
]
RISK_SOURCE_EVENTS: Final[tuple[RiskSourceEvent, ...]] = (
    "daily_checkin",
    "weekly_phq4",
    "weekly_pss4",
    "reaction_test",
    "go_no_go",
    "baseline_completion",
)

# --- Audit event types --------------------------------------------------------
AuditEventType = Literal[
    "login_success",
    "login_failed",
    "logout",
    "role_selected",
    "role_switched",
    "user_created",
    "user_updated",
    "user_deactivated",
    "user_reactivated",
    "invite_created",
    "invite_used",
    "daily_checkin_submitted",
    "weekly_phq4_submitted",
    "weekly_pss4_submitted",
    "reaction_test_submitted",
    "go_no_go_submitted",
    "case_opened",
    "case_status_changed",
    "case_note_added",
    "risk_recomputed",
    "commander_case_viewed",
    "cross_unit_access_denied",
    "medic_case_viewed",
    "denied_sensitive_access",
    "invite_email_sent",
    "invite_email_failed",
]
