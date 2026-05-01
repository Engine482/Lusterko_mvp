from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import RISK_DOMAINS
from app.db.base import Base, CreatedAtMixin, UUIDPKMixin

_DOMAIN_CHECK = ", ".join(f"'{d}'" for d in RISK_DOMAINS)


class RiskRuleHit(UUIDPKMixin, CreatedAtMixin, Base):
    """Per-rule contribution to a risk_event (DB Schema §5.3)."""

    __tablename__ = "risk_rule_hits"
    __table_args__ = (
        CheckConstraint(f"domain in ({_DOMAIN_CHECK})", name="domain_allowed"),
    )

    risk_event_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("risk_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_code: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="'{}'::jsonb"
    )
