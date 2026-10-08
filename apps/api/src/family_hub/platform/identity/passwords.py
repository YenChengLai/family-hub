"""Password hashing and policy (AUTH-2)."""

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

MIN_LENGTH = 12
MAX_LENGTH = 128

_hasher = PasswordHash((Argon2Hasher(),))

# Verified against when the e-mail is unknown, so both failure paths cost the
# same time and do not reveal whether an account exists (AUTH-3).
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing-equalization")


class WeakPasswordError(ValueError):
    pass


def check_policy(password: str) -> None:
    """Length-based policy, following NIST SP 800-63B."""
    if len(password) < MIN_LENGTH:
        raise WeakPasswordError(f"Password must be at least {MIN_LENGTH} characters")
    if len(password) > MAX_LENGTH:
        raise WeakPasswordError(f"Password must be at most {MAX_LENGTH} characters")


def hash_password(password: str) -> str:
    check_policy(password)
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> tuple[bool, str | None]:
    """Return ``(valid, new_hash)``. ``new_hash`` is set when parameters need upgrading.

    Pass ``password_hash=None`` for an unknown account; a dummy hash is checked
    so the call takes the same time and always fails.
    """
    if password_hash is None:
        _hasher.verify(password, _DUMMY_HASH)
        return False, None
    return _hasher.verify_and_update(password, password_hash)
