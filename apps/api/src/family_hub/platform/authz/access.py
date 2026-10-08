"""Every route declares exactly one access rule (AUTHZ-2).

- ``public``: anyone, e.g. health checks and login.
- ``authenticated``: any logged-in user, no household involved.
- ``require_permission("<permission>")``: a member of the household in the
  path whose role holds the permission. Non-members get 404, so household IDs
  cannot be probed (AUTHZ-5).

``check_routes`` runs at startup: the app refuses to start if a route has no
access rule, more than one, or names an unknown permission.
"""

import uuid
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from fastapi import Depends, HTTPException, Request, status
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from family_hub.platform.authz.registry import Authorizer, Module
from family_hub.platform.dependencies import DbDep, Principal, PrincipalDep
from family_hub.platform.households.models import Role
from family_hub.platform.households.service import role_in

ACCESS_ATTRIBUTE = "__family_hub_access__"


@dataclass(frozen=True)
class Access:
    kind: Literal["public", "authenticated", "permission"]
    permission: str | None = None


def _declare(access: Access) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def mark(func: Callable[..., Any]) -> Callable[..., Any]:
        setattr(func, ACCESS_ATTRIBUTE, access)
        return func

    return mark


@_declare(Access("public"))
async def public() -> None:
    """Access rule: no login required."""


@_declare(Access("authenticated"))
async def authenticated(principal: PrincipalDep) -> Principal:
    """Access rule: any logged-in user."""
    return principal


@dataclass(frozen=True)
class HouseholdContext:
    """The caller, acting within one household they belong to."""

    household_id: uuid.UUID
    role: Role
    principal: Principal


def get_authorizer(request: Request) -> Authorizer:
    authorizer: Authorizer = request.app.state.authorizer
    return authorizer


def require_permission(permission: str) -> Callable[..., Any]:
    """Access rule: member of ``{household_id}`` with ``permission``."""

    @_declare(Access("permission", permission))
    async def dependency(
        household_id: uuid.UUID,
        principal: PrincipalDep,
        db: DbDep,
        authorizer: Annotated[Authorizer, Depends(get_authorizer)],
    ) -> HouseholdContext:
        role = await role_in(db, household_id=household_id, user_id=principal.user.id)
        if role is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Household not found")
        if not authorizer.allows(role, permission):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")
        return HouseholdContext(household_id=household_id, role=role, principal=principal)

    dependency.__name__ = f"require_permission[{permission}]"
    return dependency


def _accesses(dependant: Dependant) -> Iterator[Access]:
    for sub in dependant.dependencies:
        access = getattr(sub.call, ACCESS_ATTRIBUTE, None)
        if isinstance(access, Access):
            yield access
        yield from _accesses(sub)


def route_access(route: APIRoute) -> list[Access]:
    return list(dict.fromkeys(_accesses(route.dependant)))


class AccessDeclarationError(RuntimeError):
    pass


def module_routes(modules: Sequence[Module], prefix: str) -> Iterator[tuple[str, APIRoute]]:
    """Every API route with its full path. Walks the modules' own routers (public API)."""
    for module in modules:
        for router in module.routers:
            for route in router.routes:
                if not isinstance(route, APIRoute):
                    raise AccessDeclarationError(
                        f"module '{module.name}': nested routers are not supported; "
                        "list each router in Module.routers"
                    )
                yield prefix + route.path, route


def check_routes(modules: Sequence[Module], authorizer: Authorizer, prefix: str) -> None:
    for path, route in module_routes(modules, prefix):
        accesses = route_access(route)
        where = f"{sorted(route.methods or ())} {path}"
        if len(accesses) != 1:
            raise AccessDeclarationError(
                f"{where} must declare exactly one access rule, found {len(accesses)}"
            )
        permission = accesses[0].permission
        if permission is not None and permission not in authorizer.permissions:
            raise AccessDeclarationError(f"{where} requires unknown permission '{permission}'")
