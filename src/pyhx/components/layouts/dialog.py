"""Modal dialogs, opened and closed by the server like drawers.

A page has one dialog mount (``dialog``), rendered by the page templates. A
response that contains ``dialog_content(...)`` with children opens the dialog
(out-of-band swap by id); an empty ``dialog_content()`` closes it. The dialog
stays below the drawers, so a drawer opened from a control in the dialog
appears above it; ``pyhx.dialog.js`` makes the rest of the page inert.
"""

from typing import Annotated, Any, Literal, overload

import htpy as y
from fastapi import Form

from pyhx.core import component
from pyhx.core.fragment import HTTPMethodLiteral
from pyhx.core.primitives import HtmxAttrs, htmx
from pyhx.i18n import _p

from ..primitives.button import button

DIALOG_CONTENT_ID = "dialog-content"


@component
def dialog(content: y.Node | None = None, *, id: str = DIALOG_CONTENT_ID) -> y.Node:
    """The dialog's mount: backdrop and dialog. Render once per page.

    The page templates of pyhx render it after the drawers; a custom template
    renders it once at the end of ``<body>``.

    Args:
        content: A ``dialog_content(...)`` the page is delivered with (open);
            ``None`` renders the mount with an empty, closed dialog.
        id: DOM id of the empty dialog, the target of out-of-band swaps.
    """
    return y.div(class_="hx-dialog")[
        y.div(class_="hx-dialog__backdrop", aria_hidden="true"),
        content if content is not None else dialog_content(id=id),
    ]


@component
def dialog_content(
    *children: y.Node,
    title: str | None = None,
    actions: y.Node | None = None,
    closable: bool = True,
    close_url: str | None = None,
    id: str = DIALOG_CONTENT_ID,
    **kwargs: Any,
) -> y.Node:
    """The swappable dialog: title, content and actions in one form.

    Returned from a fragment route it opens the dialog, or changes the open
    one; without children it closes the dialog.

    Args:
        children: The content, one node or several. Without any (or only
            ``None``) the dialog is closed.
        title: The heading, which also labels the dialog.
        actions: Buttons in the footer, in order. Each posts to a fragment
            route (``hx_post``); the values of the controls in the dialog and
            the clicked button's ``name``/``value`` are sent with it.
        closable: ``True`` shows a close button, which Escape also triggers;
            ``False`` makes the dialog required: only an action closes it.
        close_url: Where the close button posts instead of ``close_dialog``,
            so the app can clean up its own state too.
        id: DOM id, the target of out-of-band swaps.
    """
    is_open = any(child is not None for child in children)
    title_id = f"{id}__title"
    if is_open and closable:
        close_attrs = (
            htmx(hx_post=close_url, hx_swap="none")
            if close_url
            else htmx(hx_post=close_dialog.url(), hx_swap="none", hx_vals={"id": id})
        )
        close_button: y.Node = button(
            icon="x",
            # Translators: accessible name of the close button of a dialog.
            aria_label=_p("dialog", "Close"),
            appearance="neutral",
            variant="solid",
            # Not a submit button: Enter in a field must not close the dialog.
            type="button",
            # pyhx.dialog.js clicks this on Escape.
            data_hx_dialog_close=True,
            **close_attrs,
        )
    else:
        close_button = None

    return y.dialog(
        id=id,
        open=is_open,
        aria_modal="true" if is_open else None,
        aria_labelledby=title_id if is_open else None,
        # Focused on open when nothing in it has `autofocus` (pyhx.dialog.js).
        tabindex="-1",
        hx_ext="morph",
        hx_swap_oob="morph",
        **kwargs,
    )[
        y.form(class_="hx-dialog__form", hx_swap="none")[
            y.header[y.h2(id=title_id)[title or ""], close_button],
            y.section[children],
            y.footer[actions],
        ]
        if is_open
        else None
    ]


@overload
def open_dialog_htmx_attributes(
    url: str,
    *,
    method: HTTPMethodLiteral = "GET",
    as_dict: Literal[True],
    kwargs: HtmxAttrs | None = None,
) -> dict[str, str]: ...


@overload
def open_dialog_htmx_attributes(
    url: str,
    *,
    method: HTTPMethodLiteral = "GET",
    as_dict: Literal[False] = False,
    kwargs: HtmxAttrs | None = None,
) -> HtmxAttrs: ...


def open_dialog_htmx_attributes(
    url: str,
    *,
    method: HTTPMethodLiteral = "GET",
    as_dict: bool = False,
    kwargs: HtmxAttrs | None = None,
) -> HtmxAttrs | dict[str, str]:
    """htmx attributes for an element that loads a dialog from ``url``.

    The route returns ``dialog_content(...)``, which is swapped in out of band.
    """
    method_attr = {
        "GET": "hx_get",
        "POST": "hx_post",
        "PUT": "hx_put",
        "PATCH": "hx_patch",
        "DELETE": "hx_delete",
    }[method]

    merged: dict[str, Any] = {method_attr: url, "hx_swap": "none"}
    if kwargs:
        merged.update(kwargs)

    if as_dict:
        return htmx(as_dict=True, **merged)

    return htmx(as_dict=False, **merged)


# Fragment paths come from the handler's name, and a second handler with the
# same name is skipped: hence `close_dialog`, not `close` (the drawer's).
@dialog.fragments.post("/close")
async def close_dialog(id: Annotated[str, Form()] = DIALOG_CONTENT_ID) -> y.Node:
    return dialog_content(id=id)
