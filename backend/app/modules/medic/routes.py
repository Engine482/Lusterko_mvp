"""Medic / psychologist API per `Lusterko_API_Contracts_v1.md` §7.

Unit-scope: a medic can only act on case_reviews whose user is in the same
unit as the medic (`Lusterko_RBAC_Matrix_v1.md` §8). Field policy per RBAC
§6.3 — medic gets the detailed clinical signals that the commander does not.

Cross-unit attempts return NOT_FOUND (no existence leak) and are recorded as
denied_sensitive_access in the audit log.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.api_response import error_response, success_response
from app.core.constants import CaseStatus, RiskStatus
from app.modules.auth.dependencies import (
    SessionContext,
    get_db,
    require_role,
)
from app.modules.cases import service as cases_service
from app.modules.medic import queries
from app.services.audit_logger import log_event

router = APIRouter(
    prefix="/medic",
    tags=["medic"],
    dependencies=[Depends(require_role("medic_psych"))],
)


class UpdateStatusBody(BaseModel):
    status: CaseStatus


class AddNoteBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


def _detail_payload(detail: queries.MedicCaseDetail) -> dict[str, object]:
    return {
        "case_id": str(detail.case_id),
        "case_status": detail.case_status,
        "opened_at": detail.opened_at.isoformat(),
        "closed_at": detail.closed_at.isoformat() if detail.closed_at else None,
        "assigned_to_user_id": (
            str(detail.assigned_to_user_id) if detail.assigned_to_user_id else None
        ),
        "user": {
            "user_id": str(detail.user_id),
            "full_name": detail.full_name,
            "unit_id": str(detail.unit_id) if detail.unit_id else None,
        },
        "risk": {
            "current_risk_status": detail.current_risk_status,
            "current_risk_score": (
                str(detail.current_risk_score)
                if detail.current_risk_score is not None
                else None
            ),
            "explanation_text": detail.explanation_text,
            "hard_flag": detail.hard_flag,
        },
        "latest_daily": (
            {
                "checkin_date": detail.latest_daily.checkin_date.isoformat(),
                "sleep_score": detail.latest_daily.sleep_score,
                "energy_score": detail.latest_daily.energy_score,
                "mood_score": detail.latest_daily.mood_score,
                "concentration_score": detail.latest_daily.concentration_score,
                "comment_text": detail.latest_daily.comment_text,
            }
            if detail.latest_daily
            else None
        ),
        "latest_weekly": {
            "phq4_total": detail.latest_weekly.phq4_total,
            "pss4_total": detail.latest_weekly.pss4_total,
            "phq4_at": (
                detail.latest_weekly.phq4_at.isoformat()
                if detail.latest_weekly.phq4_at
                else None
            ),
            "pss4_at": (
                detail.latest_weekly.pss4_at.isoformat()
                if detail.latest_weekly.pss4_at
                else None
            ),
        },
        "latest_cognitive": {
            "reaction_median_ms": detail.latest_cognitive.reaction_median_ms,
            "reaction_at": (
                detail.latest_cognitive.reaction_at.isoformat()
                if detail.latest_cognitive.reaction_at
                else None
            ),
            "gonogo_commission_errors": detail.latest_cognitive.gonogo_commission_errors,
            "gonogo_omission_errors": detail.latest_cognitive.gonogo_omission_errors,
            "gonogo_at": (
                detail.latest_cognitive.gonogo_at.isoformat()
                if detail.latest_cognitive.gonogo_at
                else None
            ),
        },
        "latest_ai": {
            "summary_for_system": detail.latest_ai.summary_for_system,
            "parse_status": detail.latest_ai.parse_status,
            "text_risk_level": detail.latest_ai.text_risk_level,
            "markers": list(detail.latest_ai.markers),
        },
        "notes": [
            {
                "id": str(n.id),
                "author_user_id": str(n.author_user_id),
                "text": n.text,
                "created_at": n.created_at.isoformat(),
            }
            for n in detail.notes
        ],
    }


def _deny(
    db: Session, *, actor_id: uuid.UUID, target_case_id: uuid.UUID, reason: str
) -> Response:
    log_event(
        db,
        event_type="denied_sensitive_access",
        actor_user_id=actor_id,
        target_user_id=None,
        entity_type="case_reviews",
        entity_id=target_case_id,
        metadata={"reason": reason},
    )
    db.commit()
    return error_response("NOT_FOUND", "Case not available.")


@router.get("/cases")
def list_cases(
    case_status: CaseStatus | None = Query(default=None),
    risk: RiskStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("medic_psych")),
) -> Response:
    unit_id = ctx.user.unit_id
    if unit_id is None:
        db.commit()
        return success_response({"cases": []})
    rows = queries.list_priority_cases(
        db,
        unit_id=unit_id,
        case_status_filter=case_status,
        risk_filter=risk,
    )
    payload = [
        {
            "case_id": str(r.case_id),
            "user_id": str(r.user_id),
            "full_name": r.full_name,
            "case_status": r.case_status,
            "current_risk_status": r.current_risk_status,
            "opened_at": r.opened_at.isoformat(),
            "last_event_at": (
                r.last_event_at.isoformat() if r.last_event_at else None
            ),
        }
        for r in rows
    ]
    db.commit()
    return success_response({"cases": payload})


@router.get("/cases/{case_id}")
def get_case(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("medic_psych")),
) -> Response:
    unit_id = ctx.user.unit_id
    if unit_id is None:
        return _deny(
            db,
            actor_id=ctx.user.id,
            target_case_id=case_id,
            reason="medic has no unit",
        )
    detail = queries.case_detail(db, unit_id=unit_id, case_id=case_id)
    if detail is None:
        return _deny(
            db,
            actor_id=ctx.user.id,
            target_case_id=case_id,
            reason="case outside medic unit or missing",
        )
    log_event(
        db,
        event_type="medic_case_viewed",
        actor_user_id=ctx.user.id,
        target_user_id=detail.user_id,
        entity_type="case_reviews",
        entity_id=detail.case_id,
        metadata={
            "case_status": detail.case_status,
            "current_risk_status": detail.current_risk_status,
        },
    )
    db.commit()
    return success_response(_detail_payload(detail))


@router.patch("/cases/{case_id}")
def update_case_status(
    case_id: uuid.UUID,
    payload: UpdateStatusBody,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("medic_psych")),
) -> Response:
    unit_id = ctx.user.unit_id
    if unit_id is None:
        return _deny(
            db,
            actor_id=ctx.user.id,
            target_case_id=case_id,
            reason="medic has no unit",
        )
    detail = queries.case_detail(db, unit_id=unit_id, case_id=case_id)
    if detail is None:
        return _deny(
            db,
            actor_id=ctx.user.id,
            target_case_id=case_id,
            reason="case outside medic unit or missing",
        )
    try:
        case = cases_service.update_status(
            db,
            case_id=case_id,
            actor_user_id=ctx.user.id,
            new_status=payload.status,
        )
    except cases_service.CaseError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        {
            "case_id": str(case.id),
            "case_status": case.status,
            "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        }
    )


@router.post("/cases/{case_id}/notes")
def add_case_note(
    case_id: uuid.UUID,
    payload: AddNoteBody,
    db: Session = Depends(get_db),
    ctx: SessionContext = Depends(require_role("medic_psych")),
) -> Response:
    unit_id = ctx.user.unit_id
    if unit_id is None:
        return _deny(
            db,
            actor_id=ctx.user.id,
            target_case_id=case_id,
            reason="medic has no unit",
        )
    detail = queries.case_detail(db, unit_id=unit_id, case_id=case_id)
    if detail is None:
        return _deny(
            db,
            actor_id=ctx.user.id,
            target_case_id=case_id,
            reason="case outside medic unit or missing",
        )
    try:
        note = cases_service.add_note(
            db,
            case_id=case_id,
            author_user_id=ctx.user.id,
            text=payload.text,
        )
    except cases_service.CaseError as err:
        db.rollback()
        return error_response(err.code, err.message)  # type: ignore[arg-type]
    db.commit()
    return success_response(
        {
            "note_id": str(note.id),
            "case_review_id": str(note.case_review_id),
            "created_at": note.created_at.isoformat(),
        }
    )
