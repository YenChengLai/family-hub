"""Household and membership operations."""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from family_hub.platform.households.models import Household, Membership, Role
from family_hub.platform.identity.models import User


@dataclass(frozen=True)
class HouseholdMembership:
    household_id: uuid.UUID
    household_name: str
    role: Role


async def create_household(db: AsyncSession, *, name: str, owner: User) -> Household:
    household = Household(name=name.strip())
    db.add(household)
    await db.flush()
    db.add(Membership(household_id=household.id, user_id=owner.id, role=Role.OWNER))
    await db.flush()
    return household


async def add_member(
    db: AsyncSession, *, household_id: uuid.UUID, user: User, role: Role
) -> Membership:
    membership = Membership(household_id=household_id, user_id=user.id, role=role)
    db.add(membership)
    await db.flush()
    return membership


async def memberships_of(db: AsyncSession, user_id: uuid.UUID) -> list[HouseholdMembership]:
    rows = await db.execute(
        select(Household.id, Household.name, Membership.role)
        .join(Membership, Membership.household_id == Household.id)
        .where(Membership.user_id == user_id)
        .order_by(Household.created_at)
    )
    return [HouseholdMembership(hid, name, Role(role)) for hid, name, role in rows]
