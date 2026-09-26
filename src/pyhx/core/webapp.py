import traceback
from collections.abc import Awaitable, Callable, Coroutine, Sequence
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Protocol, Self

import htpy as y
from commons.path_operators import get_project_root_dir
from fastapi import FastAPI, Request, Response
from fastapi import WebSocket as FastAPIWebSocket
from htpy.starlette import HtpyResponse

from ._dev_mode import is_dev_mode
from .api_endpoint import ApiEndpoint, ApiFactory
from .app_context import AppContext
from .fragment import Fragment, FragmentFactory
from .fragment_registry import get_fragment_registry
from .log import LOG
from .nav_item import nav_item
from .page import Page, PageDecoratorFactory, PageResponse
from .primitives import HandlerResponse, PathTemplate, omit
from .primitives import Path as UrlPath
from .reflection_operators import ensure_parameter_type_in_signature
from .request_context import (
    RequestContext,
    build_from_request,
    build_from_websocket,
    set_request_context,
)
from .static import MultiStaticFiles
from .templates import AppNavFn, NavFactory, PageTemplate, Skeleton
from .webapp_router import WebAppRouter

# Intermediate pseudo types ...
type WebSocketRequestContext = str
type WebSocketResponse = HtpyResponse


class WebSocket(Protocol):
    path: PathTemplate
    topic: UrlPath

    async def render(self, context: WebSocketRequestContext) -> WebSocketResponse: ...


ConfigureAppFn = Callable[[FastAPI], None]


