"""User and session operations. No HTTP concerns here."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from family_hub.platform.identity.models import AuthSession, User
from family_hub.platform.identity.passwords import hash_password, verify_password
from family_hub.platform.identity.tokens import hash_session_token, new_session_token

# Avoid a write on every request: refresh last_seen_at at most this often.
LAST_SEEN_RESOLUTION = timedelta(minutes=5)


class EmailAlreadyRegisteredError(ValueError):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def now() -> datetime:
    return datetime.now(UTC)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == normalize_email(email)))


async def create_user(db: AsyncSession, *, email: str, display_name: str, password: str) -> User:
    if await get_user_by_email(db, email) is not None:
        raise EmailAlreadyRegisteredError(email)
    user = User(
        email=normalize_email(email),
        display_name=display_name.strip(),
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate(db: AsyncSession, *, email: str, password: str) -> User | None:
    """Return the user if the credentials are valid and the account is active (AUTH-3)."""
    user = await get_user_by_email(db, email)
    valid, new_hash = verify_password(password, user.password_hash if user else None)
    if user is None or not valid or not user.is_active:
        return None
    if new_hash is not None:
        user.password_hash = new_hash
    return user


@dataclass(frozen=True)
class SessionTimeouts:
    idle: timedelta
    absolute: timedelta


async def start_session(
    db: AsyncSession, *, user: User, timeouts: SessionTimeouts, user_agent: str | None
) -> str:
    """Create a session and return its token. The token is never stored (AUTH-5)."""
    token = new_session_token()
    started = now()
    db.add(
        AuthSession(
            token_hash=hash_session_token(token),
            user_id=user.id,
            created_at=started,
            last_seen_at=started,
            expires_at=started + timeouts.absolute,
            user_agent=(user_agent or "")[:255] or None,
        )
    )
    await db.flush()
    return token


async def resolve_session(
    db: AsyncSession, *, token: str, timeouts: SessionTimeouts
) -> tuple[AuthSession, User] | None:
    """Return the live session and its user, or ``None`` if invalid (AUTH-6)."""
    current = now()
    row = (
        await db.execute(
            select(AuthSession, User)
            .join(User, User.id == AuthSession.user_id)
            .where(
                AuthSession.token_hash == hash_session_token(token),
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > current,
                AuthSession.last_seen_at > current - timeouts.idle,
                User.is_active.is_(True),
            )
        )
    ).one_or_none()
    if row is None:
        return None
    session, user = row
    if current - session.last_seen_at > LAST_SEEN_RESOLUTION:
        session.last_seen_at = current
    return session, user


async def revoke_session(db: AsyncSession, *, token: str) -> None:
    await db.execute(
        update(AuthSession)
        .where(
            AuthSession.token_hash == hash_session_token(token),
            AuthSession.revoked_at.is_(None),
        )
        .values(revoked_at=now())
    )


async def revoke_all_sessions(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    await db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=now())
    )
