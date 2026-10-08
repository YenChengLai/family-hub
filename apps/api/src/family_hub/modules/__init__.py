"""Feature modules. Each module is a package exposing one ``Module`` descriptor.

To add a module, create its package and append its descriptor to ``MODULES``.
The list is explicit on purpose: what runs is visible in one place.
"""

from family_hub.platform.authz.registry import Module

MODULES: list[Module] = []
