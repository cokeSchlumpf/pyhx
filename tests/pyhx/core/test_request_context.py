from dataclasses import dataclass

import htpy as y
from commons.users import AnonymousUser, AuthenticatedUser
from fastapi.testclient import TestClient
from starlette.types import ASGIApp, Receive, Scope, Send

from pyhx.core.request_context import RequestContext
from pyhx.core.webapp import WebApp


@dataclass
class _Captured:
    """Mutable holder used to surface ``RequestContext.get()`` out of
    fragment handlers so tests can assert against it afterward."""

    ctx: RequestContext | None = None


class _SetUserMiddleware:
    """Pure ASGI middleware that sets ``request.state.user`` (HTTP) or
    ``websocket.state.user`` (WS).

    This is the convention PyHX expects auth middleware to follow:
    set a ``User`` on the scope's ``state`` and core will surface it on
    ``RequestContext.user`` when building the per-request context.
    """

    def __init__(self, app: ASGIApp, *, user: AuthenticatedUser) -> None:
        self.app = app
        self.user = user

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            scope.setdefault("state", {})
            scope["state"]["user"] = self.user
        await self.app(scope, receive, send)


def _build_app(captured: _Captured) -> WebApp:
    """Build a WebApp with a single ``/probe`` fragment that records the
    current ``RequestContext`` for inspection."""

    hx = WebApp()

    @hx.fragment.get("/probe")
    async def probe() -> y.Node:
        captured.ctx = RequestContext.get()
        return y.div["ok"]

    return hx


class TestRequestContextFromHandler:
    def test_handler_sees_request_and_anonymous_user_without_middleware(self):
        captured = _Captured()
        hx = _build_app(captured)

        client = TestClient(hx.create_app())
        response = client.get("/probe")

        assert response.status_code == 200
        ctx = captured.ctx
        assert ctx is not None
        assert ctx.request is not None
        assert ctx.request.url.path == "/probe"
        assert ctx.websocket is None
        assert isinstance(ctx.user, AnonymousUser)

    def test_user_set_on_request_state_surfaces_on_ctx(self):
        """Convention: any FastAPI middleware can put a ``User`` on
        ``request.state.user``; core's per-request context builder picks
        it up. This proves the contract that user-land auth middleware
        relies on."""
        captured = _Captured()
        user = AuthenticatedUser.create("Jane Doe")
        hx = _build_app(captured)

        app = hx.create_app()
        app.add_middleware(_SetUserMiddleware, user=user)
        client = TestClient(app)

        response = client.get("/probe")

        assert response.status_code == 200
        assert captured.ctx is not None
        assert captured.ctx.user is user

    def test_request_state_user_overrides_default_anonymous(self):
        """A different ``User`` instance on each request produces a
        different ``ctx.user`` — proves the per-request lookup is not
        cached or shared across requests."""
        captured = _Captured()
        user_a = AuthenticatedUser.create("Alice")
        hx = _build_app(captured)

        app = hx.create_app()
        app.add_middleware(_SetUserMiddleware, user=user_a)
        client = TestClient(app)

        client.get("/probe")
        assert captured.ctx is not None and captured.ctx.user is user_a
