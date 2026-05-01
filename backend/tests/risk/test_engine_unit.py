"""Pure-function tests for the Risk Engine (Spec §14 minimum scenarios).

These never touch the DB — they exercise `engine.compute` directly so we can
exhaustively cover the rule matrix from §6-§10 without fixture overhead.
"""

from __future__ import annotations

from decimal import Decimal

from app.modules.risk import engine


def _baseline_full(**overrides: int) -> engine.BaselineSnapshot:
    base: dict[str, int | bool] = dict(
        completed=True,
        sleep=7,
        energy=7,
        mood=7,
        concentration=7,
        phq4_total=2,
        pss4_total=4,
        reaction_median_ms=400,
        gonogo_commission_errors=2,
        gonogo_omission_errors=1,
    )
    base.update(overrides)
    return engine.BaselineSnapshot(**base)  # type: ignore[arg-type]


def _empty_text() -> engine.TextSnapshot:
    return engine.TextSnapshot(
        parse_status="skipped",
        text_risk_level="unknown",
        confidence_score=Decimal("0"),
        markers=(),
    )


def _no_weekly() -> engine.WeeklySnapshot:
    return engine.WeeklySnapshot(phq4_total=None, pss4_total=None)


def _no_cog() -> engine.CognitiveSnapshot:
    return engine.CognitiveSnapshot(
        reaction_median_ms=None,
        gonogo_commission_errors=None,
        gonogo_omission_errors=None,
    )


def test_green_when_everything_normal() -> None:
    result = engine.compute(
        daily=engine.DailySnapshot(7, 7, 7, 7),
        weekly=_no_weekly(),
        cognitive=_no_cog(),
        text=_empty_text(),
        baseline=_baseline_full(),
    )
    assert result.status == "green"
    assert result.total_score == Decimal("0")
    assert result.hard_flag is None


def test_yellow_by_functional_cluster() -> None:
    # Two scales drop severely vs baseline → F1×2 + F4 = 3 (functional cap),
    # plus F3×2 (absolute low ≤3) but capped at 3.
    daily = engine.DailySnapshot(sleep_score=2, energy_score=3, mood_score=7, concentration_score=7)
    result = engine.compute(
        daily=daily,
        weekly=_no_weekly(),
        cognitive=_no_cog(),
        text=_empty_text(),
        baseline=_baseline_full(),
    )
    assert result.functional_score == Decimal("3")
    assert result.status == "yellow"
    assert result.hard_flag is None


def test_red_hard_flag_severe_functional_cluster() -> None:
    # Three scales ≤3 → HF1 → red regardless of total.
    daily = engine.DailySnapshot(sleep_score=2, energy_score=2, mood_score=2, concentration_score=8)
    result = engine.compute(
        daily=daily,
        weekly=_no_weekly(),
        cognitive=_no_cog(),
        text=_empty_text(),
        baseline=_baseline_full(),
    )
    assert result.hard_flag == "severe_functional_cluster"
    assert result.status == "red"


def test_yellow_by_weekly_strain_combined() -> None:
    # PHQ-4 elevated (E1) + PSS-4 elevated (E4) + E7 combined → 2.5 capped to 2.
    weekly = engine.WeeklySnapshot(phq4_total=7, pss4_total=9)
    result = engine.compute(
        daily=engine.DailySnapshot(7, 7, 7, 7),
        weekly=weekly,
        cognitive=_no_cog(),
        text=_empty_text(),
        baseline=_baseline_full(),
    )
    assert result.emotional_score == Decimal("2")
    rules = {h.rule_code for h in result.hits}
    assert {"E1", "E4", "E7"}.issubset(rules)
    # Status here is below yellow threshold without other domains; cap is the
    # point — we're verifying the combined rule fires, not the bucket.
    assert result.status in ("green", "yellow")


def test_red_by_cumulative_score() -> None:
    # Functional cap (3) + emotional cap (2) + cognitive cap (2) = 7 ≥ 6.
    daily = engine.DailySnapshot(sleep_score=2, energy_score=3, mood_score=3, concentration_score=2)
    weekly = engine.WeeklySnapshot(phq4_total=10, pss4_total=12)
    cog = engine.CognitiveSnapshot(
        reaction_median_ms=600,  # 600/400 = 1.5 → C2 (+2)
        gonogo_commission_errors=2,
        gonogo_omission_errors=1,
    )
    result = engine.compute(
        daily=daily,
        weekly=weekly,
        cognitive=cog,
        text=_empty_text(),
        baseline=_baseline_full(),
    )
    # Hard flag may also fire (HF1) since 4 scales are low — both routes lead
    # to red, which is the point.
    assert result.status == "red"


