"""Module descriptors and the permission policy built from them (AUTHZ-3, AUTHZ-4).

Policies are code, reviewed in pull requests (ADR-0012). Role membership is
not here: it is read from the memberships table on every request.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import casbin
from fastapi import APIRouter

from family_hub.platform.households.models import Role

# Role hierarchy: each role inherits every permission of the roles it contains.
ROLE_HIERARCHY: tuple[tuple[Role, Role], ...] = ((Role.OWNER, Role.ADULT), (Role.ADULT, Role.CHILD))

CASBIN_MODEL = """
[request_definition]
r = role, obj, act

[policy_definition]
p = role, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.role, p.role) && r.obj == p.obj && r.act == p.act
"""


@dataclass(frozen=True)
class Permission:
    name: str
    """``<module>.<resource>.<action>``, e.g. ``finance.transaction.create``."""
    description: str


@dataclass(frozen=True)
class Module:
    """What a module gives the platform. Nothing else of a module is used (see architecture.md)."""

    name: str
    routers: Sequence[APIRouter]
    """Mounted under ``/api/v1``. Feature-module routes start with ``/<name>``."""
    permissions: Sequence[Permission]
    grants: Mapping[Role, frozenset[str]] = field(default_factory=dict)
    """Permissions granted directly to each role. Inherited ones need not be repeated."""


class ModuleRegistryError(ValueError):
    pass


def split(permission: str) -> tuple[str, str]:
    """``finance.transaction.create`` -> (``finance.transaction``, ``create``)."""
    obj, _, act = permission.rpartition(".")
    return obj, act


def validate(modules: Sequence[Module]) -> None:
    """Fail fast on inconsistent declarations (AUTHZ-4)."""
    seen_modules: set[str] = set()
    seen_permissions: set[str] = set()
    for module in modules:
        if module.name in seen_modules:
            raise ModuleRegistryError(f"duplicate module '{module.name}'")
        seen_modules.add(module.name)
        if module.name != "platform":
            for router in module.routers:
                for route in router.routes:
                    path = getattr(route, "path", "")
                    if not (path == f"/{module.name}" or path.startswith(f"/{module.name}/")):
                        raise ModuleRegistryError(
                            f"route '{path}' of module '{module.name}' must start with "
                            f"'/{module.name}'"
                        )
        declared = set()
        for permission in module.permissions:
            parts = permission.name.split(".")
            if len(parts) != 3 or parts[0] != module.name or not all(parts):
                raise ModuleRegistryError(
                    f"permission '{permission.name}' must be '{module.name}.<resource>.<action>'"
                )
            if permission.name in seen_permissions:
                raise ModuleRegistryError(f"duplicate permission '{permission.name}'")
            seen_permissions.add(permission.name)
            declared.add(permission.name)
        for role, granted in module.grants.items():
            unknown = granted - declared
            if unknown:
                raise ModuleRegistryError(
                    f"module '{module.name}' grants undeclared permissions to {role}: "
                    + ", ".join(sorted(unknown))
                )


class Authorizer:
    """Answers "may this role do this?" from the registered modules."""

    def __init__(self, modules: Sequence[Module]) -> None:
        validate(modules)
        model = casbin.Model()
        model.load_model_from_text(CASBIN_MODEL)
        self._enforcer = casbin.Enforcer(model)
        for parent, child in ROLE_HIERARCHY:
            self._enforcer.add_grouping_policy(parent.value, child.value)
        for module in modules:
            for role, granted in module.grants.items():
                for permission in sorted(granted):
                    self._enforcer.add_policy(role.value, *split(permission))
        self.permissions: dict[str, Permission] = {
            p.name: p for module in modules for p in module.permissions
        }

    def allows(self, role: Role, permission: str) -> bool:
        """Deny by default: unknown permissions are never allowed (AUTHZ-1)."""
        if permission not in self.permissions:
            return False
        return bool(self._enforcer.enforce(role.value, *split(permission)))

    def roles_with(self, permission: str) -> list[Role]:
        return [role for role in Role if self.allows(role, permission)]
