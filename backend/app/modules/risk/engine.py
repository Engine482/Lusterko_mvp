"""Pure rule-based Risk Engine (Lusterko_Risk_Engine_Spec_v1.md §4-§11).

This module is intentionally IO-free: it receives plain snapshots and returns
scores + rule hits + explanation. Persistence and recompute orchestration live
in `risk.service`. Keeping the engine pure makes the §14 test matrix trivial.

All scoring uses Decimal so values like `+0.5` round-trip cleanly into the
`numeric(4,1)` columns defined in DB Schema §5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from app.core.constants import (
    AIMarker,
    HardFlag,
    ParseStatus,
    RiskDomain,
    RiskStatus,
    TextRiskLevel,
)

# Per-domain caps (Spec §5.2). Final aggregation sums the capped values.
_FUNCTIONAL_CAP: Final[Decimal] = Decimal("3")
_EMOTIONAL_CAP: Final[Decimal] = Decimal("2")
_COGNITIVE_CAP: Final[Decimal] = Decimal("2")
_TEXT_CAP: Final[Decimal] = Decimal("2")

# Final thresholds (Spec §5.1 / §10.2).
_YELLOW_FROM = Decimal("3")
_RED_FROM = Decimal("6")

# Markers that count toward the "reinforcement" bonus (Spec §9.2).
_REINFORCEMENT_MARKERS: Final[frozenset[AIMarker]] = frozenset(
    {
        "sleep_issue",
        "fatigue",
        "low_mood",
        "anxiety_tension",
        "concentration_problem",
    }
)


# --- Public IO shapes --------------------------------------------------------


@dataclass(frozen=True)
class DailySnapshot:
    sleep_score: int
    energy_score: int
    mood_score: int
    concentration_score: int


@dataclass(frozen=True)
class WeeklySnapshot:
    """Latest weekly totals (or None if never submitted)."""

    phq4_total: int | None
    pss4_total: int | None


@dataclass(frozen=True)
class CognitiveSnapshot:
    """Latest cognitive measurements (None if never submitted)."""

    reaction_median_ms: int | None
    gonogo_commission_errors: int | None
    gonogo_omission_errors: int | None


@dataclass(frozen=True)
class TextSnapshot:
    """Result of AI parsing of the current daily check-in's comment."""

    parse_status: ParseStatus
    text_risk_level: TextRiskLevel
    confidence_score: Decimal
    markers: tuple[AIMarker, ...]
    previous_text_risk_level: TextRiskLevel | None = None


@dataclass(frozen=True)
class BaselineSnapshot:
    completed: bool
    sleep: int | None = None
    energy: int | None = None
    mood: int | None = None
    concentration: int | None = None
    phq4_total: int | None = None
    pss4_total: int | None = None
    reaction_median_ms: int | None = None
    gonogo_commission_errors: int | None = None
    gonogo_omission_errors: int | None = None


@dataclass(frozen=True)
class RuleHit:
    rule_code: str
    domain: RiskDomain
    weight: Decimal
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DomainResult:
    score: Decimal  # already capped
    hits: tuple[RuleHit, ...]
    hard_flag: HardFlag | None = None


@dataclass(frozen=True)
class RiskResult:
    status: RiskStatus
    total_score: Decimal
    functional_score: Decimal
    emotional_score: Decimal
    cognitive_score: Decimal
    text_score: Decimal
    hard_flag: HardFlag | None
    explanation_text: str | None
    hits: tuple[RuleHit, ...]


# --- Functional (Spec §6) ----------------------------------------------------


def _scale_signals(current: int, baseline: int | None) -> tuple[bool, bool, bool]:
    """Return (severe_drop, moderate_drop, absolute_low) for one daily scale."""

    severe_drop = baseline is not None and current <= baseline - 3
    moderate_drop = baseline is not None and current == baseline - 2
    absolute_low = current <= 3
    return severe_drop, moderate_drop, absolute_low


