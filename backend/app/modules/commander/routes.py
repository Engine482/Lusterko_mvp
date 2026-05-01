"""Commander API per `Lusterko_API_Contracts_v1.md` §6 + RBAC §5.3, §6.2.

Unit-scope is the only permission boundary here: a commander can only see
soldiers whose `users.unit_id == commander.unit_id`. A commander without a
unit_id sees no soldiers — we do not silently fall back to a global view.

Field policy (RBAC §6.2): commander never sees item-level PHQ-4/PSS-4, raw
cognitive payload, raw AI JSON, confidence_score, or medic notes. The
serializers in this module are the only place commander data crosses the
HTTP boundary, so field filtering is centralized.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from datetime import datetime

from app.core.api_response import error_response, success_response
from app.core.constants import RISK_STATUSES, RiskStatus
from app.modules.auth.dependencies import (
    SessionContext,
    get_db,
    require_role,
)
from app.modules.commander import queries
from app.services.audit_logger import log_event

router = APIRouter(
    prefix="/commander",
    tags=["commander"],
    dependencies=[Depends(require_role("commander"))],
)


def _require_unit(ctx: SessionContext) -> uuid.UUID | None:
    return ctx.user.unit_id


@router.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("commander")),
) -> Response:
    unit_id = _require_unit(ctx)
    if unit_id is None:
        db.commit()
        return success_response(
            {"unit_id": None, "counts": {s: 0 for s in RISK_STATUSES}}
        )
    counts = queries.status_counts(db, unit_id=unit_id)
    db.commit()
    return success_response(
        {"unit_id": str(unit_id), "counts": dict(counts)}
    )


@router.get("/dashboard/cases")
def dashboard_cases(
    status_filter: RiskStatus | None = Query(default=None, alias="status"),
    name: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("commander")),
) -> Response:
    unit_id = _require_unit(ctx)
    if unit_id is None:
        db.commit()
        return success_response({"cases": []})
    rows = queries.cases_in_unit(
        db, unit_id=unit_id, status_filter=status_filter, name_query=name
    )
    payload = [
        {
            "user_id": str(r.user_id),
            "full_name": r.full_name,
            "current_risk_status": r.current_risk_status,
            "explanation_text": r.explanation_text,
            "calculated_at": (
                r.calculated_at.isoformat() if r.calculated_at else None
            ),
            "last_daily_at": (
                r.last_daily_at.isoformat() if r.last_daily_at else None
            ),
        }
        for r in rows
    ]
    db.commit()
    return success_response({"cases": payload})


@router.get("/cases/{user_id}")
def commander_case_card(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("commander")),
) -> Response:
    unit_id = _require_unit(ctx)
    if unit_id is None:
        log_event(
            db,
            event_type="cross_unit_access_denied",
            actor_user_id=ctx.user.id,
            target_user_id=user_id,
            entity_type="users",
            entity_id=user_id,
            metadata={"reason": "commander has no unit"},
        )
        db.commit()
        return error_response("FORBIDDEN", "Commander has no unit assigned.")

    card = queries.case_card(db, unit_id=unit_id, target_user_id=user_id)
    if card is None:
        log_event(
            db,
            event_type="cross_unit_access_denied",
            actor_user_id=ctx.user.id,
            target_user_id=user_id,
            entity_type="users",
            entity_id=user_id,
            metadata={"reason": "outside commander unit or not a soldier"},
        )
        db.commit()
        # Same response shape as missing user — do not leak existence across
        # units (RBAC §6.2 forbids cross-unit visibility).
        return error_response("NOT_FOUND", "Case not available.")

    log_event(
        db,
        event_type="commander_case_viewed",
        actor_user_id=ctx.user.id,
        target_user_id=card.user_id,
        entity_type="users",
        entity_id=card.user_id,
        metadata={
            "current_risk_status": card.current_risk_status,
            "unit_id": str(unit_id),
        },
    )
    db.commit()
    return success_response(
        {
            "user_id": str(card.user_id),
            "full_name": card.full_name,
            "unit_id": str(card.unit_id) if card.unit_id else None,
            "current_risk_status": card.current_risk_status,
            "explanation_text": card.explanation_text,
            "calculated_at": (
                card.calculated_at.isoformat() if card.calculated_at else None
            ),
            "recent_status_trend": [
                {
                    "status": entry["status"],
                    "at": (
                        entry["at"].isoformat()
                        if isinstance(entry["at"], datetime)
                        else None
                    ),
                    "source": entry["source"],
                }
                for entry in card.recent_status_trend
            ],
        }
    )