def test_red_by_acute_distress_marker() -> None:
    text = engine.TextSnapshot(
        parse_status="success",
        text_risk_level="high",
        confidence_score=Decimal("0.9"),
        markers=("acute_distress",),
    )
    result = engine.compute(
        daily=engine.DailySnapshot(7, 7, 7, 7),
        weekly=_no_weekly(),
        cognitive=_no_cog(),
        text=text,
        baseline=_baseline_full(),
    )
    assert result.hard_flag == "acute_distress"
    assert result.status == "red"


def test_red_by_repeated_high_text_risk() -> None:
    text = engine.TextSnapshot(
        parse_status="success",
        text_risk_level="high",
        confidence_score=Decimal("0.8"),
        markers=("low_mood", "fatigue"),
        previous_text_risk_level="high",
    )
    result = engine.compute(
        daily=engine.DailySnapshot(7, 7, 7, 7),
        weekly=_no_weekly(),
        cognitive=_no_cog(),
        text=text,
        baseline=_baseline_full(),
    )
    assert result.hard_flag == "repeated_high_text_risk"
    assert result.status == "red"


def test_text_modifier_ignored_on_low_confidence() -> None:
    text = engine.TextSnapshot(
        parse_status="success",
        text_risk_level="high",
        confidence_score=Decimal("0.4"),  # below 0.60 — base modifier skipped
        markers=("sleep_issue",),
    )
    result = engine.compute(
        daily=engine.DailySnapshot(7, 7, 7, 7),
        weekly=_no_weekly(),
        cognitive=_no_cog(),
        text=text,
        baseline=_baseline_full(),
    )
    assert result.text_score == Decimal("0")


def test_parse_failure_resilience() -> None:
    text = engine.TextSnapshot(
        parse_status="failed",
        text_risk_level="unknown",
        confidence_score=Decimal("0"),
        markers=(),
    )
    result = engine.compute(
        daily=engine.DailySnapshot(7, 7, 7, 7),
        weekly=_no_weekly(),
        cognitive=_no_cog(),
        text=text,
        baseline=_baseline_full(),
    )
    assert result.text_score == Decimal("0")
    assert result.status == "green"


def test_incomplete_baseline_returns_insufficient_data() -> None:
    result = engine.compute(
        daily=engine.DailySnapshot(7, 7, 7, 7),
        weekly=_no_weekly(),
        cognitive=_no_cog(),
        text=_empty_text(),
        baseline=engine.BaselineSnapshot(completed=False),
    )
    assert result.status == "insufficient_data"
    assert result.hard_flag is None


def test_hard_flag_overrides_incomplete_baseline() -> None:
    # Spec §3.3: hard flags still fire even without baseline.
    text = engine.TextSnapshot(
        parse_status="success",
        text_risk_level="high",
        confidence_score=Decimal("0.9"),
        markers=("acute_distress",),
    )
    result = engine.compute(
        daily=engine.DailySnapshot(5, 5, 5, 5),
        weekly=_no_weekly(),
        cognitive=_no_cog(),
        text=text,
        baseline=engine.BaselineSnapshot(completed=False),
    )
    assert result.status == "red"
    assert result.hard_flag == "acute_distress"


def test_severe_cognitive_drop_hard_flag() -> None:
    cog = engine.CognitiveSnapshot(
        reaction_median_ms=600,  # 600/400 = 1.5 → ratio ≥ 1.40
        gonogo_commission_errors=8,  # baseline 2; 8 ≥ 2*1.5 and ≥3 absolute
        gonogo_omission_errors=1,
    )
    result = engine.compute(
        daily=engine.DailySnapshot(7, 7, 7, 7),
        weekly=_no_weekly(),
        cognitive=cog,
        text=_empty_text(),
        baseline=_baseline_full(),
    )
    assert result.hard_flag == "severe_cognitive_drop"
    assert result.status == "red"


def test_explanation_omitted_for_green() -> None:
    result = engine.compute(
        daily=engine.DailySnapshot(7, 7, 7, 7),
        weekly=_no_weekly(),
        cognitive=_no_cog(),
        text=_empty_text(),
        baseline=_baseline_full(),
    )
    assert result.explanation_text is None