def _functional(daily: DailySnapshot, baseline: BaselineSnapshot) -> DomainResult:
    scales = (
        ("sleep", daily.sleep_score, baseline.sleep),
        ("energy", daily.energy_score, baseline.energy),
        ("mood", daily.mood_score, baseline.mood),
        ("concentration", daily.concentration_score, baseline.concentration),
    )

    hits: list[RuleHit] = []
    severe_or_low_count = 0
    raw = Decimal("0")

    for name, current, base in scales:
        severe, moderate, low = _scale_signals(current, base)
        if severe:
            raw += 1
            hits.append(
                RuleHit(
                    "F1",
                    "functional",
                    Decimal("1"),
                    {"scale": name, "current": current, "baseline": base},
                )
            )
        elif moderate:
            raw += Decimal("0.5")
            hits.append(
                RuleHit(
                    "F2",
                    "functional",
                    Decimal("0.5"),
                    {"scale": name, "current": current, "baseline": base},
                )
            )
        if low:
            raw += 1
            hits.append(
                RuleHit(
                    "F3",
                    "functional",
                    Decimal("1"),
                    {"scale": name, "current": current},
                )
            )
        if severe or low:
            severe_or_low_count += 1

    if severe_or_low_count >= 2:
        raw += 1
        hits.append(
            RuleHit(
                "F4",
                "functional",
                Decimal("1"),
                {"affected_scales": severe_or_low_count},
            )
        )

    hard_flag: HardFlag | None = None
    if severe_or_low_count >= 3:
        hard_flag = "severe_functional_cluster"
        hits.append(
            RuleHit(
                "HF1",
                "functional",
                Decimal("0"),
                {"affected_scales": severe_or_low_count},
            )
        )

    capped = min(raw, _FUNCTIONAL_CAP)
    return DomainResult(score=capped, hits=tuple(hits), hard_flag=hard_flag)


# --- Emotional / stress (Spec §7) -------------------------------------------


def _emotional(weekly: WeeklySnapshot, baseline: BaselineSnapshot) -> DomainResult:
    hits: list[RuleHit] = []
    raw = Decimal("0")
    phq4_elevated = False
    pss4_elevated = False

    if weekly.phq4_total is not None:
        if weekly.phq4_total >= 9:
            raw += 2
            hits.append(
                RuleHit(
                    "E2",
                    "emotional",
                    Decimal("2"),
                    {"phq4_total": weekly.phq4_total},
                )
            )
            phq4_elevated = True
        elif weekly.phq4_total >= 6:
            raw += 1
            hits.append(
                RuleHit(
                    "E1",
                    "emotional",
                    Decimal("1"),
                    {"phq4_total": weekly.phq4_total},
                )
            )
            phq4_elevated = True

        if (
            baseline.phq4_total is not None
            and weekly.phq4_total >= baseline.phq4_total + 3
        ):
            raw += Decimal("0.5")
            hits.append(
                RuleHit(
                    "E3",
                    "emotional",
                    Decimal("0.5"),
                    {
                        "phq4_total": weekly.phq4_total,
                        "baseline_phq4_total": baseline.phq4_total,
                    },
                )
            )

    if weekly.pss4_total is not None:
        if weekly.pss4_total >= 11:
            raw += 2
            hits.append(
                RuleHit(
                    "E5",
                    "emotional",
                    Decimal("2"),
                    {"pss4_total": weekly.pss4_total},
                )
            )
            pss4_elevated = True
        elif weekly.pss4_total >= 8:
            raw += 1
            hits.append(
                RuleHit(
                    "E4",
                    "emotional",
                    Decimal("1"),
                    {"pss4_total": weekly.pss4_total},
                )
            )
            pss4_elevated = True

        if (
            baseline.pss4_total is not None
            and weekly.pss4_total >= baseline.pss4_total + 4
        ):
            raw += Decimal("0.5")
            hits.append(
                RuleHit(
                    "E6",
                    "emotional",
                    Decimal("0.5"),
                    {
                        "pss4_total": weekly.pss4_total,
                        "baseline_pss4_total": baseline.pss4_total,
                    },
                )
            )

    if phq4_elevated and pss4_elevated:
        raw += Decimal("0.5")
        hits.append(RuleHit("E7", "emotional", Decimal("0.5"), {}))

    return DomainResult(score=min(raw, _EMOTIONAL_CAP), hits=tuple(hits))


