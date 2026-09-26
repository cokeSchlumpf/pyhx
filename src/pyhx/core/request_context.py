from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, overload

from commons.users import AnonymousUser, User
from fastapi import Request
from starlette.websockets import WebSocket

from .app_context import AppContext


def _empty_app_context() -> AppContext:
    """Default-factory helper — fresh empty :class:`AppContext` per ``RequestContext``."""
    return AppContext({})


@dataclass
class RequestContext:
    request: Request | None = None
    websocket: WebSocket | None = None
    user: User = field(default_factory=AnonymousUser)
    app_context: AppContext = field(default_factory=_empty_app_context)

    @staticmethod
    def get() -> "RequestContext":
        return _current_request_context.get()

    @staticmethod
    def get_request() -> Request:
        ctx = RequestContext.get()
        req = ctx.request

        assert req is not None, (
            "Request can only be read during request procesing of HTTP Requests (fragments and pages), not in WebSocket calls."
        )
        return req

    # fmt: off
    @staticmethod
    @overload
    def get_from_context[T1](t1: type[T1], /) -> tuple[T1]: ...
    @staticmethod
    @overload
    def get_from_context[T1, T2](t1: type[T1], t2: type[T2], /) -> tuple[T1, T2]: ...
    @staticmethod
    @overload
    def get_from_context[T1, T2, T3](t1: type[T1], t2: type[T2], t3: type[T3], /) -> tuple[T1, T2, T3]: ...
    @staticmethod
    @overload
    def get_from_context[T1, T2, T3, T4](t1: type[T1], t2: type[T2], t3: type[T3], t4: type[T4], /) -> tuple[T1, T2, T3, T4]: ...
    @staticmethod
    @overload
    def get_from_context[T1, T2, T3, T4, T5](t1: type[T1], t2: type[T2], t3: type[T3], t4: type[T4], t5: type[T5], /) -> tuple[T1, T2, T3, T4, T5]: ...
    @staticmethod
    @overload
    def get_from_context(*types: type) -> tuple[Any, ...]: ...
    # fmt: on

    @staticmethod
    def get_from_context(*types: type) -> tuple[Any, ...]:
        """Resolve each requested type to a value from the current context.

        Reads the active :class:`RequestContext` via :meth:`get`, then resolves
        each requested type: ``Request``, ``WebSocket`` and ``User`` are served
        straight from the context; every other type is looked up in the
        app-level :class:`AppContext` (``AppContext.get(type)``).

        The returned tuple is statically typed per element for up to five
        arguments, e.g. ``get_from_context(User, DomainRegistry)`` is inferred
        as ``tuple[User, DomainRegistry]``.
        """
        ctx = RequestContext.get()
        return tuple(ctx._resolve_one(t) for t in types)

    @staticmethod
    async def get_from_request(
        parameter_name: str, form_field_name: str | None = None
    ) -> str:
        """Read a single value from the current HTTP request, path params first.

        Resolves a value in two steps against the active request (obtained via
        :meth:`get_from_context`):

        1. If ``parameter_name`` is present in ``request.path_params`` (e.g. a
           route like ``/projects/{parameter_name}``), that value is returned,
           coerced to ``str``.
        2. Otherwise the request body is parsed as form data and the field named
           ``form_field_name`` is returned.

        This is intended for request/form handling in HTTP flows (fragments and
        pages). It does not work for WebSocket calls, since it requires a
        ``Request`` in the context — see :meth:`get_request`.

        Args:
            parameter_name: Path-parameter name to look up first. Also used as
                the form-field name when ``form_field_name`` is not given.
            form_field_name: Form-field name to fall back to when the value is
                not a path parameter. Defaults to ``parameter_name``.

        Returns:
            The resolved value as a ``str``.

        Raises:
            KeyError: If neither the path parameter nor the form field yields a
                value.
            AssertionError: If the resolved form field is not a plain string
                (e.g. an uploaded file).
            AttributeError: If no ``Request`` is available in the current
                context (e.g. within a WebSocket flow), since ``None`` has no
                ``path_params``.
        """
        (request,) = RequestContext.get_from_context(Request)

        if parameter_name in request.path_params:
            return str(request.path_params[parameter_name])

        form_field_name = form_field_name or parameter_name

        form_data = await request.form()
        value = form_data.get(form_field_name)

        if value is None:
            raise KeyError(
                f"No data found in request ({parameter_name}, {form_field_name})"
            )

        assert isinstance(value, str)

        return value

    def _resolve_one(self, t: type) -> Any:
        if isinstance(t, type) and issubclass(t, Request):
            return self.request
        if isinstance(t, type) and issubclass(t, WebSocket):
            return self.websocket
        if t is User or isinstance(self.user, t):
            return self.user
        return self.app_context.get(t)


_current_request_context: ContextVar[RequestContext] = ContextVar(
    "pyhx.current_request_context"
)


def set_request_context(ctx: RequestContext) -> None:
    _current_request_context.set(ctx)


def build_from_request(
    request: Request,
    app_context: AppContext | None = None,
) -> RequestContext:
    """Build a ``RequestContext`` from a Starlette ``Request``.

    Reads conventionally placed values from ``request.state``:
    - ``request.state.user`` → ``ctx.user`` (defaults to ``AnonymousUser`` if unset)

    ``app_context`` is the WebApp's :class:`AppContext` — passed in by
    :class:`~pyhx.core.webapp.WebApp` at handler entry so request-side
    code can reach app-level state without going through
    ``WebApp.get()``. ``None`` falls back to an empty context, which
    keeps direct ``RequestContext`` construction (e.g. in tests)
    working.

    Any other per-request data the application needs from middleware should
    be read directly off the FastAPI-injected ``Request`` via ``request.state``.
    """
    return RequestContext(
        request=request,
        user=getattr(request.state, "user", AnonymousUser()),
        app_context=app_context if app_context is not None else _empty_app_context(),
    )


def build_from_websocket(
    websocket: WebSocket,
    app_context: AppContext | None = None,
) -> RequestContext:
    """Build a ``RequestContext`` from a Starlette ``WebSocket``.

    Mirrors :func:`build_from_request` for WS scopes: middleware seeds
    ``websocket.state.user`` (defaults to ``AnonymousUser`` if unset).
    ``app_context`` is threaded in the same way.
    """
    return RequestContext(
        websocket=websocket,
        user=getattr(websocket.state, "user", AnonymousUser()),
        app_context=app_context if app_context is not None else _empty_app_context(),
    )
