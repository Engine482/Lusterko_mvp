"""Case lifecycle (Risk Engine §13 + Backlog EPIC-51).

Auto-open rules (P0.6 update — was: red OR persistent-yellow only):
- a fresh case is opened when status becomes `red` or `yellow`;
- normal/insufficient_data never open a case;
- never duplicate. If the user already has a non-closed case, the new
  risk_event is just attached to it (priority bump implicit by recency of
  `last_risk_event_id`).

Status transitions: new → in_review → monitoring → closed. Re-opening
(monitoring → in_review) is allowed; closed is terminal. Anything else is
rejected with CASE_INVALID_TRANSITION.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import CaseStatus
from app.models.case_review import CaseReview
from app.models.case_review_note import CaseReviewNote
from app.models.risk_event import RiskEvent
from app.services.audit_logger import log_event


_OPEN_STATUSES: frozenset[CaseStatus] = frozenset({"new", "in_review", "monitoring"})

# Allowed transitions per Spec §13 (re-opening monitoring → in_review is
# permitted because new risk events can resurface a "settled" case).
_TRANSITIONS: dict[CaseStatus, frozenset[CaseStatus]] = {
    "new": frozenset({"in_review", "closed"}),
    "in_review": frozenset({"monitoring", "closed"}),
    "monitoring": frozenset({"in_review", "closed"}),
    "closed": frozenset(),
}


class CaseError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def open_case_for(db: Session, *, user_id: uuid.UUID) -> CaseReview | None:
    return db.execute(
        select(CaseReview)
        .where(CaseReview.user_id == user_id, CaseReview.status != "closed")
        .order_by(CaseReview.opened_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def maybe_open_case(
    db: Session,
    *,
    user_id: uuid.UUID,
    risk_event: RiskEvent,
) -> CaseReview | None:
    """Called from `risk_service.recompute` after a new event is flushed.

    Returns the open case if one exists or was created (with the new event
    attached); returns None if no case is warranted yet.
    """

    existing = open_case_for(db, user_id=user_id)

    # P0.6: yellow and red both open a case on the first signal.
    # Normal / insufficient_data never open a psychologist case.
    should_open = risk_event.new_status in ("red", "yellow")

    if existing is not None:
        # De-dup: just attach the new event so the dashboards bump priority.
        existing.last_risk_event_id = risk_event.id
        return existing

    if not should_open:
        return None

    case = CaseReview(
        user_id=user_id,
        status="new",
        opened_at=datetime.now(timezone.utc),
        last_risk_event_id=risk_event.id,
    )
    db.add(case)
    db.flush()
    log_event(
        db,
        event_type="case_opened",
        actor_user_id=None,  # auto-opened by the engine
        target_user_id=user_id,
        entity_type="case_reviews",
        entity_id=case.id,
        metadata={
            "trigger_status": risk_event.new_status,
            "hard_flag": risk_event.hard_flag,
            "risk_event_id": str(risk_event.id),
        },
    )
    return case


def update_status(
    db: Session,
    *,
    case_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    new_status: CaseStatus,
) -> CaseReview:
    case = db.get(CaseReview, case_id)
    if case is None:
        raise CaseError("NOT_FOUND", "Case not found.")
    current: CaseStatus = case.status  # type: ignore[assignment]
    if new_status not in _TRANSITIONS[current]:
        raise CaseError(
            "CASE_INVALID_TRANSITION",
            f"Cannot move case from '{current}' to '{new_status}'.",
        )
    case.status = new_status
    if new_status == "closed":
        case.closed_at = datetime.now(timezone.utc)
    else:
        case.closed_at = None
    if case.assigned_to_user_id is None and new_status == "in_review":
        case.assigned_to_user_id = actor_user_id
    log_event(
        db,
        event_type="case_status_changed",
        actor_user_id=actor_user_id,
        target_user_id=case.user_id,
        entity_type="case_reviews",
        entity_id=case.id,
        metadata={"from": current, "to": new_status},
    )
    return case


def add_note(
    db: Session,
    *,
    case_id: uuid.UUID,
    author_user_id: uuid.UUID,
    text: str,
) -> CaseReviewNote:
    case = db.get(CaseReview, case_id)
    if case is None:
        raise CaseError("NOT_FOUND", "Case not found.")
    cleaned = text.strip()
    if not cleaned:
        raise CaseError("VALIDATION_ERROR", "Note text cannot be empty.")
    if len(cleaned) > 4000:
        raise CaseError("VALIDATION_ERROR", "Note text exceeds 4000 characters.")
    note = CaseReviewNote(
        case_review_id=case.id,
        author_user_id=author_user_id,
        text=cleaned,
    )
    db.add(note)
    db.flush()
    log_event(
        db,
        event_type="case_note_added",
        actor_user_id=author_user_id,
        target_user_id=case.user_id,
        entity_type="case_review_notes",
        entity_id=note.id,
        metadata={"case_review_id": str(case.id), "length": len(cleaned)},
    )
    return note
