"""Record and read audit events (AUDIT-1..4)."""

import uuid
from collections.abc import Sequence
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from family_hub.platform.audit.models import AuditEvent

Source = Literal["api", "cli"]

# Never written to the log, whatever a caller passes (AUDIT-3).
SECRET_FIELDS = frozenset({"password", "password_hash", "token", "token_hash", "secret"})


def _scrub(values: dict[str, Any] | None) -> dict[str, Any] | None:
    if values is None:
        return None
    return {k: v for k, v in values.items() if k not in SECRET_FIELDS}


async def record(
    db: AsyncSession,
    *,
    source: Source,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | str | None,
    actor_user_id: uuid.UUID | None,
    household_id: uuid.UUID | None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> None:
    """Add an event to the caller's transaction, so it commits or rolls back with the change."""
    db.add(
        AuditEvent(
            source=source,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            actor_user_id=actor_user_id,
            household_id=household_id,
            before=_scrub(before),
            after=_scrub(after),
        )
    )
    await db.flush()


async def for_household(
    db: AsyncSession, household_id: uuid.UUID, *, limit: int
) -> Sequence[AuditEvent]:
    result = await db.scalars(
        select(AuditEvent)
        .where(AuditEvent.household_id == household_id)
        .order_by(AuditEvent.occurred_at.desc(), AuditEvent.id)
        .limit(limit)
    )
    return result.all()
