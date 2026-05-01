"""Read-side queries for the commander dashboard (Backlog EPIC-43).

All queries take a `unit_id` argument that must come from the authenticated
commander's own unit. Unit-scope enforcement happens in the route layer; these
helpers do not look up the commander themselves.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.constants import RISK_STATUSES, RiskStatus
from app.models.daily_checkin import DailyCheckin
from app.models.risk_event import RiskEvent
from app.models.risk_status import RiskStatusRow
from app.models.user import User
from app.models.user_role import UserRole


_SOLDIER_FILTER = (UserRole.role == "soldier") & (User.status == "active")


def status_counts(db: Session, *, unit_id: uuid.UUID) -> dict[RiskStatus, int]:
    """KPI row for Commander Dashboard (Wireframes §6.1).

    Soldiers in the unit who have never had a recompute are bucketed under
    `insufficient_data` so the totals always sum to "soldiers in unit".
    """

    soldier_count_stmt = (
        select(func.count(User.id.distinct()))
        .join(UserRole, UserRole.user_id == User.id)
        .where(User.unit_id == unit_id, _SOLDIER_FILTER)
    )
    total_soldiers = db.execute(soldier_count_stmt).scalar_one()

    rows = db.execute(
        select(
            RiskStatusRow.current_risk_status,
            func.count(RiskStatusRow.id),
        )
        .join(User, User.id == RiskStatusRow.user_id)
        .join(UserRole, UserRole.user_id == User.id)
        .where(User.unit_id == unit_id, _SOLDIER_FILTER)
        .group_by(RiskStatusRow.current_risk_status)
    ).all()

    counts: dict[RiskStatus, int] = {s: 0 for s in RISK_STATUSES}
    classified = 0
    for status_value, n in rows:
        if status_value in counts:
            counts[status_value] = int(n)
            classified += int(n)
    counts["insufficient_data"] += max(total_soldiers - classified, 0)
    return counts


@dataclass(frozen=True)
class CaseRow:
    user_id: uuid.UUID
    full_name: str
    unit_id: uuid.UUID | None
    current_risk_status: RiskStatus
    explanation_text: str | None
    calculated_at: datetime | None
    last_daily_at: datetime | None


def cases_in_unit(
    db: Session,
    *,
    unit_id: uuid.UUID,
    status_filter: RiskStatus | None = None,
    name_query: str | None = None,
    limit: int = 100,
) -> list[CaseRow]:
    """List of soldiers in the unit ranked by urgency.

    Sort order matches Wireframes §6.2 + Risk Engine §13.1 priority — red
    first, then yellow, then insufficient_data, then green; within a bucket
    the freshest recompute wins."""

    last_daily_subq = (
        select(
            DailyCheckin.user_id.label("user_id"),
            func.max(DailyCheckin.created_at).label("last_at"),
        )
        .group_by(DailyCheckin.user_id)
        .subquery()
    )

    rank = case(
        (RiskStatusRow.current_risk_status == "red", 0),
        (RiskStatusRow.current_risk_status == "yellow", 1),
        (RiskStatusRow.current_risk_status == "insufficient_data", 2),
        (RiskStatusRow.current_risk_status == "green", 3),
        else_=4,
    )

    stmt = (
        select(
            User.id,
            User.full_name,
            User.unit_id,
            RiskStatusRow.current_risk_status,
            RiskStatusRow.explanation_text,
            RiskStatusRow.calculated_at,
            last_daily_subq.c.last_at,
        )
        .join(UserRole, UserRole.user_id == User.id)
        .outerjoin(RiskStatusRow, RiskStatusRow.user_id == User.id)
        .outerjoin(last_daily_subq, last_daily_subq.c.user_id == User.id)
        .where(User.unit_id == unit_id, _SOLDIER_FILTER)
        .order_by(rank, RiskStatusRow.calculated_at.desc().nullslast())
        .limit(limit)
    )

    if status_filter is not None:
        stmt = stmt.where(RiskStatusRow.current_risk_status == status_filter)
    if name_query:
        like = f"%{name_query.strip().lower()}%"
        stmt = stmt.where(func.lower(User.full_name).like(like))

    rows = db.execute(stmt).all()
    return [
        CaseRow(
            user_id=row[0],
            full_name=row[1],
            unit_id=row[2],
            current_risk_status=row[3] or "insufficient_data",
            explanation_text=row[4],
            calculated_at=row[5],
            last_daily_at=row[6],
        )
        for row in rows
    ]


@dataclass(frozen=True)
class CaseCard:
    user_id: uuid.UUID
    full_name: str
    unit_id: uuid.UUID | None
    current_risk_status: RiskStatus
    explanation_text: str | None
    calculated_at: datetime | None
    recent_status_trend: list[dict[str, object]]


def case_card(
    db: Session, *, unit_id: uuid.UUID, target_user_id: uuid.UUID
) -> CaseCard | None:
    """Commander Case Card. RBAC §6.2: scoped to unit, no item-level data,
    no raw AI, no confidence_score, no medic notes. Trend is the last 14 days
    of risk_event statuses so the commander can see the trajectory without
    raw psychometric values."""

    user = db.execute(
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .where(
            User.id == target_user_id,
            User.unit_id == unit_id,
            _SOLDIER_FILTER,
        )
    ).scalar_one_or_none()
    if user is None:
        return None

    status = db.execute(
        select(RiskStatusRow).where(RiskStatusRow.user_id == user.id)
    ).scalar_one_or_none()

    horizon = datetime.now(timezone.utc) - timedelta(days=14)
    events = db.execute(
        select(
            RiskEvent.new_status,
            RiskEvent.created_at,
            RiskEvent.source_event_type,
        )
        .where(RiskEvent.user_id == user.id, RiskEvent.created_at >= horizon)
        .order_by(RiskEvent.created_at.desc())
        .limit(20)
    ).all()

    trend: list[dict[str, object]] = [
        {
            "status": row[0],
            "at": row[1],
            "source": row[2],
        }
        for row in events
    ]

    return CaseCard(
        user_id=user.id,
        full_name=user.full_name,
        unit_id=user.unit_id,
        current_risk_status=(status.current_risk_status if status else "insufficient_data"),  # type: ignore[arg-type]
        explanation_text=status.explanation_text if status else None,
        calculated_at=status.calculated_at if status else None,
        recent_status_trend=trend,
    )
