"""Answers for errors the app doesn't handle, in the language of the request.

Pages get an error page in the app's page template, htmx requests (fragments,
API endpoints) a short plain text that the error toast of
``pyhx.notifications.js`` shows. Stack traces are added only in development;
they are always logged by the caller.
"""

import traceback
from collections.abc import Mapping
from http import HTTPStatus

import htpy as y
from fastapi import Request
from starlette.responses import PlainTextResponse


def error_texts(status: int) -> tuple[str, str]:
    """Title and text of an error page for an HTTP ``status``."""
    # Imported lazily: ``pyhx.i18n`` imports ``pyhx.core``.
    from pyhx.i18n import _

    if status == HTTPStatus.BAD_REQUEST:
        return _("Invalid request"), _(
            "The request couldn't be processed. Check your input and try again."
        )
    if status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
        return _("No access"), _("You don't have permission to see this page.")
    if status == HTTPStatus.NOT_FOUND:
        return _("Page not found"), _(
            "This page doesn't exist. Check the address or go to the start page."
        )
    if status == HTTPStatus.METHOD_NOT_ALLOWED:
        return _("Not possible"), _("This action isn't possible here.")
    return _("Something went wrong"), _(
        "The request couldn't be completed. Try again later."
    )


def is_htmx(request: Request) -> bool:
    return request.headers.get("hx-request") == "true"


def wants_html(request: Request) -> bool:
    return "text/html" in request.headers.get("accept", "")


def own_detail(status: int, detail: object) -> str | None:
    """The ``detail`` of an ``HTTPException`` if the app set it, else ``None`` (the status' phrase)."""
    if not isinstance(detail, str) or not detail:
        return None
    try:
        phrase = HTTPStatus(status).phrase
    except ValueError:
        phrase = ""
    return None if detail == phrase else detail


def error_page(
    status: int,
    *,
    text: str | None = None,
    exc: BaseException | None = None,
    is_dev: bool = False,
) -> y.Node:
    """The body of an error page: title, text, a link to the start page, and the trace in development."""
    from pyhx.i18n import _

    title, general = error_texts(status)
    return y.section(class_="hx-error-page")[
        y.h1[title],
        y.p[text or general],
        y.p[y.a(href="/")[_("Go to the start page")]],
        y.pre["".join(traceback.format_exception(exc))]
        if is_dev and exc is not None
        else None,
    ]


def error_text_response(
    status: int,
    *,
    text: str | None = None,
    exc: BaseException | None = None,
    is_dev: bool = False,
    headers: Mapping[str, str] | None = None,
) -> PlainTextResponse:
    """A short plain text for an htmx request; the error toast shows it."""
    _title, general = error_texts(status)
    body = text or general
    if is_dev and exc is not None:
        body += "\n\n" + "".join(traceback.format_exception(exc))
    return PlainTextResponse(body, status_code=status, headers=headers)
