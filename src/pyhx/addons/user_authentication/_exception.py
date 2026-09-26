"""``NotAuthenticated`` plus the handler that converts it into a login
redirect.

The two redirect shapes themselves (303 + ``Location`` for plain
requests, 200 + ``HX-Redirect`` for HTMX) live on the response types
that encode them — :meth:`PageResponse.redirect` and
:meth:`FragmentResponse.redirect`.
"""

from collections.abc import Awaitable, Callable
from urllib.parse import urlencode

from fastapi import Request, Response

from pyhx.core import FragmentResponse, PageResponse


class NotAuthenticated(Exception):
    """Raised by handlers or dependencies to signal that the current
    request needs an authenticated user.

    Caught by the addon's exception handler (registered when
    :func:`configure_user_authentication` is called with the default
    ``include_exception_handler=True``) and converted into a redirect to
    ``login_path`` with ``?next=`` preserving the original URL.

    Apps with their own login UI may still raise this — but only if
    they pass the correct ``login_path`` to
    :func:`configure_user_authentication`. The handler doesn't know
    where the login page actually lives; it redirects to whatever path
    it was configured with.
    """


def make_not_authenticated_handler(
    login_path: str,
) -> Callable[[Request, Exception], Awaitable[Response]]:
    """Build a FastAPI exception handler that converts
    :class:`NotAuthenticated` into a redirect to ``login_path``."""

    async def handle(request: Request, _exc: Exception) -> Response:
        current = request.url.path
        if request.url.query:
            current = f"{current}?{request.url.query}"

        # Loop guard: if a handler at the login page itself raises
        # ``NotAuthenticated`` for some reason, don't pass next=/login
        # because that would re-trigger the redirect on the next request.
        params = urlencode({"next": current}) if request.url.path != login_path else ""
        location = f"{login_path}?{params}" if params else login_path

        # HTMX's XHR follows 3xx transparently and only sees the redirected
        # page's body — so a 303 from an hx-post would have HTMX swap the
        # login page into the original form's wrapper. ``HX-Redirect`` on a
        # 200 makes HTMX do ``window.location`` instead. Plain (non-HTMX)
        # requests need a real 3xx + ``Location`` since browsers ignore
        # ``Location`` on 2xx responses.
        if request.headers.get("HX-Request") == "true":
            return FragmentResponse.redirect(location).to_response()
        return PageResponse.redirect(location).to_response()

    return handle
