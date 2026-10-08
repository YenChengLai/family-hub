"""Administrative command line (AUTH-1: accounts are created here, not via sign-up).

Usage: ``uv run family-hub <command> --help``
"""

import argparse
import asyncio
import getpass
import sys
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from family_hub.config import get_settings
from family_hub.db import create_engine, create_sessionmaker
from family_hub.platform.audit import service as audit
from family_hub.platform.households import service as households
from family_hub.platform.households.models import Role
from family_hub.platform.identity import service as identity
from family_hub.platform.identity.passwords import WeakPasswordError, check_policy

# Fictional accounts for local development only (never real people).
DEV_PASSWORD = "family-hub-dev-password"  # noqa: S105 - development seed only
DEV_HOUSEHOLD = "Demo Family"
DEV_USERS = [
    ("alice@example.com", "Alice", Role.OWNER),
    ("bob@example.com", "Bob", Role.ADULT),
]


def prompt_password() -> str:
    while True:
        password = getpass.getpass("Password: ")
        try:
            check_policy(password)
        except WeakPasswordError as exc:
            print(exc, file=sys.stderr)
            continue
        if getpass.getpass("Repeat password: ") == password:
            return password
        print("Passwords do not match", file=sys.stderr)


async def create_household(db: AsyncSession, args: argparse.Namespace) -> None:
    owner = await identity.create_user(
        db, email=args.owner_email, display_name=args.owner_name, password=prompt_password()
    )
    household = await households.create_household(db, name=args.name, owner=owner)
    await audit.record(
        db,
        source="cli",
        action="platform.household.create",
        entity_type="household",
        entity_id=household.id,
        actor_user_id=None,
        household_id=household.id,
        after={"name": household.name, "owner_user_id": str(owner.id)},
    )
    print(f"Created household {household.id} with owner {owner.email}")


async def add_member(db: AsyncSession, args: argparse.Namespace) -> None:
    user = await identity.create_user(
        db, email=args.email, display_name=args.name, password=prompt_password()
    )
    await households.add_member(db, household_id=args.household_id, user=user, role=args.role)
    await audit.record(
        db,
        source="cli",
        action="platform.member.add",
        entity_type="membership",
        entity_id=user.id,
        actor_user_id=None,
        household_id=args.household_id,
        after={"user_id": str(user.id), "role": str(args.role)},
    )
    print(f"Added {user.email} as {args.role} to household {args.household_id}")


async def seed_dev(db: AsyncSession, _: argparse.Namespace) -> None:
    if get_settings().environment != "development":
        raise SystemExit("seed-dev only runs with FH_ENVIRONMENT=development")
    if await identity.get_user_by_email(db, DEV_USERS[0][0]) is not None:
        print("Development seed already present")
        return
    users = [
        (await identity.create_user(db, email=e, display_name=n, password=DEV_PASSWORD), role)
        for e, n, role in DEV_USERS
    ]
    household = await households.create_household(db, name=DEV_HOUSEHOLD, owner=users[0][0])
    for user, role in users[1:]:
        await households.add_member(db, household_id=household.id, user=user, role=role)
    print(f"Seeded '{DEV_HOUSEHOLD}':")
    for email, _name, role in DEV_USERS:
        print(f"  {email} ({role}) / {DEV_PASSWORD}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="family-hub", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    p = commands.add_parser("create-household", help="Create a household and its owner")
    p.add_argument("--name", required=True)
    p.add_argument("--owner-email", required=True)
    p.add_argument("--owner-name", required=True)
    p.set_defaults(handler=create_household)

    p = commands.add_parser("add-member", help="Create a user and add them to a household")
    p.add_argument("--household-id", required=True, type=uuid.UUID)
    p.add_argument("--email", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--role", required=True, type=Role, choices=[Role.ADULT, Role.CHILD])
    p.set_defaults(handler=add_member)

    p = commands.add_parser("seed-dev", help="Create fictional development accounts")
    p.set_defaults(handler=seed_dev)
    return parser


async def run(args: argparse.Namespace) -> None:
    engine = create_engine(str(get_settings().database_url))
    try:
        async with create_sessionmaker(engine)() as db, db.begin():
            await args.handler(db, args)
    except identity.EmailAlreadyRegisteredError as exc:
        raise SystemExit(f"E-mail already registered: {exc}") from exc
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    main()
