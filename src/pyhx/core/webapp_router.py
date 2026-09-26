"""Decorator-based route collector that is attached to a WebApp later.

Use a :class:`WebAppRouter` to declare pages, fragments, and websockets in
modules that should not import a live :class:`~pyhx.core.WebApp`
instance. The router exposes the same ``.page`` and ``.fragment``
decorator surfaces as the WebApp, captured against a local list, and is
attached via :meth:`WebApp.include_router`. Routers can also be merged
into one another via :meth:`WebAppRouter.include_router` for nested
sub-namespaces.

Each router can be included at most once. To use the same routes under a
different prefix, construct a fresh router.
"""

from typing import TYPE_CHECKING

from .api_endpoint import ApiEndpoint, ApiFactory
from .fragment import Fragment, FragmentFactory
from .page import Page, PageDecoratorFactory
from .primitives import PathTemplate

if TYPE_CHECKING:
    from .webapp import WebSocket


class WebAppRouter:
    def __init__(self) -> None:
        self._pages: list[Page] = []
        self._fragments: list[Fragment] = []
        self._api_endpoints: list[ApiEndpoint] = []
        self._websockets: list[WebSocket] = []
        self._included: bool = False

        self.page = PageDecoratorFactory(self._pages)
        self.fragment = FragmentFactory(self._fragments)
        self.api = ApiFactory(self._api_endpoints)

    def add_websocket(self, ws: "WebSocket") -> None:
        self._websockets.append(ws)

    def include_router(self, router: "WebAppRouter", *, prefix: str = "") -> None:
        """Merge another :class:`WebAppRouter`'s pages, fragments, and websockets
        into this one. ``prefix`` is prepended to every captured path.

        Prefixes compose across inclusion levels: a router included into
        this one under ``"/sub"`` and this router later included into a
        :class:`WebApp` under ``"/api"`` leaves every leaf path with the
        final ``"/api/sub/…"`` prefix. Each handle's ``.url()`` reflects
        the composed path after every inclusion step.

        A router can be included at most once; a second call raises
        :class:`RuntimeError`.
        """
        if router._included:
            raise RuntimeError(
                "WebAppRouter has already been included. Each router can "
                "be included at most once. To use the same routes under "
                "a different prefix, construct a fresh router."
            )

        prefix = self._normalize_router_prefix(prefix)

        for page in router._pages:
            if prefix:
                page.path = PathTemplate(prefix + str(page.path))
            self._pages.append(page)
        for fragment in router._fragments:
            if prefix:
                fragment.path = PathTemplate(prefix + str(fragment.path))
            self._fragments.append(fragment)
        for endpoint in router._api_endpoints:
            if prefix:
                endpoint.path = PathTemplate(prefix + str(endpoint.path))
            self._api_endpoints.append(endpoint)
        for ws in router._websockets:
            if prefix:
                ws.path = PathTemplate(prefix + str(ws.path))
            self._websockets.append(ws)

        router._included = True

    @staticmethod
    def _normalize_router_prefix(prefix: str) -> str:
        if prefix in ("", "/"):
            return ""
        if not prefix.startswith("/"):
            raise ValueError(
                f"WebAppRouter prefix must start with '/', got: {prefix!r}"
            )
        return prefix.rstrip("/")
