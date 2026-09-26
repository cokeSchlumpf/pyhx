from dataclasses import dataclass
from http import HTTPMethod

from commons.users import AnonymousUser, AuthenticatedUser
from fastapi import Response
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.testclient import TestClient
from starlette.types import ASGIApp, Receive, Scope, Send

from pyhx.addons.user_authentication import require_authenticated_user
from pyhx.core import RequestContext, WebAppRouter
from pyhx.core.api_endpoint import ApiEndpointDefinition
from pyhx.core.primitives import PathTemplate
from pyhx.core.webapp import WebApp


async def _dummy_render() -> Response: ...


class TestApiEndpointUrl:
    def _make(self, path: str) -> ApiEndpointDefinition:
        return ApiEndpointDefinition(PathTemplate(path), HTTPMethod.GET, _dummy_render)

    def test_path_params_only(self):
        endpoint = self._make("/items/{item_id}")
        assert endpoint.url(item_id=42) == "/items/42"

    def test_path_params_and_query(self):
        endpoint = self._make("/items/{item_id}")
        assert endpoint.url(item_id=42, query={"q": "hello"}) == "/items/42?q=hello"

    def test_none_query_omits_question_mark(self):
        endpoint = self._make("/items")
        assert endpoint.url(query=None) == "/items"


@dataclass
class _Captured:
    """Mutable holder used to surface ``RequestContext.get()`` out of an
    ``@app.api`` handler so tests can assert against it afterward."""

    ctx: RequestContext | None = None


class _SetUserMiddleware:
    """Pure ASGI middleware that sets ``request.state.user`` (HTTP).

    Mirrors the convention PyHX expects auth middleware to follow (see
    ``test_request_context``): set a ``User`` on the scope's ``state`` and
    core surfaces it on ``RequestContext.user``.
    """

    def __init__(self, app: ASGIApp, *, user: AuthenticatedUser) -> None:
        self.app = app
        self.user = user

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            scope.setdefault("state", {})
            scope["state"]["user"] = self.user
        await self.app(scope, receive, send)


class TestApiEndpointRequestContext:
    def test_context_is_set_with_anonymous_user(self):
        captured = _Captured()
        hx = WebApp()

        @hx.api.get("/probe")
        async def probe() -> Response:
            captured.ctx = RequestContext.get()
            return JSONResponse({"ok": True})

        client = TestClient(hx.create_app())
        response = client.get("/probe")

        assert response.status_code == 200
        ctx = captured.ctx
        assert ctx is not None
        assert ctx.request is not None
        assert ctx.request.url.path == "/probe"
        assert isinstance(ctx.user, AnonymousUser)

    def test_user_surfaces_and_auth_accessor_works(self):
        captured = _Captured()
        user = AuthenticatedUser.create("Jane Doe")
        hx = WebApp()

        @hx.api.get("/me")
        async def me() -> Response:
            caller = require_authenticated_user()
            captured.ctx = RequestContext.get()
            return JSONResponse({"name": caller.display_name})

        app = hx.create_app()
        app.add_middleware(_SetUserMiddleware, user=user)
        client = TestClient(app)

        response = client.get("/me")

        assert response.status_code == 200
        assert captured.ctx is not None
        assert captured.ctx.user is user
        assert response.json() == {"name": user.display_name}


class TestApiEndpointResponse:
    def test_raw_response_passthrough(self):
        hx = WebApp()

        @hx.api.post("/echo")
        async def echo() -> Response:
            return JSONResponse({"created": True}, status_code=201)

        client = TestClient(hx.create_app())
        response = client.post("/echo")

        assert response.status_code == 201
        assert response.json() == {"created": True}

    def test_path_and_query_params_resolve(self):
        hx = WebApp()

        @hx.api.get("/items/{item_id}")
        async def get_item(item_id: str, q: str = "none") -> Response:
            return JSONResponse({"item_id": item_id, "q": q})

        client = TestClient(hx.create_app())
        response = client.get("/items/42", params={"q": "hello"})

        assert response.status_code == 200
        assert response.json() == {"item_id": "42", "q": "hello"}

    def test_all_methods_register_and_dispatch(self):
        hx = WebApp()

        @hx.api.get("/r")
        async def r_get() -> Response:
            return PlainTextResponse("GET")

        @hx.api.post("/r")
        async def r_post() -> Response:
            return PlainTextResponse("POST")

        @hx.api.put("/r")
        async def r_put() -> Response:
            return PlainTextResponse("PUT")

        @hx.api.patch("/r")
        async def r_patch() -> Response:
            return PlainTextResponse("PATCH")

        @hx.api.delete("/r")
        async def r_delete() -> Response:
            return PlainTextResponse("DELETE")

        client = TestClient(hx.create_app())

        assert client.get("/r").text == "GET"
        assert client.post("/r").text == "POST"
        assert client.put("/r").text == "PUT"
        assert client.patch("/r").text == "PATCH"
        assert client.delete("/r").text == "DELETE"


class TestApiEndpointExceptionDispatch:
    def test_registered_exception_handler_is_used(self):
        class _Boom(Exception):
            pass

        hx = WebApp()

        @hx.api.get("/boom")
        async def boom() -> Response:
            raise _Boom()

        app = hx.create_app()

        async def handle_boom(request, exc) -> Response:
            return JSONResponse({"handled": True}, status_code=418)

        app.add_exception_handler(_Boom, handle_boom)
        client = TestClient(app)

        response = client.get("/boom")

        # The handler-registered type is re-raised by the wrapper and
        # dispatched by FastAPI, not swallowed into the 500 debug page.
        assert response.status_code == 418
        assert response.json() == {"handled": True}


class TestApiEndpointRouter:
    def test_router_endpoints_compose_under_prefix(self):
        router = WebAppRouter()

        @router.api.get("/ping")
        async def ping() -> Response:
            return PlainTextResponse("pong")

        hx = WebApp()
        hx.include_router(router, prefix="/api")
        client = TestClient(hx.create_app())

        response = client.get("/api/ping")

        assert response.status_code == 200
        assert response.text == "pong"


class TestApiEndpointOpenApi:
    def test_route_is_included_in_openapi_schema(self):
        hx = WebApp()

        @hx.api.get("/api/widgets")
        async def widgets() -> Response:
            return JSONResponse([])

        app = hx.create_app()
        schema = app.openapi()

        assert "/api/widgets" in schema["paths"]
        assert "get" in schema["paths"]["/api/widgets"]
