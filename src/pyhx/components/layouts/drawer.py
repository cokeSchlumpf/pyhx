from typing import Annotated, Any, Literal, overload

import htpy as y
from fastapi import Form

from pyhx.core import component
from pyhx.core.fragment import HTTPMethodLiteral
from pyhx.core.primitives import HtmxAttrs, classnames, htmx, merge_styles, styles

from ..primitives.button import button

DRAWER_CONTENT_ID = "drawer-content"

# A second drawer instance, stacked above the primary one (see the app shell and
# `.hx-drawer--popup` in drawer.css). Used by drawer-based pickers
# (`drawer_select` / `drawer_radio`) so they can open *on top of* a form that is
# itself rendered in the primary drawer, instead of replacing it.
POPUP_DRAWER_CONTENT_ID = "drawer-content-popup"


@component
def drawer(
    children: y.Node | None = None,
    *,
    id: str = DRAWER_CONTENT_ID,
    title: str | None = None,
    top: str = "0px",
    bottom: str = "0px",
    **kwargs,
) -> y.Node:
    return y.div(
        **classnames(
            "hx-drawer",
            **merge_styles(
                {"--hx--drawer--top": top, "--hx--drawer-bottom": bottom}, **kwargs
            ),
        )
    )[
        y.div(class_="hx-drawer__backdrop", aria_hidden="true"),
        drawer_content(children, id=id, title=title),
    ]


@component
def drawer_content(
    children: y.Node | None = None,
    *,
    id: str = DRAWER_CONTENT_ID,
    title: str | None = None,
    header_controls: y.Node | None = None,
    header_controls_position: Literal["left", "right"] = "left",
    close_url: str | None = None,
    **kwargs,
) -> y.Node:
    """The drawer's swappable panel: a header with a close button, plus content.

    Args:
        children: Panel body. Empty content closes the drawer.
        id: DOM id, and the target for out-of-band swaps.
        title: Heading text, also the accessible label.
        header_controls: Extra nodes beside the close button.
        header_controls_position: Which side of it they sit on.
        close_url: Where the close button posts; lets a consumer clear its
            own state too, which the generic close cannot.
    """
    close_attrs = (
        htmx(
            hx_post=close_url,
            hx_swap="none",
            hx_include="[data-hx-include='always']",
        )
        if close_url
        else htmx(
            hx_post=close.url(),
            hx_swap="none",
            hx_vals={"id": id},
        )
    )
    return y.aside(
        id=id,
        aria_label=title or "Details",
        hx_ext="morph",
        hx_swap_oob="morph",
        **kwargs,
    )[
        y.header[
            y.h3[title or ""],
            y.div(**styles("flex", "justify-end", "gap-sm", "items-center"))[
                header_controls
                if header_controls and header_controls_position == "left"
                else None,
                button(
                    icon="x",
                    aria_label="Close",
                    appearance="neutral",
                    variant="solid",
                    # pyhx.drawer.js clicks this when the backdrop is clicked.
                    data_hx_drawer_close=True,
                    **close_attrs,
                ),
                header_controls
                if header_controls and header_controls_position == "right"
                else None,
            ],
        ],
        y.section[children],
    ]


@overload
def open_drawer_htmx_attributes(
    url: str,
    id: str = DRAWER_CONTENT_ID,
    *,
    method: HTTPMethodLiteral = "GET",
    as_dict: Literal[True],
    kwargs: HtmxAttrs | None = None,
) -> dict[str, str]: ...


@overload
def open_drawer_htmx_attributes(
    url: str,
    id: str = DRAWER_CONTENT_ID,
    *,
    method: HTTPMethodLiteral = "GET",
    as_dict: Literal[False] = False,
    kwargs: HtmxAttrs | None = None,
) -> HtmxAttrs: ...


def open_drawer_htmx_attributes(
    url: str,
    id: str = DRAWER_CONTENT_ID,
    *,
    method: HTTPMethodLiteral = "GET",
    as_dict: bool = False,
    kwargs: HtmxAttrs | None = None,
) -> HtmxAttrs | dict[str, str]:
    target = f"#{id}"
    method_attr = {
        "GET": "hx_get",
        "POST": "hx_post",
        "PUT": "hx_put",
        "PATCH": "hx_patch",
        "DELETE": "hx_delete",
    }[method]

    merged: dict[str, Any] = {
        method_attr: url,
        "hx_swap": "none",
        "hx_target": target,
    }
    if kwargs:
        merged.update(kwargs)

    if as_dict:
        return htmx(as_dict=True, **merged)

    return htmx(as_dict=False, **merged)


@drawer.fragments.post("/close")
async def close(id: Annotated[str, Form()]) -> y.Node:
    return drawer_content(id=id)