class WebApp:
    @staticmethod
    def get() -> "WebApp":
        return _current_webapp.get()

    def __init__(
        self,
        *,
        title: str = "PyHX App",
        context: dict[str, Any] | None = None,
        fragments: Sequence[Fragment] | None = None,
        pages: Sequence[Page] | None = None,
        api_endpoints: Sequence[ApiEndpoint] | None = None,
        static_dirs: Sequence[Path] | None = None,
        websockets: Sequence[WebSocket] | None = None,
        default_page_template: PageTemplate | None = None,
        configure_fastapi_app: Sequence[ConfigureAppFn] | None = None,
        navigation: AppNavFn | None = None,
        is_dev: bool | None = None,
    ) -> None:
        self.title = title

        # Defensive copy: caller-supplied dict isn't aliased into our
        # storage, so the caller mutating it post-construction can't
        # secretly leak into the WebApp. AppContext holds the dict by
        # reference, so subsequent ``set_context`` writes are visible
        # through every existing AppContext view (including the ones
        # already threaded into in-flight RequestContexts).
        self._context: dict[str, Any] = dict(context or {})
        self.context: AppContext = AppContext(self._context)

        self.default_page_template = default_page_template or Skeleton()

        self._navigation = navigation or {}
        self._pages = list(pages or [])
        self._fragments = list(fragments or [])
        self._api_endpoints = list(api_endpoints or [])
        self._websockets = list(websockets or [])
        self._configure_fastapi_app = list(configure_fastapi_app or [])
        self._is_dev = is_dev if is_dev is not None else is_dev_mode()

        self.fragment = FragmentFactory(self._fragments)
        self.page = PageDecoratorFactory(self._pages)
        self.api = ApiFactory(self._api_endpoints)
        self.navigation = NavFactory(self._navigation)
        self.nav_item = nav_item

        self._static_dirs = static_dirs or [
            # The default static directory according to suggested best practices on PyHX project structure.
            get_project_root_dir() / "src" / "app" / "_02_webapp" / "static"
        ]

        self._unsubscribe_from_registry: Callable[[], None] | None = (
            get_fragment_registry().subscribe(
                self._on_global_fragment_registered, replay=True
            )
        )

        set_webapp(self)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @property
    def is_dev(self) -> bool:
        """Whether this WebApp is running in development mode.

        Resolved from the constructor's ``is_dev=`` argument; if that was
        omitted, falls back to :func:`pyhx.core._dev_mode.is_dev_mode`
        (env var ``PYHX_DEBUG`` then a ``sys.argv`` scan for ``dev`` /
        ``--reload``).
        """
        return self._is_dev

    @property
    def request_context(self) -> RequestContext:
        """Request context"""
        return RequestContext.get()

    def set_context(self, key: str, value: Any) -> None:
        """Set or replace an app-level context entry by key.

        Mutates the underlying dict in place, so every existing
        :class:`AppContext` view — including ones already threaded
        into in-flight :class:`RequestContext` instances — sees the
        new value on the next read.

        Typically called once during startup (e.g. to register an
        adapter built from the config) but safe to call later if a
        feature flag or hot-reload sequence demands it.
        """
        self._context[key] = value

    def close(self) -> None:
        """Detach this WebApp from the global FragmentRegistry. Idempotent."""
        if self._unsubscribe_from_registry is not None:
            self._unsubscribe_from_registry()
            self._unsubscribe_from_registry = None

    def configure_fast_api_app(self, fn: ConfigureAppFn) -> None:
        """Attach a configuration function which is executed on app initialization."""
        self._configure_fastapi_app.append(fn)

    def create_app(self, *, app: FastAPI | None = None) -> FastAPI:
        app = app or FastAPI(title="PyHX App")

        app.mount("/static", MultiStaticFiles(list(self._static_dirs)))
        self._register_pages(app)
        self._register_fragments(app)
        self._register_api_endpoints(app)
        self._register_websockets(app)

        for fn in self._configure_fastapi_app:
            fn(app)

        return app

    def include_router(self, router: WebAppRouter, *, prefix: str = "") -> None:
        """Attach a :class:`WebAppRouter`'s pages, fragments, and websockets
        to this WebApp. ``prefix`` is prepended to every captured path;
        each handle's ``.url()`` reflects the effective (prefixed) path
        after this call so ``nav_item(page)`` keeps working.

        A router can be included at most once; a second call raises
        :class:`RuntimeError`.
        """
        if router._included:
            raise RuntimeError(
                "WebAppRouter has already been included. Each router can "
                "be included at most once. To use the same routes under "
                "a different prefix, construct a fresh router."
            )

        prefix = WebAppRouter._normalize_router_prefix(prefix)

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

    def _handle_fragment_request(
        self, fragment: Fragment
    ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        return self._handle_request(fragment.render)

    def _handle_page_request(
        self, page: Page
    ) -> Callable[..., Coroutine[Any, Any, Response]]:
        async def _render(**kwargs) -> Response:
            try:
                set_webapp(self)
                set_request_context(
                    build_from_request(kwargs[request_param_name], self.context)
                )

                if request_param_added:
                    del kwargs[request_param_name]

                result = await page.render(**kwargs)

                if isinstance(result, PageResponse):
                    page_response = result
                else:
                    page_response = PageResponse(node=result)

                page_response = await self._render_page_template(
                    page.title, page_response
                )
                return page_response.to_response()
            except Exception as exc:
                # Let FastAPI's exception_handler dispatch handle exception
                # types the app has explicitly registered for (e.g. addon-
                # defined types like ``NotAuthenticated``). Anything else
                # falls through to the in-route debug page below.
                # ``RequestContext`` was set at the top of the try block, so
                # it's safe to read here even though kwargs may have already
                # had the request param deleted before page.render ran.
                if _has_app_exception_handler(RequestContext.get().request, exc):
                    raise
                # TODO mw: Default error page.
                # Log Error
                # TODO: Error handler must be different / configurable
                LOG.exception("Error handling request")
                stacktrace_str = traceback.format_exc()
                return HtpyResponse(
                    y.div[y.h1["Internal Server Error"], y.pre[stacktrace_str]],
                    status_code=500,
                )

        signature, request_param_name, request_param_added = (
            ensure_parameter_type_in_signature(page.render, Request, "request")
        )
        new_annotations = {
            request_param_name: Request,
            **page.render.__annotations__,
        }

        _render.__signature__ = signature  # type: ignore[attr-defined]
        _render.__annotations__ = new_annotations

        return _render

    def _handle_request(
        self, handler: Callable[..., Awaitable[HandlerResponse]]
    ) -> Callable[..., Coroutine[Any, Any, Response]]:
        async def _render(**kwargs) -> Response:
            try:
                set_webapp(self)
                set_request_context(
                    build_from_request(kwargs[request_param_name], self.context)
                )

                if request_param_added:
                    del kwargs[request_param_name]

                handler_response = await handler(**kwargs)
                return handler_response.to_response()
            except Exception as exc:
                # Let FastAPI's exception_handler dispatch handle exception
                # types the app has explicitly registered for (e.g. addon-
                # defined types like ``NotAuthenticated``). Anything else
                # falls through to the in-route debug page below.
                # ``RequestContext`` was set at the top of the try block, so
                # it's safe to read here even though kwargs may have already
                # had the request param deleted before page.render ran.
                if _has_app_exception_handler(RequestContext.get().request, exc):
                    raise
                # TODO mw: Default error page.
                # Log Error
                # TODO: Error handler must be different / configurable
                LOG.exception("Error handling request")
                stacktrace_str = traceback.format_exc()
                return HtpyResponse(
                    y.div[y.h1["Internal Server Error"], y.pre[stacktrace_str]],
                    status_code=500,
                )

        signature, request_param_name, request_param_added = (
            ensure_parameter_type_in_signature(handler, Request, "request")
        )
        new_annotations = {
            request_param_name: Request,
            **handler.__annotations__,
        }

        _render.__signature__ = signature  # type: ignore[attr-defined]
        _render.__annotations__ = new_annotations

        return _render

    def _handle_api_request(
        self, endpoint: ApiEndpoint
    ) -> Callable[..., Coroutine[Any, Any, Response]]:
        async def _render(**kwargs) -> Response:
            try:
                set_webapp(self)
                set_request_context(
                    build_from_request(kwargs[request_param_name], self.context)
                )

                if request_param_added:
                    del kwargs[request_param_name]

                # The handler returns a fully-formed FastAPI ``Response``;
                # unlike pages/fragments there is no ``Node`` to wrap.
                return await endpoint.render(**kwargs)
            except Exception as exc:
                # Mirror ``_handle_request``: defer to FastAPI's exception
                # dispatch for types the app registered a handler for (e.g.
                # ``NotAuthenticated`` from the auth addon); otherwise fall
                # through to the in-route debug page.
                if _has_app_exception_handler(RequestContext.get().request, exc):
                    raise
                LOG.exception("Error handling request")
                stacktrace_str = traceback.format_exc()
                return HtpyResponse(
                    y.div[y.h1["Internal Server Error"], y.pre[stacktrace_str]],
                    status_code=500,
                )

        signature, request_param_name, request_param_added = (
            ensure_parameter_type_in_signature(endpoint.render, Request, "request")
        )
        new_annotations = {
            request_param_name: Request,
            **endpoint.render.__annotations__,
        }

        _render.__signature__ = signature  # type: ignore[attr-defined]
        _render.__annotations__ = new_annotations

        return _render

    def _handle_websocket_request(
        self, websocket: WebSocket
    ) -> Callable[[FastAPIWebSocket], Coroutine[Any, Any, None]]:
        async def _handle_websocket_connection(ws: FastAPIWebSocket) -> None:
            set_webapp(self)
            set_request_context(build_from_websocket(ws, self.context))

            # TODO mw: Impelment ....
            await ws.accept()

        return _handle_websocket_connection

    def _on_global_fragment_registered(self, fragment: Fragment) -> None:
        """Listener attached to :class:`FragmentRegistry`.

        Mirrors :meth:`register_component`: if the fragment's (path, method)
        is already known to this WebApp, log a warning and skip; otherwise
        forward to :meth:`FragmentFactory.add`.
        """
        if self.fragment.exists(fragment.path, fragment.method):
            LOG.warning(
                "WebApp: fragment %s %s already registered; "
                "skipping duplicate from FragmentRegistry",
                fragment.method,
                fragment.path,
            )
            return
        self.fragment.add(str(fragment.path), fragment.method, fragment.render)

    def _register_fragments(self, app: FastAPI) -> None:
        """Regisers fragment routes on FastAPI app."""
        self._fragments.sort(key=lambda f: str(f.path))

        for fragment in self._fragments:
            LOG.info(f"Registering fragment [{fragment.method}] {fragment.path}")
            app.add_api_route(
                path=str(fragment.path),
                endpoint=self._handle_fragment_request(fragment),
                methods=[str(fragment.method)],
                include_in_schema=False,
                response_model=None,
            )

    def _register_api_endpoints(self, app: FastAPI) -> None:
        """Registers ``@app.api`` routes on the FastAPI app.

        Unlike fragments/pages, API endpoints are included in the OpenAPI
        schema (``include_in_schema`` left at its default ``True``) since they
        constitute the app's public HTTP API.
        """
        self._api_endpoints.sort(key=lambda e: str(e.path))

        for endpoint in self._api_endpoints:
            LOG.info(f"Registering api endpoint [{endpoint.method}] {endpoint.path}")
            app.add_api_route(
                path=str(endpoint.path),
                endpoint=self._handle_api_request(endpoint),
                methods=[str(endpoint.method)],
                response_model=None,
            )

    def _register_pages(self, app: FastAPI) -> None:
        """Registers page routes on FastAPI app."""

        for page in self._pages:
            app.add_api_route(
                path=str(page.path),
                endpoint=self._handle_page_request(page),
                methods=["GET"],
                include_in_schema=False,
                response_model=None,
            )

    def _register_websockets(self, app: FastAPI) -> None:
        """Registeres websocket endooints on FastAPI app."""

        for ws in self._websockets:
            app.add_api_websocket_route(
                path=str(ws.path), endpoint=self._handle_websocket_request(ws)
            )

    async def _render_page_template(
        self, page_title: str | None, page_response: PageResponse
    ) -> PageResponse:
        page_title = page_response.page_title or page_title
        page_template = page_response.page_template or self.default_page_template

        if page_title == omit:
            page_title = None

        if page_template != omit:
            page_response.node = await page_template(
                request=RequestContext.get(),
                app_title=self.title,
                page_title=page_title,
                body=page_response.node,
                navigation=self._navigation,
            )

        return page_response


def _has_app_exception_handler(request: Request | None, exc: BaseException) -> bool:
    """Whether the FastAPI app behind ``request`` has registered an
    ``exception_handler`` for ``type(exc)`` (or any of its bases).

    Used by ``_handle_page_request`` / ``_handle_request`` to decide
    whether to re-raise instead of swallowing into the debug page —
    re-raising lets FastAPI dispatch the registered handler.
    """
    if request is None:
        return False
    handlers = getattr(getattr(request, "app", None), "exception_handlers", None)
    if not handlers:
        return False
    return any(isinstance(exc, cls) for cls in handlers if isinstance(cls, type))


_current_webapp: ContextVar[WebApp] = ContextVar("pyhx.current_webapp")


def set_webapp(app: WebApp) -> None:
    _current_webapp.set(app)
