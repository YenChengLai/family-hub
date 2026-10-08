"""Household access, tenancy, permissions, and audit (AUTHZ-*, AUDIT-*)."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError

from family_hub.platform.audit.models import AuditEvent
from family_hub.platform.households.models import Membership
from family_hub.platform.identity.models import User

from .conftest import Family, login


def url(family: Family, suffix: str = "") -> str:
    return f"/api/v1/households/{family.household_id}{suffix}"


async def patch(client: AsyncClient, family: Family, csrf: object, body: dict[str, str]) -> int:
    response = await client.patch(url(family), json=body, headers={"X-CSRF-Token": str(csrf)})
    return response.status_code


class TestReadHousehold:
    async def test_member_sees_household_and_members(
        self, client: AsyncClient, family: Family
    ) -> None:
        await login(client, family.adult_email)

        body = (await client.get(url(family))).json()

        assert body["name"] == "Demo Family"
        assert [(m["display_name"], m["role"]) for m in body["members"]] == [
            ("Alice", "owner"),
            ("Bob", "adult"),
            ("Carol", "child"),
        ]

    async def test_child_can_read(self, client: AsyncClient, family: Family) -> None:
        """AUTHZ-3: child holds platform.household.read."""
        await login(client, family.child_email)

        assert (await client.get(url(family))).status_code == 200

    async def test_requires_login(self, client: AsyncClient, family: Family) -> None:
        assert (await client.get(url(family))).status_code == 401

    async def test_other_household_looks_nonexistent(
        self, client: AsyncClient, family: Family, other_family: Family
    ) -> None:
        """AUTHZ-5: a non-member cannot tell whether a household exists."""
        await login(client, other_family.owner_email)

        foreign = await client.get(url(family))
        missing = await client.get(f"/api/v1/households/{uuid.uuid4()}")

        assert foreign.status_code == missing.status_code == 404
        assert foreign.json() == missing.json()


class TestUpdateHousehold:
    async def test_owner_can_rename_and_it_is_audited(
        self, app: FastAPI, client: AsyncClient, family: Family
    ) -> None:
        """AUDIT-1"""
        body = await login(client, family.owner_email)

        assert await patch(client, family, body["csrf_token"], {"name": "Renamed"}) == 200
        assert (await client.get(url(family))).json()["name"] == "Renamed"

        async with app.state.sessionmaker() as db:
            event = await db.scalar(
                select(AuditEvent).where(AuditEvent.action == "platform.household.update")
            )
        assert event is not None
        assert event.before == {"name": "Demo Family"}
        assert event.after == {"name": "Renamed"}
        user = body["user"]
        assert isinstance(user, dict)
        assert str(event.actor_user_id) == user["id"]

    @pytest.mark.parametrize("member", ["adult", "child"])
    async def test_non_owner_cannot_update(
        self, client: AsyncClient, family: Family, member: str
    ) -> None:
        email = family.adult_email if member == "adult" else family.child_email
        body = await login(client, email)

        assert await patch(client, family, body["csrf_token"], {"name": "Nope"}) == 403

    async def test_unknown_timezone_rejected(self, client: AsyncClient, family: Family) -> None:
        body = await login(client, family.owner_email)

        assert await patch(client, family, body["csrf_token"], {"timezone": "Mars/Base"}) == 422

    async def test_unchanged_values_are_not_audited(
        self, app: FastAPI, client: AsyncClient, family: Family
    ) -> None:
        body = await login(client, family.owner_email)

        await patch(client, family, body["csrf_token"], {"name": "Demo Family"})

        async with app.state.sessionmaker() as db:
            count = await db.scalar(
                select(text("count(*)"))
                .select_from(AuditEvent)
                .where(AuditEvent.action == "platform.household.update")
            )
        assert count == 0

    async def test_role_change_applies_on_next_request(
        self, app: FastAPI, client: AsyncClient, family: Family
    ) -> None:
        """ADR-0012: roles are read from memberships on every request, never cached."""
        body = await login(client, family.adult_email)
        assert await patch(client, family, body["csrf_token"], {"name": "X"}) == 403

        async with app.state.sessionmaker() as db, db.begin():
            bob = await db.scalar(select(User.id).where(User.email == family.adult_email))
            await db.execute(
                update(Membership).where(Membership.user_id == bob).values(role="owner")
            )

        assert await patch(client, family, body["csrf_token"], {"name": "X"}) == 200


class TestAuditLog:
    async def test_owner_reads_household_events(self, client: AsyncClient, family: Family) -> None:
        body = await login(client, family.owner_email)
        await patch(client, family, body["csrf_token"], {"timezone": "Europe/London"})

        events = (await client.get(url(family, "/audit-events"))).json()

        assert [e["action"] for e in events] == ["platform.household.update"]
        assert events[0]["after"] == {"timezone": "Europe/London"}

    async def test_adult_cannot_read_audit_log(self, client: AsyncClient, family: Family) -> None:
        await login(client, family.adult_email)

        assert (await client.get(url(family, "/audit-events"))).status_code == 403

    async def test_login_and_logout_are_audited(
        self, app: FastAPI, client: AsyncClient, family: Family
    ) -> None:
        body = await login(client, family.owner_email)
        await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": str(body["csrf_token"])})

        async with app.state.sessionmaker() as db:
            actions = (await db.scalars(select(AuditEvent.action))).all()
        assert sorted(actions) == ["auth.login", "auth.logout"]

    async def test_events_cannot_be_changed_or_deleted(
        self, app: FastAPI, client: AsyncClient, family: Family
    ) -> None:
        """AUDIT-2: enforced by a database trigger, not just application code."""
        await login(client, family.owner_email)

        for statement in (
            "UPDATE platform.audit_events SET action = 'tampered'",
            "DELETE FROM platform.audit_events",
        ):
            async with app.state.engine.begin() as conn:
                with pytest.raises(DBAPIError, match="append-only"):
                    await conn.execute(text(statement))
