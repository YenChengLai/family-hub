"""The platform, described with the same contract as feature modules."""

from family_hub.platform import health
from family_hub.platform.authz.registry import Module, Permission
from family_hub.platform.households import router as households
from family_hub.platform.households.models import Role
from family_hub.platform.identity import router as identity

PLATFORM = Module(
    name="platform",
    routers=(health.router, identity.router, households.router),
    permissions=(
        Permission("platform.household.read", "See the household and its members"),
        Permission("platform.household.manage", "Rename the household, change its time zone"),
        Permission("platform.audit.read", "Read the household's audit log"),
    ),
    grants={
        Role.CHILD: frozenset({"platform.household.read"}),
        Role.OWNER: frozenset({"platform.household.manage", "platform.audit.read"}),
    },
)
