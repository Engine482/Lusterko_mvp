"""Soldier API per `Lusterko_API_Contracts_v1.md` §5.

All endpoints under `/api/v1/soldier` require `active_role == 'soldier'`
(`Lusterko_RBAC_Matrix_v1.md` §5.2). Until AI parsing (Sprint 3) and Risk
Engine (Sprint 4) ship, daily check-in returns `insufficient_data` with no
explanation; that's a valid value per API Contracts §2.2.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.api_response import error_response, success_response
from app.modules.assessments import baseline_service, daily_service
from app.modules.auth.dependencies import (
    SessionContext,
    get_db,
    require_role,
)
from app.models.baseline_profile import BaselineProfile
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
        steps=[BaselineStepStatus(step_code=step, completed=done) for step, done in statuses.items()],
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
    db.commit()
    # AI parse → Sprint 3, Risk Engine → Sprint 4. Until then we return a valid
    # placeholder envelope (`insufficient_data` + `skipped`).
    return success_response(
        DailySubmissionResponse(
            daily_checkin_id=row.id,
            risk_status="insufficient_data",
            explanation_text=None,
            ai_parse_status="skipped",
        ).model_dump(mode="json")
    )


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
