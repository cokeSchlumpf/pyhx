import functools
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from http import HTTPMethod, HTTPStatus
from typing import Literal, Protocol

from fastapi import Response
from htpy import Node
from htpy.starlette import HtpyResponse
from starlette.background import BackgroundTask

from .primitives import Path, PathTemplate, encode_query

HTTPMethodLiteral = Literal["DELETE", "GET", "PATCH", "POST", "PUT"]


@dataclass(frozen=True)
class FragmentResponse:
    """Extended response wrapper for HTMX-style page responses.

    Wraps an htpy ``Node`` with HTTP response metadata (status, headers,
    media type, background task). Render functions can return a plain
    ``Node`` and the framework wraps it in ``FragmentResponse`` automatically.

    Attributes
    ----------
    node : Node
        The htpy node tree to render as the response body.
    status_code : HTTPStatus
        HTTP status code. Defaults to ``200 OK``.
    headers : dict of str to str, optional
        Extra response headers. ``None`` means no additional headers.
    media_type : str, optional
        ``Content-Type`` value. Defaults to ``"text/html"``.
    background : BackgroundTask, optional
        Starlette background task to run after the response is sent.
    """

    node: Node
    status_code: HTTPStatus = HTTPStatus.OK
    headers: dict[str, str] | None = None
    media_type: str | None = "text/html"
    background: BackgroundTask | None = None

    @classmethod
    def redirect(cls, location: str) -> "FragmentResponse":
        """Trigger a full-page browser navigation from an htmx-driven response.

        htmx intercepts the response and swaps the body into the element that
        issued the request, so a fragment can never *render* a different page.
        A plain ``303 + Location`` doesn't help either: htmx's XHR follows the
        redirect transparently and only sees the redirected page's HTML, which
        it then swaps into the originating element. The ``HX-Redirect`` header
        tells htmx to do ``window.location = location`` instead, which is a real
        browser navigation.

        The body is empty — htmx reads the header and navigates away, so nothing
        would be swapped in anyway.

        For a redirect from a plain (non-htmx) page handler, use
        :meth:`~pyhx.core.PageResponse.redirect`, which sends the ``303 +
        Location`` that browsers act on. Browsers ignore ``Location`` on a 2xx,
        so the two shapes are not interchangeable.
        """
        return cls(
            node="",
            status_code=HTTPStatus.OK,
            headers={"HX-Redirect": location},
        )

    def to_response(self) -> Response:
        return HtpyResponse(
            self.node,
            status_code=self.status_code.value,
            headers=self.headers,
            media_type=self.media_type,
            background=self.background,
        )


FragmentResult = Node | FragmentResponse


def resolve_fragment_result(
    fn: Callable[..., Awaitable[FragmentResult]],
) -> Callable[..., Awaitable[FragmentResponse]]:
    # @functools.wraps copies __wrapped__ onto the inner function so
    # introspection tools (FastAPI's route-parameter analysis among them)
    # can recover the original signature. Without this, FastAPI sees only
    # ``(**kwargs)`` and treats ``kwargs`` as a single query parameter.
    @functools.wraps(fn)
    async def __call__(**kwargs) -> FragmentResponse:
        result = await fn(**kwargs)

        if isinstance(result, FragmentResponse):
            return result
        else:
            return FragmentResponse(node=result)

    return __call__


class Fragment(Protocol):
    path: PathTemplate
    method: HTTPMethod
    render: Callable[..., Awaitable[FragmentResponse]]
    url: Callable[..., str]


class FragmentDefinition(Fragment):
    def __init__(
        self,
        path: PathTemplate,
        method: HTTPMethod,
        render: Callable[..., Awaitable[FragmentResponse]],
    ) -> None:
        self.path = path
        self.method = method
        self.render = render

    def url(self, *, query: Mapping[str, object] | None = None, **kwargs) -> str:
        """Build a concrete URL for this fragment.

        Path variables are supplied as keyword arguments. The optional
        ``query`` mapping is encoded into a query string (see
        :func:`~pyhx.core.primitives.encode_query`). Because ``query`` is a
        reserved keyword-only parameter, a path template variable named
        ``query`` cannot be supplied through this method.
        """
        return str(self.path.format(**kwargs)) + encode_query(query or {})


class FragmentFactory:
    def __init__(self, fragments: list[Fragment]) -> None:
        self._fragments = fragments

    def _create(
        self, path: str, method: HTTPMethod
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        def __call__(fn: Callable[..., Awaitable[FragmentResult]]) -> Fragment:
            fragment = FragmentDefinition(
                PathTemplate(path), method, resolve_fragment_result(fn)
            )
            self._fragments.append(fragment)
            return fragment

        return __call__

    def delete(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._create(path, HTTPMethod.DELETE)

    def get(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._create(path, HTTPMethod.GET)

    def patch(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._create(path, HTTPMethod.PATCH)

    def post(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._create(path, HTTPMethod.POST)

    def put(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[FragmentResult]]], Fragment]:
        return self._create(path, HTTPMethod.PUT)

    def add(
        self,
        path: str,
        method: HTTPMethod | HTTPMethodLiteral,
        fn: Callable[..., Awaitable[FragmentResult]],
    ) -> Fragment:
        if method == "DELETE":
            method = HTTPMethod.DELETE
        elif method == "GET":
            method = HTTPMethod.GET
        elif method == "PATCH":
            method = HTTPMethod.PATCH
        elif method == "POST":
            method = HTTPMethod.POST
        elif method == "PUT":
            method = HTTPMethod.PUT
        elif isinstance(method, str):
            raise ValueError(f"Unknown method type `{method}`")

        return self._create(path, method)(fn)

    def exists(
        self, path: str | PathTemplate | Path, method: HTTPMethod | HTTPMethodLiteral
    ) -> bool:
        """Return True if a fragment is registered for ``path`` and ``method``.

        Comparison semantics by ``path`` type:

        - ``str``: wrapped as :class:`PathTemplate` (mirroring ``add()``),
          then matched by template equality (string form).
        - :class:`PathTemplate`: matched by template equality.
        - :class:`Path` (concrete): matched against each registered template
          via :meth:`PathTemplate.match`, so e.g. ``Path("/users/42")``
          matches a template ``/users/{id}``.

        ``method`` accepts both :class:`HTTPMethod` and its string literals
        (``"GET"`` etc.). Unknown string methods raise :class:`ValueError`.
        """
        if isinstance(method, str):
            method = HTTPMethod(method)

        if isinstance(path, Path):
            query_template, query_path = None, path
        elif isinstance(path, PathTemplate):
            query_template, query_path = path, None
        else:
            query_template, query_path = PathTemplate(path), None

        for fragment in self._fragments:
            if fragment.method != method:
                continue
            if query_template is not None and fragment.path == query_template:
                return True
            if (
                query_path is not None
                and fragment.path.match(str(query_path)) is not None
            ):
                return True

        return False