# --- Cognitive (Spec §8) ----------------------------------------------------


def _error_increased(current: int, baseline: int | None) -> bool:
    """C3/C4 trigger: current is 50% above baseline OR ≥3 absolute errors more.
    Absolute floor handles the "baseline is 0" case where percent is undefined.
    """

    if current >= 3 and (baseline is None or current - (baseline or 0) >= 3):
        return True
    if baseline is None or baseline == 0:
        return False
    return current >= baseline * 1.5


def _cognitive(cog: CognitiveSnapshot, baseline: BaselineSnapshot) -> DomainResult:
    hits: list[RuleHit] = []
    raw = Decimal("0")

    severe_reaction = False
    if cog.reaction_median_ms is not None and baseline.reaction_median_ms:
        ratio = cog.reaction_median_ms / baseline.reaction_median_ms
        if ratio >= 1.30:
            raw += 2
            hits.append(
                RuleHit(
                    "C2",
                    "cognitive",
                    Decimal("2"),
                    {"current_ms": cog.reaction_median_ms, "ratio": round(ratio, 3)},
                )
            )
            severe_reaction = ratio >= 1.40
        elif ratio >= 1.15:
            raw += 1
            hits.append(
                RuleHit(
                    "C1",
                    "cognitive",
                    Decimal("1"),
                    {"current_ms": cog.reaction_median_ms, "ratio": round(ratio, 3)},
                )
            )

    commission_increase = False
    if cog.gonogo_commission_errors is not None and _error_increased(
        cog.gonogo_commission_errors, baseline.gonogo_commission_errors
    ):
        raw += 1
        commission_increase = True
        hits.append(
            RuleHit(
                "C3",
                "cognitive",
                Decimal("1"),
                {
                    "current": cog.gonogo_commission_errors,
                    "baseline": baseline.gonogo_commission_errors,
                },
            )
        )

    omission_increase = False
    if cog.gonogo_omission_errors is not None and _error_increased(
        cog.gonogo_omission_errors, baseline.gonogo_omission_errors
    ):
        raw += 1
        omission_increase = True
        hits.append(
            RuleHit(
                "C4",
                "cognitive",
                Decimal("1"),
                {
                    "current": cog.gonogo_omission_errors,
                    "baseline": baseline.gonogo_omission_errors,
                },
            )
        )

    hard_flag: HardFlag | None = None
    if severe_reaction and (commission_increase or omission_increase):
        hard_flag = "severe_cognitive_drop"
        hits.append(RuleHit("HF2", "cognitive", Decimal("0"), {}))

    return DomainResult(score=min(raw, _COGNITIVE_CAP), hits=tuple(hits), hard_flag=hard_flag)


# --- Text (Spec §9) ---------------------------------------------------------


_TEXT_BASE: Final[dict[TextRiskLevel, Decimal]] = {
    "none": Decimal("0"),
    "low": Decimal("0.5"),
    "medium": Decimal("1"),
    "high": Decimal("2"),
    "unknown": Decimal("0"),
}


