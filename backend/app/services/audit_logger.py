"""Skeleton helper for `audit_logs` writes (Sprint 0 deliverable).

Coverage of the suggested event types lives in `core.constants.AuditEventType`
and is enforced by callers in later sprints (Backlog TASK-1301..1303,
TASK-2801..2803, TASK-3901..3903, TASK-4701..4703, TASK-5701..5706).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.constants import AuditEventType
from app.models.audit_log import AuditLog


def log_event(
    session: Session,
    *,
    event_type: AuditEventType,
    actor_user_id: uuid.UUID | None = None,
    target_user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {},
        ip_address=ip_address,
    )
    session.add(entry)
    return entry
