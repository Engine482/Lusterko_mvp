"""Read-side queries for the medic module (Backlog EPIC-52).

Like the commander module, scope checks happen in the route layer; these
helpers take an already-validated `unit_id` argument.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from typing import cast

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.core.constants import CaseStatus, RiskStatus
from app.models.case_review import CaseReview
from app.models.case_review_note import CaseReviewNote
from app.models.comment_ai_analysis import CommentAiAnalysis
from app.models.daily_checkin import DailyCheckin
from app.models.go_no_go_test import GoNoGoTest
from app.models.reaction_test import ReactionTest
from app.models.risk_status import RiskStatusRow
from app.models.user import User
from app.models.weekly_phq4 import WeeklyPhq4Assessment
from app.models.weekly_pss4 import WeeklyPss4Assessment


@dataclass(frozen=True)
class MedicCaseRow:
    case_id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    case_status: CaseStatus
    current_risk_status: RiskStatus
    opened_at: datetime
    last_event_at: datetime | None


def list_priority_cases(
    db: Session,
    *,
    unit_id: uuid.UUID,
    case_status_filter: CaseStatus | None = None,
    risk_filter: RiskStatus | None = None,
    limit: int = 100,
) -> list[MedicCaseRow]:
    """Open cases first, ordered by red > yellow > insufficient_data > green
    and then by recency. Closed cases are included only when explicitly
    filtered for."""

    risk_rank = case(
        (RiskStatusRow.current_risk_status == "red", 0),
        (RiskStatusRow.current_risk_status == "yellow", 1),
        (RiskStatusRow.current_risk_status == "insufficient_data", 2),
        (RiskStatusRow.current_risk_status == "green", 3),
        else_=4,
    )

    stmt = (
        select(
            CaseReview.id,
            CaseReview.user_id,
            User.full_name,
            CaseReview.status,
            RiskStatusRow.current_risk_status,
            CaseReview.opened_at,
            RiskStatusRow.calculated_at,
        )
        .join(User, User.id == CaseReview.user_id)
        .outerjoin(RiskStatusRow, RiskStatusRow.user_id == CaseReview.user_id)
        .where(User.unit_id == unit_id)
        .order_by(risk_rank, CaseReview.opened_at.desc())
        .limit(limit)
    )

    if case_status_filter is not None:
        stmt = stmt.where(CaseReview.status == case_status_filter)
    else:
        stmt = stmt.where(CaseReview.status != "closed")

    if risk_filter is not None:
        stmt = stmt.where(RiskStatusRow.current_risk_status == risk_filter)

    rows = db.execute(stmt).all()
    return [
        MedicCaseRow(
            case_id=row[0],
            user_id=row[1],
            full_name=row[2],
            case_status=row[3],
            current_risk_status=row[4] or "insufficient_data",
            opened_at=row[5],
            last_event_at=row[6],
        )
        for row in rows
    ]


@dataclass(frozen=True)
class LatestDaily:
    checkin_date: date
    sleep_score: int
    energy_score: int
    mood_score: int
    concentration_score: int
    comment_text: str | None


@dataclass(frozen=True)
class LatestWeekly:
    phq4_total: int | None
    pss4_total: int | None
    phq4_at: date | None
    pss4_at: date | None


@dataclass(frozen=True)
class LatestCognitive:
    reaction_median_ms: int | None
    reaction_at: date | None
    gonogo_commission_errors: int | None
    gonogo_omission_errors: int | None
    gonogo_at: date | None


@dataclass(frozen=True)
class LatestAi:
    summary_for_system: str | None
    parse_status: str | None
    text_risk_level: str | None
    markers: tuple[str, ...]


@dataclass(frozen=True)
class CaseNote:
    id: uuid.UUID
    author_user_id: uuid.UUID
    text: str
    created_at: datetime


@dataclass(frozen=True)
class MedicCaseDetail:
    case_id: uuid.UUID
    case_status: CaseStatus
    opened_at: datetime
    closed_at: datetime | None
    assigned_to_user_id: uuid.UUID | None
    user_id: uuid.UUID
    full_name: str
    unit_id: uuid.UUID | None
    current_risk_status: RiskStatus
    current_risk_score: Decimal | None
    explanation_text: str | None
    hard_flag: str | None
    latest_daily: LatestDaily | None
    latest_weekly: LatestWeekly
    latest_cognitive: LatestCognitive
    latest_ai: LatestAi
    notes: tuple[CaseNote, ...] = field(default_factory=tuple)


def case_detail(
    db: Session,
    *,
    unit_id: uuid.UUID,
    case_id: uuid.UUID,
) -> MedicCaseDetail | None:
    case_row = db.execute(
        select(CaseReview, User)
        .join(User, User.id == CaseReview.user_id)
        .where(CaseReview.id == case_id, User.unit_id == unit_id)
    ).one_or_none()
    if case_row is None:
        return None
    case_obj, user = case_row

    status_row = db.execute(
        select(RiskStatusRow).where(RiskStatusRow.user_id == user.id)
    ).scalar_one_or_none()

    daily = db.execute(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user.id)
        .order_by(DailyCheckin.checkin_date.desc(), DailyCheckin.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    latest_daily = (
        LatestDaily(
            checkin_date=daily.checkin_date,
            sleep_score=daily.sleep_score,
            energy_score=daily.energy_score,
            mood_score=daily.mood_score,
            concentration_score=daily.concentration_score,
            comment_text=daily.comment_text,
        )
        if daily
        else None
    )

    phq4 = db.execute(
        select(WeeklyPhq4Assessment)
        .where(WeeklyPhq4Assessment.user_id == user.id)
        .order_by(WeeklyPhq4Assessment.assessment_date.desc())
        .limit(1)
    ).scalar_one_or_none()
    pss4 = db.execute(
        select(WeeklyPss4Assessment)
        .where(WeeklyPss4Assessment.user_id == user.id)
        .order_by(WeeklyPss4Assessment.assessment_date.desc())
        .limit(1)
    ).scalar_one_or_none()
    weekly = LatestWeekly(
        phq4_total=phq4.total_score if phq4 else None,
        pss4_total=pss4.total_score if pss4 else None,
        phq4_at=phq4.assessment_date if phq4 else None,
        pss4_at=pss4.assessment_date if pss4 else None,
    )

    reaction = db.execute(
        select(ReactionTest)
        .where(ReactionTest.user_id == user.id, ReactionTest.context == "cognitive")
        .order_by(ReactionTest.test_date.desc(), ReactionTest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    gonogo = db.execute(
        select(GoNoGoTest)
        .where(GoNoGoTest.user_id == user.id, GoNoGoTest.context == "cognitive")
        .order_by(GoNoGoTest.test_date.desc(), GoNoGoTest.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    cognitive = LatestCognitive(
        reaction_median_ms=reaction.median_reaction_time_ms if reaction else None,
        reaction_at=reaction.test_date if reaction else None,
        gonogo_commission_errors=gonogo.commission_errors if gonogo else None,
        gonogo_omission_errors=gonogo.omission_errors if gonogo else None,
        gonogo_at=gonogo.test_date if gonogo else None,
    )

    ai_row = db.execute(
        select(CommentAiAnalysis)
        .join(DailyCheckin, DailyCheckin.id == CommentAiAnalysis.daily_checkin_id)
        .where(DailyCheckin.user_id == user.id)
        .order_by(DailyCheckin.checkin_date.desc(), DailyCheckin.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    raw_markers: list[Any] = list(ai_row.markers) if ai_row else []
    latest_ai = LatestAi(
        summary_for_system=ai_row.summary_for_system if ai_row else None,
        parse_status=ai_row.parse_status if ai_row else None,
        text_risk_level=ai_row.text_risk_level if ai_row else None,
        markers=tuple(str(m) for m in raw_markers),
    )

    note_rows = db.execute(
        select(CaseReviewNote)
        .where(CaseReviewNote.case_review_id == case_obj.id)
        .order_by(CaseReviewNote.created_at.desc())
    ).scalars().all()
    notes = tuple(
        CaseNote(
            id=n.id,
            author_user_id=n.author_user_id,
            text=n.text,
            created_at=n.created_at,
        )
        for n in note_rows
    )

    return MedicCaseDetail(
        case_id=case_obj.id,
        case_status=cast(CaseStatus, case_obj.status),
        opened_at=case_obj.opened_at,
        closed_at=case_obj.closed_at,
        assigned_to_user_id=case_obj.assigned_to_user_id,
        user_id=user.id,
        full_name=user.full_name,
        unit_id=user.unit_id,
        current_risk_status=cast(
            RiskStatus,
            status_row.current_risk_status if status_row else "insufficient_data",
        ),
        current_risk_score=status_row.current_risk_score if status_row else None,
        explanation_text=status_row.explanation_text if status_row else None,
        hard_flag=status_row.hard_flag if status_row else None,
        latest_daily=latest_daily,
        latest_weekly=weekly,
        latest_cognitive=cognitive,
        latest_ai=latest_ai,
        notes=notes,
    )
