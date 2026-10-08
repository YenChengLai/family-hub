"""Household endpoints. Every route is scoped to a household the caller belongs to (AUTHZ-5)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from family_hub.platform.audit import service as audit
from family_hub.platform.authz.access import HouseholdContext, require_permission
from family_hub.platform.dependencies import DbDep
from family_hub.platform.households import service
from family_hub.platform.households.schemas import (
    AuditEventOut,
    HouseholdOut,
    HouseholdUpdate,
    MemberOut,
)

router = APIRouter(prefix="/households", tags=["households"])

ReadHousehold = Annotated[HouseholdContext, Depends(require_permission("platform.household.read"))]
ManageHousehold = Annotated[
    HouseholdContext, Depends(require_permission("platform.household.manage"))
]
ReadAudit = Annotated[HouseholdContext, Depends(require_permission("platform.audit.read"))]


async def _household_out(db: DbDep, ctx: HouseholdContext) -> HouseholdOut:
    household = await service.get_household(db, ctx.household_id)
    if household is None:  # membership exists, so this only happens mid-deletion
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Household not found")
    members = await service.members_of(db, ctx.household_id)
    return HouseholdOut(
        id=household.id,
        name=household.name,
        timezone=household.timezone,
        members=[
            MemberOut(user_id=m.user_id, display_name=m.display_name, role=m.role) for m in members
        ],
    )


@router.get("/{household_id}", summary="Household and its members")
async def get_household(ctx: ReadHousehold, db: DbDep) -> HouseholdOut:
    return await _household_out(db, ctx)


@router.patch("/{household_id}", summary="Rename or change time zone")
async def update_household(body: HouseholdUpdate, ctx: ManageHousehold, db: DbDep) -> HouseholdOut:
    household = await service.get_household(db, ctx.household_id)
    if household is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Household not found")
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    before = {field: getattr(household, field) for field in changes}
    changes = {k: v for k, v in changes.items() if before[k] != v}
    if changes:
        for field, value in changes.items():
            setattr(household, field, value)
        await audit.record(
            db,
            source="api",
            action="platform.household.update",
            entity_type="household",
            entity_id=household.id,
            actor_user_id=ctx.principal.user.id,
            household_id=household.id,
            before={k: before[k] for k in changes},
            after=changes,
        )
    return await _household_out(db, ctx)


@router.get("/{household_id}/audit-events", summary="Recent audit events, newest first")
async def list_audit_events(
    ctx: ReadAudit, db: DbDep, limit: Annotated[int, Query(ge=1, le=200)] = 50
) -> list[AuditEventOut]:
    events = await audit.for_household(db, ctx.household_id, limit=limit)
    return [AuditEventOut.model_validate(e, from_attributes=True) for e in events]
