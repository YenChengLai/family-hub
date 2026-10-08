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


async def role_in(db: AsyncSession, *, household_id: uuid.UUID, user_id: uuid.UUID) -> Role | None:
    """The user's role in the household, or ``None`` if not a member. Read on every request."""
    role = await db.scalar(
        select(Membership.role).where(
            Membership.household_id == household_id, Membership.user_id == user_id
        )
    )
    return Role(role) if role is not None else None


@dataclass(frozen=True)
class Member:
    user_id: uuid.UUID
    display_name: str
    role: Role


async def get_household(db: AsyncSession, household_id: uuid.UUID) -> Household | None:
    return await db.get(Household, household_id)


async def members_of(db: AsyncSession, household_id: uuid.UUID) -> list[Member]:
    rows = await db.execute(
        select(User.id, User.display_name, Membership.role)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.household_id == household_id)
        .order_by(Membership.created_at)
    )
    return [Member(uid, name, Role(role)) for uid, name, role in rows]
