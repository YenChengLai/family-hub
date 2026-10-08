import uuid
from datetime import datetime
from typing import Any
from zoneinfo import available_timezones

from pydantic import BaseModel, Field, field_validator

from family_hub.platform.households.models import Role


class MemberOut(BaseModel):
    user_id: uuid.UUID
    display_name: str
    role: Role


class HouseholdOut(BaseModel):
    id: uuid.UUID
    name: str
    timezone: str
    members: list[MemberOut]


class HouseholdUpdate(BaseModel):
    """Only the fields that are sent are changed."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    timezone: str | None = Field(default=None, description="IANA name, e.g. Asia/Taipei")

    @field_validator("timezone")
    @classmethod
    def known_timezone(cls, value: str | None) -> str | None:
        if value is not None and value not in available_timezones():
            raise ValueError("unknown time zone")
        return value


class AuditEventOut(BaseModel):
    id: uuid.UUID
    occurred_at: datetime
    source: str
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
