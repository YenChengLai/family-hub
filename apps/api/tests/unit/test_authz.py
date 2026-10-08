"""Registry, role hierarchy, and route access declarations (AUTHZ-1..4)."""

import pytest
from fastapi import APIRouter, Depends

from family_hub.main import API_PREFIX, create_app
from family_hub.modules import MODULES
from family_hub.platform.authz.access import (
    AccessDeclarationError,
    authenticated,
    module_routes,
    public,
    require_permission,
    route_access,
)
from family_hub.platform.authz.registry import Authorizer, Module, ModuleRegistryError, Permission
from family_hub.platform.households.models import Role
from family_hub.platform.module import PLATFORM


def demo_module(router: APIRouter | None = None, **overrides: object) -> Module:
    fields: dict[str, object] = {
        "name": "demo",
        "routers": (router or APIRouter(prefix="/demo"),),
        "permissions": (
            Permission("demo.item.read", "Read items"),
            Permission("demo.item.delete", "Delete items"),
        ),
        "grants": {
            Role.CHILD: frozenset({"demo.item.read"}),
            Role.OWNER: frozenset({"demo.item.delete"}),
        },
    }
    fields.update(overrides)
    return Module(**fields)  # type: ignore[arg-type]


class TestRoleHierarchy:
    """AUTHZ-3: owner ⊇ adult ⊇ child."""

    def test_permissions_are_inherited_upwards(self) -> None:
        authorizer = Authorizer([demo_module()])

        assert authorizer.roles_with("demo.item.read") == [Role.OWNER, Role.ADULT, Role.CHILD]
        assert authorizer.roles_with("demo.item.delete") == [Role.OWNER]

    def test_unknown_permission_is_denied(self) -> None:
        """AUTHZ-1"""
        authorizer = Authorizer([demo_module()])

        assert not authorizer.allows(Role.OWNER, "demo.item.update")


class TestRegistryValidation:
    """AUTHZ-4"""

    def test_permission_must_be_namespaced_by_module(self) -> None:
        bad = demo_module(permissions=(Permission("other.item.read", "x"),), grants={})
        with pytest.raises(ModuleRegistryError, match="must be 'demo"):
            Authorizer([bad])

    def test_cannot_grant_undeclared_permission(self) -> None:
        bad = demo_module(grants={Role.ADULT: frozenset({"demo.item.update"})})
        with pytest.raises(ModuleRegistryError, match="undeclared"):
            Authorizer([bad])

    def test_module_names_are_unique(self) -> None:
        with pytest.raises(ModuleRegistryError, match="duplicate module"):
            Authorizer([demo_module(), demo_module(permissions=(), grants={})])


class TestRouteAccessDeclarations:
    """AUTHZ-2: the app refuses to start unless every route declares one access rule."""

    def test_route_without_access_rule_blocks_startup(self) -> None:
        router = APIRouter(prefix="/demo")

        @router.get("/open")
        async def forgot_access() -> None: ...

        with pytest.raises(AccessDeclarationError, match="exactly one access rule, found 0"):
            create_app(modules=[demo_module(router)])

    def test_route_with_two_access_rules_blocks_startup(self) -> None:
        router = APIRouter(prefix="/demo")

        @router.get("/twice", dependencies=[Depends(public), Depends(authenticated)])
        async def twice() -> None: ...

        with pytest.raises(AccessDeclarationError, match="found 2"):
            create_app(modules=[demo_module(router)])

    def test_route_requiring_unknown_permission_blocks_startup(self) -> None:
        router = APIRouter(prefix="/demo")

        @router.get(
            "/{household_id}/x", dependencies=[Depends(require_permission("demo.item.fly"))]
        )
        async def unknown() -> None: ...

        with pytest.raises(AccessDeclarationError, match=r"unknown permission 'demo\.item\.fly'"):
            create_app(modules=[demo_module(router)])

    def test_check_covers_every_served_operation(self) -> None:
        """Guard: the startup check must see every route the app serves.

        FastAPI 0.142 stopped exposing included routes in ``app.routes``; this
        compares the checked routes with the OpenAPI operations instead.
        """
        app = create_app()
        served = {
            (method.upper(), path)
            for path, operations in app.openapi()["paths"].items()
            for method in operations
        }
        checked = {
            (method, path)
            for path, route in module_routes([PLATFORM, *MODULES], API_PREFIX)
            for method in route.methods or ()
        }

        assert served == checked

    def test_feature_module_routes_must_use_its_prefix(self) -> None:
        router = APIRouter(prefix="/elsewhere")

        @router.get("/x", dependencies=[Depends(public)])
        async def stray() -> None: ...

        with pytest.raises(ModuleRegistryError, match="must start with '/demo'"):
            Authorizer([demo_module(router)])

    def test_public_routes_are_exactly_the_expected_ones(self) -> None:
        """Making a route public must be a deliberate, reviewed change."""
        public_routes = {
            (method, path)
            for path, route in module_routes([PLATFORM, *MODULES], API_PREFIX)
            if route_access(route)[0].kind == "public"
            for method in route.methods or ()
        }

        assert public_routes == {
            ("GET", "/api/v1/health"),
            ("GET", "/api/v1/health/ready"),
            ("POST", "/api/v1/auth/login"),
            ("POST", "/api/v1/auth/logout"),
        }

    def test_platform_grants_follow_the_documented_matrix(self) -> None:
        authorizer = Authorizer([PLATFORM])

        assert authorizer.roles_with("platform.household.read") == list(Role)
        assert authorizer.roles_with("platform.household.manage") == [Role.OWNER]
        assert authorizer.roles_with("platform.audit.read") == [Role.OWNER]
