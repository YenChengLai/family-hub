import uuid

from pydantic import BaseModel, Field

from family_hub.platform.households.models import Role
from family_hub.platform.identity.passwords import MAX_LENGTH


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    # Only the upper bound is enforced at login; the policy applies when setting a password.
    password: str = Field(min_length=1, max_length=MAX_LENGTH)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str


class MembershipOut(BaseModel):
    household_id: uuid.UUID
    household_name: str
    role: Role


class SessionOut(BaseModel):
    user: UserOut
    memberships: list[MembershipOut]
    csrf_token: str
    """Send this back as the ``X-CSRF-Token`` header on state-changing requests."""