def _text(text: TextSnapshot) -> DomainResult:
    hits: list[RuleHit] = []
    raw = Decimal("0")
    hard_flag: HardFlag | None = None

    usable = (
        text.parse_status == "success"
        and text.confidence_score >= Decimal("0.60")
        and text.text_risk_level in _TEXT_BASE
    )
    if usable:
        base = _TEXT_BASE[text.text_risk_level]
        if base > 0:
            raw += base
            hits.append(
                RuleHit(
                    "T1",
                    "text",
                    base,
                    {"text_risk_level": text.text_risk_level},
                )
            )

        reinforcing = [m for m in text.markers if m in _REINFORCEMENT_MARKERS]
        if len(reinforcing) >= 2:
            raw += Decimal("0.5")
            hits.append(
                RuleHit("T2", "text", Decimal("0.5"), {"markers": reinforcing})
            )

    # HF3: acute_distress with high confidence — fires regardless of usable
    # because it's an explicit safety signal (Spec §9.3).
    if "acute_distress" in text.markers and text.confidence_score >= Decimal("0.75"):
        hard_flag = "acute_distress"
        hits.append(RuleHit("HF3", "text", Decimal("0"), {}))

    # HF4: previous AND current daily comment both classified high.
    if (
        text.text_risk_level == "high"
        and text.previous_text_risk_level == "high"
    ):
        hard_flag = hard_flag or "repeated_high_text_risk"
        hits.append(RuleHit("HF4", "text", Decimal("0"), {}))

    return DomainResult(score=min(raw, _TEXT_CAP), hits=tuple(hits), hard_flag=hard_flag)


# --- Aggregation + explanation (Spec §10-§11) -------------------------------


_HARD_FLAG_TEXT: Final[dict[HardFlag, str]] = {
    "severe_functional_cluster": (
        "Виявлено сукупне функціональне просідання за кількома щоденними шкалами."
    ),
    "severe_cognitive_drop": (
        "Зафіксовано виражене погіршення когнітивних показників."
    ),
    "acute_distress": (
        "Текстовий коментар містить ознаки гострого дистресу."
    ),
    "repeated_high_text_risk": (
        "Повторно виявлено високоризиковий текстовий сигнал."
    ),
}


def _domain_text(
    functional: DomainResult,
    emotional: DomainResult,
    cognitive: DomainResult,
    text: DomainResult,
) -> str | None:
    parts: list[str] = []
    if functional.score > 0:
        parts.append(
            "Зафіксовано просідання щоденних шкал відносно базового профілю."
        )
    if emotional.score > 0:
        parts.append(
            "Щотижневі шкали вказують на підвищене емоційне та стресове навантаження."
        )
    if cognitive.score > 0:
        parts.append(
            "Зафіксовано погіршення когнітивних показників порівняно з базовим рівнем."
        )
    if text.score > 0:
        parts.append(
            "Текстовий коментар містить ознаки виснаження, тривоги або дистресу."
        )
    return " ".join(parts) if parts else None


def compute(
    *,
    daily: DailySnapshot,
    weekly: WeeklySnapshot,
    cognitive: CognitiveSnapshot,
    text: TextSnapshot,
    baseline: BaselineSnapshot,
) -> RiskResult:
    f = _functional(daily, baseline)
    e = _emotional(weekly, baseline)
    c = _cognitive(cognitive, baseline)
    t = _text(text)

    total = f.score + e.score + c.score + t.score
    hard_flag = f.hard_flag or c.hard_flag or t.hard_flag

    if hard_flag is not None:
        status: RiskStatus = "red"
        explanation: str | None = _HARD_FLAG_TEXT[hard_flag]
    elif not baseline.completed:
        # Spec §3.3: incomplete baseline blocks cumulative red, but hard flags
        # have already been handled above.
        status = "insufficient_data"
        explanation = None
    elif total >= _RED_FROM:
        status = "red"
        explanation = _domain_text(f, e, c, t)
    elif total >= _YELLOW_FROM:
        status = "yellow"
        explanation = _domain_text(f, e, c, t)
    else:
        status = "green"
        explanation = None

    hits = tuple(list(f.hits) + list(e.hits) + list(c.hits) + list(t.hits))
    return RiskResult(
        status=status,
        total_score=total,
        functional_score=f.score,
        emotional_score=e.score,
        cognitive_score=c.score,
        text_score=t.score,
        hard_flag=hard_flag,
        explanation_text=explanation,
        hits=hits,
    )
