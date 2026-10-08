import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from family_hub.db import Base

SCHEMA = "platform"


class AuditEvent(Base):
    """One recorded change. Rows are never updated or deleted (AUDIT-2).

    IDs are stored without foreign keys so events outlive the rows they
    describe (AUDIT-4).
    """

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_household_occurred", "household_id", "occurred_at"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    source: Mapped[str] = mapped_column(String(10))
    """``api`` or ``cli``."""
    actor_user_id: Mapped[uuid.UUID | None]
    household_id: Mapped[uuid.UUID | None]
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
