from collections.abc import Awaitable, Callable, Mapping
from http import HTTPMethod
from typing import Protocol

from fastapi import Response

from .primitives import PathTemplate, encode_query


class ApiEndpoint(Protocol):
    """A custom API endpoint that returns a raw FastAPI ``Response``.

    Unlike :class:`~pyhx.core.fragment.Fragment` and
    :class:`~pyhx.core.page.Page`, the handler is responsible for the full
    ``Response`` (status, headers, body, media type) — the framework does not
    wrap an htpy ``Node``. The pyhx wrapper around ``render`` still seeds the
    per-request :class:`~pyhx.core.request_context.RequestContext`, so
    ``RequestContext.get()`` and the auth accessors work inside the handler.
    """

    path: PathTemplate
    method: HTTPMethod
    render: Callable[..., Awaitable[Response]]
    url: Callable[..., str]


class ApiEndpointDefinition(ApiEndpoint):
    def __init__(
        self,
        path: PathTemplate,
        method: HTTPMethod,
        render: Callable[..., Awaitable[Response]],
    ) -> None:
        self.path = path
        self.method = method
        self.render = render

    def url(self, *, query: Mapping[str, object] | None = None, **kwargs) -> str:
        """Build a concrete URL for this endpoint.

        Path variables are supplied as keyword arguments. The optional
        ``query`` mapping is encoded into a query string (see
        :func:`~pyhx.core.primitives.encode_query`). Because ``query`` is a
        reserved keyword-only parameter, a path template variable named
        ``query`` cannot be supplied through this method.
        """
        return str(self.path.format(**kwargs)) + encode_query(query or {})


class ApiFactory:
    """Capture-only decorator factory for ``@app.api`` endpoints.

    Mirrors :class:`~pyhx.core.fragment.FragmentFactory`, but stores the raw
    handler (no result wrapping): the handler returns a ``Response`` directly.
    Handlers must be ``async`` — the pyhx wrapper ``await``\\ s ``render``.
    """

    def __init__(self, endpoints: list[ApiEndpoint]) -> None:
        self._endpoints = endpoints

    def _create(
        self, path: str, method: HTTPMethod
    ) -> Callable[[Callable[..., Awaitable[Response]]], ApiEndpoint]:
        def __call__(fn: Callable[..., Awaitable[Response]]) -> ApiEndpoint:
            endpoint = ApiEndpointDefinition(PathTemplate(path), method, fn)
            self._endpoints.append(endpoint)
            return endpoint

        return __call__

    def delete(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[Response]]], ApiEndpoint]:
        return self._create(path, HTTPMethod.DELETE)

    def get(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[Response]]], ApiEndpoint]:
        return self._create(path, HTTPMethod.GET)

    def patch(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[Response]]], ApiEndpoint]:
        return self._create(path, HTTPMethod.PATCH)

    def post(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[Response]]], ApiEndpoint]:
        return self._create(path, HTTPMethod.POST)

    def put(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[Response]]], ApiEndpoint]:
        return self._create(path, HTTPMethod.PUT)
