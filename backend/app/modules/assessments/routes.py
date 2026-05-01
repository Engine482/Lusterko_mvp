"""Soldier API per `Lusterko_API_Contracts_v1.md` §5.

All endpoints under `/api/v1/soldier` require `active_role == 'soldier'`
(`Lusterko_RBAC_Matrix_v1.md` §5.2). Risk Engine integration lands in Sprint 4
(daily response keeps `risk_status: insufficient_data` until then). AI parsing
is wired in Sprint 3: when the comment is non-empty the parser runs and the
result is persisted via `comment_ai_analyses`.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.api_response import error_response, success_response
from app.modules.ai import parser as ai_parser
from app.modules.assessments import (
    baseline_service,
    cognitive_service,
    daily_service,
    weekly_service,
)
from app.modules.auth.dependencies import (
    SessionContext,
    get_db,
    require_role,
)
from app.models.baseline_profile import BaselineProfile
from app.models.comment_ai_analysis import CommentAiAnalysis
from app.schemas.soldier import (
    BaselineCompleteResponse,
    BaselineStepStatus,
    BaselineSubmittedResponse,
    CompletionSummaryResponse,
    DailyCheckinSubmission,
    DailySubmissionResponse,
    DailyTodayResponse,
    GoNoGoSubmission,
    OnboardingStatusResponse,
    Phq4Submission,
    Pss4Submission,
    ReactionTestSubmission,
    SleepSubmission,
)

router = APIRouter(
    prefix="/soldier",
    tags=["soldier"],
    dependencies=[Depends(require_role("soldier"))],
)


def _profile_for(db: Session, user_id) -> BaselineProfile | None:  # type: ignore[no-untyped-def]
    return db.execute(
        select(BaselineProfile).where(BaselineProfile.user_id == user_id)
    ).scalar_one_or_none()


# --- Onboarding & baseline ---------------------------------------------------


@router.get("/onboarding-status")
def onboarding_status(
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    profile = _profile_for(db, ctx.user.id)
    statuses = baseline_service.step_status(profile)
    nxt = baseline_service.next_required_step(profile)
    payload = OnboardingStatusResponse(
        baseline_completed=bool(profile and profile.baseline_completed),
        completed_at=(profile.completed_at if profile else None),
        steps=[
            BaselineStepStatus(step_code=step, completed=done)
            for step, done in statuses.items()
        ],
        next_required_step=nxt,
    )
    db.commit()
    return success_response(payload.model_dump(mode="json"))


@router.post("/baseline/phq4")
def baseline_phq4(
    payload: Phq4Submission,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    try:
        profile = baseline_service.submit_phq4(
            db, user_id=ctx.user.id, answers=payload.answers
        )
    except baseline_service.BaselineError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        BaselineSubmittedResponse(
            step_code="phq4",
            computed={"phq4_total": profile.baseline_phq4_total or 0},
        ).model_dump()
    )


@router.post("/baseline/pss4")
def baseline_pss4(
    payload: Pss4Submission,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    try:
        profile = baseline_service.submit_pss4(
            db, user_id=ctx.user.id, answers=payload.answers
        )
    except baseline_service.BaselineError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        BaselineSubmittedResponse(
            step_code="pss4",
            computed={"pss4_total": profile.baseline_pss4_total or 0},
        ).model_dump()
    )


@router.post("/baseline/sleep")
def baseline_sleep(
    payload: SleepSubmission,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    try:
        baseline_service.submit_sleep(db, user_id=ctx.user.id, sleep_score=payload.sleep_score)
    except baseline_service.BaselineError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(BaselineSubmittedResponse(step_code="sleep").model_dump())


@router.post("/baseline/reaction-test")
def baseline_reaction_test(
    payload: ReactionTestSubmission,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    try:
        baseline_service.submit_reaction_test(
            db,
            user_id=ctx.user.id,
            median_reaction_time_ms=payload.median_reaction_time_ms,
            valid_trials=payload.valid_trials,
        )
    except baseline_service.BaselineError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(BaselineSubmittedResponse(step_code="reaction_test").model_dump())


@router.post("/baseline/go-no-go")
def baseline_go_no_go(
    payload: GoNoGoSubmission,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    try:
        baseline_service.submit_go_no_go(
            db,
            user_id=ctx.user.id,
            commission_errors=payload.commission_errors,
            omission_errors=payload.omission_errors,
            valid_trials=payload.valid_trials,
        )
    except baseline_service.BaselineError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(BaselineSubmittedResponse(step_code="go_no_go").model_dump())


@router.post("/baseline/complete")
def baseline_complete(
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    try:
        profile = baseline_service.complete_baseline(db, user_id=ctx.user.id)
    except baseline_service.BaselineError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    assert profile.completed_at is not None
    return success_response(
        BaselineCompleteResponse(
            baseline_completed=True, completed_at=profile.completed_at
        ).model_dump(mode="json")
    )


# --- Daily check-in ----------------------------------------------------------


@router.get("/daily-checkins/today")
def daily_today(
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    day = daily_service.today()
    already, last_status = daily_service.get_today_state(db, user_id=ctx.user.id, day=day)
    db.commit()
    return success_response(
        DailyTodayResponse(
            already_submitted=already, checkin_date=day, last_risk_status=last_status
        ).model_dump(mode="json")
    )


@router.post("/daily-checkins")
def daily_submit(
    payload: DailyCheckinSubmission,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    try:
        row = daily_service.submit_daily(
            db,
            user_id=ctx.user.id,
            sleep_score=payload.sleep_score,
            energy_score=payload.energy_score,
            mood_score=payload.mood_score,
            concentration_score=payload.concentration_score,
            comment_text=payload.comment_text,
            day=daily_service.today(),
        )
    except daily_service.DailyError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]

    # Sprint 3: AI parse the optional comment. AI failure must not break the
    # daily save (PRD §22.4).
    analysis = ai_parser.analyze_comment(payload.comment_text)
    db.add(
        CommentAiAnalysis(
            daily_checkin_id=row.id,
            language_detected=analysis.language_detected,
            has_signal=analysis.has_signal,
            markers=list(analysis.markers),
            text_risk_level=analysis.text_risk_level,
            confidence_score=Decimal(str(round(analysis.confidence_score, 3))),
            summary_for_system=analysis.summary_for_system,
            parse_status=analysis.parse_status,
            raw_model_name=analysis.raw_model_name,
        )
    )
    db.commit()

    # Risk Engine — Sprint 4. Until then we return insufficient_data even if
    # AI flagged a high-risk comment (no auto-decisioning without Risk Engine).
    return success_response(
        DailySubmissionResponse(
            daily_checkin_id=row.id,
            risk_status="insufficient_data",
            explanation_text=None,
            ai_parse_status=analysis.parse_status,
        ).model_dump(mode="json")
    )


# --- Weekly reassessment -----------------------------------------------------


@router.post("/weekly/phq4")
def weekly_phq4(
    payload: Phq4Submission,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    try:
        row = weekly_service.submit_phq4(db, user_id=ctx.user.id, answers=payload.answers)
    except weekly_service.WeeklyError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        {"weekly_phq4_id": str(row.id), "total_score": row.total_score}
    )


@router.post("/weekly/pss4")
def weekly_pss4(
    payload: Pss4Submission,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    try:
        row = weekly_service.submit_pss4(db, user_id=ctx.user.id, answers=payload.answers)
    except weekly_service.WeeklyError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        {"weekly_pss4_id": str(row.id), "total_score": row.total_score}
    )


# --- Periodic cognitive ------------------------------------------------------


@router.post("/cognitive/reaction-test")
def cognitive_reaction(
    payload: ReactionTestSubmission,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    row = cognitive_service.submit_reaction(
        db,
        user_id=ctx.user.id,
        median_reaction_time_ms=payload.median_reaction_time_ms,
        valid_trials=payload.valid_trials,
    )
    db.commit()
    return success_response({"reaction_test_id": str(row.id)})


@router.post("/cognitive/go-no-go")
def cognitive_go_no_go(
    payload: GoNoGoSubmission,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    row = cognitive_service.submit_go_no_go(
        db,
        user_id=ctx.user.id,
        commission_errors=payload.commission_errors,
        omission_errors=payload.omission_errors,
        valid_trials=payload.valid_trials,
    )
    db.commit()
    return success_response({"go_no_go_id": str(row.id)})


@router.get("/completion-summary")
def completion_summary(
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("soldier")),
) -> Response:
    summary = daily_service.completion_summary(
        db, user_id=ctx.user.id, day=daily_service.today()
    )
    db.commit()
    return success_response(
        CompletionSummaryResponse(**summary).model_dump(mode="json")  # type: ignore[arg-type]
    )
