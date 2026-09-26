from typing import cast

from .fragment_registry import RegistryFragmentFactory
from .webapp import WebApp


class _WebAppProxy:
    # Registry-backed so module-import-time `@hx.fragment.get(...)` works
    # even before any WebApp is constructed. Resolved by normal attribute
    # lookup (not __getattr__), so it bypasses the WebApp proxy entirely.
    fragment: RegistryFragmentFactory = RegistryFragmentFactory()

    def __getattr__(self, name):
        return getattr(WebApp.get(), name)


hx: WebApp = cast(WebApp, _WebAppProxy())
