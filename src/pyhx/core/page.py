from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import Protocol

from fastapi import Response
from htpy import Node
from htpy.starlette import HtpyResponse
from starlette.background import BackgroundTask

from .primitives import IconName, Omit, PathTemplate, encode_query, omit
from .templates import PageTemplate


@dataclass
class PageResponse:
    """Extended response wrapper for HTMX-style page responses.

    Wraps an htpy ``Node`` with HTTP response metadata (status, headers,
    media type, background task). Render functions can return a plain
    ``Node`` and the framework wraps it in ``PageResponse`` automatically.

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

    # Allows to override the web apps default template. Omit -> No template will be applied.
    page_template: PageTemplate | Omit | None = None

    # Allows to override the page's title when rendering. Usually used by template to render HTML Page title.
    page_title: str | Omit | None = None

    @classmethod
    def redirect(cls, location: str) -> "PageResponse":
        """Plain HTTP 303 redirect from a top-level page handler.

        The response body is empty and the browser only reads the ``Location``
        header, so ``page_template=omit`` skips the WebApp's default template
        rather than wrapping nothing in the app skeleton.

        For a redirect from an htmx-driven fragment, use
        :meth:`~pyhx.core.FragmentResponse.redirect` instead: htmx's XHR follows
        a 3xx transparently and would swap the redirected page into the
        originating element.
        """
        return cls(
            node="",
            status_code=HTTPStatus.SEE_OTHER,
            headers={"location": location},
            page_template=omit,
        )

    def to_response(self) -> Response:
        return HtpyResponse(
            self.node,
            status_code=self.status_code.value,
            headers=self.headers,
            media_type=self.media_type,
            background=self.background,
        )


PageResult = PageResponse | Node


class Page(Protocol):
    path: PathTemplate
    title: str
    render: Callable[..., Awaitable[PageResult]]
    url: Callable[..., str]
    icon: IconName | None


class PageDefinition(Page):
    def __init__(
        self,
        path: PathTemplate,
        title: str,
        render: Callable[..., Awaitable[PageResult]],
        icon: IconName | None = None,
    ) -> None:
        self.title = title
        self.path = path
        self.render = render
        self.icon = icon

    def url(self, *, query: Mapping[str, object] | None = None, **kwargs) -> str:
        """Build a concrete URL for this page.

        Path variables are supplied as keyword arguments. The optional
        ``query`` mapping is encoded into a query string (see
        :func:`~pyhx.core.primitives.encode_query`). Because ``query`` is a
        reserved keyword-only parameter, a path template variable named
        ``query`` cannot be supplied through this method.
        """
        return str(self.path.format(**kwargs)) + encode_query(query or {})


class PageDecoratorFactory:
    """Capture-only decorator: builds a :class:`PageDefinition` from the
    raw user function and appends it to ``pages``. Template application
    happens at request time on the WebApp side (see
    :meth:`WebApp._handle_page_request`), so this factory has no WebApp
    dependency and can be reused by alternative collectors."""

    def __init__(self, pages: list[Page]) -> None:
        self._pages = pages

    def __call__(
        self, path: str, *, title: str, icon: IconName | None = None
    ) -> Callable[[Callable[..., Awaitable[PageResult]]], Page]:
        def __call__(fn: Callable[..., Awaitable[PageResult]]) -> Page:
            page = PageDefinition(PathTemplate(path), title, fn, icon=icon)
            self._pages.append(page)
            return page

        return __call__
