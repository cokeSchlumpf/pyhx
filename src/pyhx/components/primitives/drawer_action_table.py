"""Drawer-based action picker: pick one item from a list to trigger a caller's action.

``drawer_action_table`` opens a popup drawer listing candidate items in the same shape as ``drawer_radio`` (a flat, single-column list)

Compare d to ``drawer_radio``, this component owns no commit/select endpoint of its own: clicking a row posts straight to a ``commit_url`` the caller supplies
The caller's commit endpoint is responsible for closing this drawer and refreshing whatever it needs to, the same way ``drawer_radio.select_item`` does both in one response.
"""

from collections.abc import Sequence
from typing import Annotated

import htpy as y
from fastapi import Form, Request
from pydantic import BaseModel

import pyhx.components as c
from pyhx.core import component
from pyhx.core.primitives import htmx

CONFIG_JSON_FIELD = "drawer_action_table_config_json"
AVAILABLE_ITEMS_ID = "hx-drawer-action-table__available-items"


class DrawerActionItem(BaseModel):
    """One candidate row: a stable ``id`` and its display ``label``. ``label`` is matched against the filter query as a plain case-insensitive substring."""

    id: str
    label: str


class DrawerActionTableConfig(BaseModel):
    """State of a ``drawer_action_table``, serialized into a hidden input.

    Round-trips across the filter interaction (open -> type -> re-render), a row click posts straight to
    ``commit_url`` rather than being staged in this component's own state.
    """

    items: tuple[DrawerActionItem, ...]
    query: str = ""
    commit_url: str
    commit_hx_include: str | None = None
    cancel_url: str | None = None
    cancel_hx_include: str | None = None
    title: str = "Select item"

    def visible_items(self) -> tuple[DrawerActionItem, ...]:
        """Items whose label matches ``query`` (case-insensitive substring)."""
        q = self.query.lower()
        if not q:
            return self.items
        return tuple(item for item in self.items if q in item.label.lower())


@component
def drawer_action_table_endpoints() -> y.Node:
    """Mount point for the drawer-action-table htmx fragment routes.

    Renders nothing visible; including this component in an app registers the
    fragment endpoints below so the drawer's filter and cancel interactions
    resolve.
    """
    return y.fragment[""]


def _available_items(config: DrawerActionTableConfig, *, oob: bool = False) -> y.Node:
    """Render the (possibly filtered) row list as a flat, single-column table."""
    visible = config.visible_items()
    rows = [
        y.tr(
            **htmx(
                hx_post=config.commit_url,
                hx_trigger="click",
                hx_swap="none",
                hx_vals={"value": item.id},
                hx_include=config.commit_hx_include,
            )
        )[
            # `title` surfaces the full label as a native hover tooltip when
            # the CSS ellipsis (`.hx-drawer-action-table__available-items td`)
            # truncates it.
            y.td(class_="hx-drawer-action-table__label", title=item.label)[item.label]
        ]
        for item in visible
    ]
    return y.div(
        id=AVAILABLE_ITEMS_ID,
        class_=AVAILABLE_ITEMS_ID,
        **(htmx(hx_swap_oob="outerHTML", as_dict=True) if oob else {}),
    )[
        y.table[
            y.thead[y.tr[y.th["Available items"]]],
            y.tbody[
                *rows,
                (
                    y.tr[
                        y.td(class_="hx-drawer-action-table__empty")[
                            "No available items."
                        ]
                    ]
                    if not rows
                    else None
                ),
            ],
        ]
    ]


def _config_input(config: DrawerActionTableConfig, *, oob: bool = False) -> y.Node:
    return y.input(
        type="hidden",
        id=CONFIG_JSON_FIELD,
        name=CONFIG_JSON_FIELD,
        value=config.model_dump_json(),
        **(htmx(hx_swap_oob="outerHTML", as_dict=True) if oob else {}),
    )


def drawer_action_table(
    items: Sequence[DrawerActionItem],
    *,
    commit_url: str,
    commit_hx_include: str | None = None,
    cancel_url: str | None = None,
    cancel_hx_include: str | None = None,
    title: str = "Select item",
) -> y.Node:
    """Render popup-drawer content: a filterable flat list of items to pick one from.

    Parameters
    ----------
    items:
        Candidate rows, already narrowed to whatever pool the caller considers
        selectable
    commit_url:
        URL a row's click posts to, with the row's id attached under
        ``"value"`` via ``hx_vals``. typically a fragment route that
        performs the action and returns both an empty
        ``c.drawer_content(id=c.POPUP_DRAWER_CONTENT_ID)`` (to close this
        drawer) and an out-of-band refresh of whatever the action changed.
    commit_hx_include:
        Optional htmx ``hx-include`` selector forwarded onto every row's click,
        for callers whose commit endpoint needs form fields living outside this
        drawer (e.g. a page-state hidden input marked ``data-hx-include="always"`` elsewhere on the page).
    cancel_url:
        Optional override for the Cancel button's target, for callers that
        need to undo something when the drawer closes without a pick (e.g.
        clearing a visual anchor set when it opened). Posted to (not a plain
        GET) so ``cancel_hx_include`` can ride along. Defaults to this
        component's own no-op close.
    cancel_hx_include:
        Optional htmx ``hx-include`` selector forwarded onto the Cancel click,
        mirroring ``commit_hx_include``. Only meaningful with ``cancel_url``.
    title:
        The drawer's header title.
    """
    config = DrawerActionTableConfig(
        items=tuple(items),
        commit_url=commit_url,
        commit_hx_include=commit_hx_include,
        cancel_url=cancel_url,
        cancel_hx_include=cancel_hx_include,
        title=title,
    )
    cancel_attrs = (
        htmx(
            hx_post=config.cancel_url,
            hx_swap="none",
            hx_include=config.cancel_hx_include,
        )
        if config.cancel_url is not None
        else htmx(hx_get=close_drawer.url(), hx_swap="none")
    )
    return c.drawer_content(
        y.div(class_="hx-drawer-action-table")[
            y.div(
                class_="hx-drawer-action-table__search",
                hx_post=query_items.url(),
                hx_trigger="input delay:200ms",
                hx_target=f"#{AVAILABLE_ITEMS_ID}",
                hx_swap="none",
                hx_include="this",
                as_dict=True,
            )[
                _config_input(config),
                c.form_field("query", "Filter items", y.input()),
            ],
            _available_items(config),
            y.div(class_="hx-drawer-action-table__actions")[
                c.button("Cancel", **cancel_attrs),
            ],
        ],
        id=c.POPUP_DRAWER_CONTENT_ID,
        title=config.title,
    )


@drawer_action_table_endpoints.fragments.post("/drawer-action-table/query")
async def query_items(
    request: Request, query: Annotated[str | None, Form()] = None
) -> y.Node:
    """Re-filter the item list as the user types, OOB-swapping the list and the
    serialized state."""
    form = await request.form()
    config = DrawerActionTableConfig.model_validate_json(str(form[CONFIG_JSON_FIELD]))
    config.query = query or ""
    return y.fragment[
        _available_items(config, oob=True),
        _config_input(config, oob=True),
    ]


@drawer_action_table_endpoints.fragments.get("/drawer-action-table/close-drawer")
async def close_drawer() -> y.Node:
    """Close the drawer without picking anything."""
    return c.drawer_content(id=c.POPUP_DRAWER_CONTENT_ID)
