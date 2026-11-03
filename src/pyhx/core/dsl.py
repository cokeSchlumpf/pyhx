from typing import cast

from .fragment_registry import RegistryFragmentFactory, get_fragment_registry
from .stream import StreamFactory
from .webapp import WebApp


class _WebAppProxy:
    # Registry-backed so module-import-time `@hx.fragment.get(...)` and
    # `@hx.stream.get(...)` work even before any WebApp is constructed. Resolved by normal attribute
    # lookup (not __getattr__), so it bypasses the WebApp proxy entirely.
    fragment: RegistryFragmentFactory = RegistryFragmentFactory()
    stream: StreamFactory = StreamFactory(get_fragment_registry().register)

    def __getattr__(self, name):
        return getattr(WebApp.get(), name)


hx: WebApp = cast(WebApp, _WebAppProxy())
