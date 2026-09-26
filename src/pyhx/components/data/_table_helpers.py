"""Shared rendering bits for :class:`DataTable` and :class:`HierarchicalDataTable`.

Both tables share the wrapper div, the hidden state input, the toolbar,
the header row, the CSS grid track string, and the row-selection model
(``select_mode`` + ``is_selected``). They differ in body rendering (flat
list vs. recursive tree with expand) and in the extra state the
hierarchical variant carries (``is_expanded``).
"""

import inspect
from collections.abc import Awaitable, Callable
from inspect import Parameter
from typing import Literal, cast

import htpy as y
from pydantic import BaseModel, Field

from pyhx.core import RequestContext
from pyhx.core.primitives import htmx
from pyhx.core.primitives.resolve_value import SyncOrAsyncFn

from ..primitives import button, table
from ..primitives.table import SortDirection
from ..view_model.columns import Fixed, Flex
from .column import Column
from .filter_drawer import FilterDrawer
from .sources.query import Query

TOGGLE_FULLSCREEN_ACTION = "toggle_fullscreen"
"""``action`` form value posted by the toolbar's maximize button.

Both table handlers read ``action`` from the form and flip
``state.fullscreen`` when they see this value. The button posts via
``hx_vals`` against the same fragment URL that re-renders the table, so
no extra endpoint is needed.
"""


TOGGLE_SELECT_ACTION = "toggle_select"
"""``action`` form value posted when the user clicks a selectable row.

Both table handlers route this through :func:`apply_select_toggle` to
mutate ``state.is_selected``. The same value travels via ``hx_vals``
alongside the row's ``item_id``.
"""


EXPAND_ALL_ACTION = "expand_all"
"""``action`` form value posted by the hierarchical table's expand-all button.

The handler walks the source recursively to discover every expandable
node id and writes the full set into ``state.is_expanded``.
"""


COLLAPSE_ALL_ACTION = "collapse_all"
"""``action`` form value posted by the hierarchical table's collapse-all button.

The handler simply clears ``state.is_expanded`` — no source walk needed.
"""


SelectMode = Literal["none", "single", "multi", "single-leafs", "multi-leafs"]
"""Row-selection model shared by both tables.

The flat :class:`~pyhx.components.data.data_table.DataTable` only accepts
``"none" | "single" | "multi"`` — leaf-restricted modes are meaningless
without a tree. The hierarchical variant accepts the full union.
"""


class TableState(BaseModel):
    """Round-trippable UI state for a data table.

    Serialized into a single hidden ``<input>`` next to the table and
    re-validated on every fragment request. Both the flat and the
    hierarchical table share this base; ``is_selected`` is part of the
    base because both tables support selection. The hierarchical variant
    subclasses it to add ``is_expanded``.
    """

    query: Query
    fullscreen: bool = False
    column_widths: str | None = None
    is_selected: list[str] = Field(default_factory=list)


def is_multi_select(mode: SelectMode) -> bool:
    """True for modes that allow more than one row selected at a time."""
    return mode in ("multi", "multi-leafs")


def is_leafs_only_select(mode: SelectMode) -> bool:
    """True for modes that restrict selection to leaf rows."""
    return mode in ("single-leafs", "multi-leafs")


def normalize_selection(mode: SelectMode, is_selected: list[str]) -> list[str]:
    """Truncate single-select modes to one id.

    Non-selectable ids (e.g. non-leaf rows in a leafs-only mode) are
    dropped per-row at render time — a non-selectable row just won't
    render ``aria-selected`` — so we don't filter them here.
    """
    if not is_multi_select(mode) and len(is_selected) > 1:
        return is_selected[:1]
    return is_selected


def apply_select_toggle(
    mode: SelectMode, is_selected: list[str], item_id: str
) -> list[str]:
    """Return the new selection list after toggling ``item_id``.

    In multi modes the id is added/removed; in single modes the
    selection is replaced with just ``item_id``. Returns a new list —
    callers should assign it back onto state rather than mutating in
    place.
    """
    if is_multi_select(mode):
        if item_id in is_selected:
            return [x for x in is_selected if x != item_id]
        return [*is_selected, item_id]
    return [item_id]


async def read_state_from_request[S: TableState](
    state_input_name: str, state_type: type[S]
) -> S | None:
    """Read the table's persisted state from the current request's form.

    Looks up the current :class:`RequestContext`, reads the hidden
    ``<input name=state_input_name>`` from the request body, and
    validates it as ``state_type``. Returns ``None`` when there's no
    current request, no form, or no such field — i.e. on the page-level
    first paint where the table hasn't been emitted yet.

    Used by both tables' public ``render()`` so callers (the filter
    drawer, ad-hoc page code) can pass only the fields they want to
    override; the rest carry over from the request's state input.
    """
    try:
        request = RequestContext.get().request
    except LookupError:
        request = None
    if request is None:
        return None
    form = await request.form()
    state_json = form.get(state_input_name)
    if state_json is None:
        return None
    return state_type.model_validate_json(str(state_json))


def is_htmx_request() -> bool:
    """True when the current request was issued by htmx, not a plain navigation.

    Both tables' ``update_query_fragment`` hook renders an oob copy of e.g a page-header button alongside
    the table. That trick only works while htmx's client-side runtime is actively processing the response: on a real AJAX round-trip it finds
    the ``hx-swap-oob``tagged node and swaps it into the existing element instead of inserting it inline. On a full-document page load there is
    no htmx JS running yet, so the same node would just render as literal, visible duplicate HTML wherever the server happened to place it. Every
    request htmx issues carries ``HX-Request: true``, so we need to tell the two cases apart.
    """
    try:
        request = RequestContext.get().request
    except LookupError:
        return False
    return request is not None and request.headers.get("HX-Request") == "true"


def render_state_input(
    state_div_id: str, state_input_name: str, state: BaseModel
) -> y.Node:
    """The ``<div>`` holding the table's serialized state.

    Wraps a single hidden ``<input>`` whose value is ``state`` dumped to
    JSON. The wrapping div has a stable id so toolbar buttons, drawer
    triggers, and the column-resize JS can include it in their requests
    via ``hx-include``.
    """
    return y.div(id=state_div_id, data_hx_include="always")[
        y.input(
            type="hidden",
            name=state_input_name,
            value=state.model_dump_json(),
        ),
    ]


def render_toolbar(
    *,
    render_table_url: str,
    clear_sort_and_filter_url: str,
    filter_drawer: FilterDrawer,
    state_div_id: str,
    query: Query,
    leading_buttons: list[y.Node] | None = None,
    enable_sort_and_filter: bool = True,
) -> y.Node:
    """The toolbar above the table: maximize, clear, and settings.

    The maximize button posts ``action=toggle_fullscreen`` so the
    handler can flip ``state.fullscreen`` server-side rather than
    threading a transient form value. The clear button hits its own
    dedicated fragment. The settings button defers to the drawer's
    open-attributes helper and switches to ``appearance="primary"``
    while ``query`` has an active filter or sort, so the toolbar signals
    at a glance that the table isn't showing its unfiltered state.

    ``leading_buttons`` are rendered before the maximize button — the
    hierarchical table uses this slot for its expand-all / collapse-all
    pair, which would be meaningless on the flat table.

    When ``enable_sort_and_filter`` is ``False`` the clear and settings
    (filter-drawer) buttons are omitted — the maximize button and any
    ``leading_buttons`` still render.
    """
    sort_and_filter_buttons: list[y.Node] = []
    if enable_sort_and_filter:
        sort_and_filter_buttons = [
            button(
                icon="x",
                variant="ghost",
                disabled=not query.is_active_filter_or_sort(),
                title="Clear Filter & Sort",
                **htmx(
                    hx_post=clear_sort_and_filter_url,
                    hx_swap="none",
                    hx_include="[data-hx-include='always']",
                ),
            ),
            button(
                icon="settings",
                variant="ghost",
                appearance="primary" if query.is_active_filter_or_sort() else "neutral",
                title="Filter & Sort Settings",
                **filter_drawer.open_drawer_htmx_attributes(
                    kwargs={"hx_include": "[data-hx-include='always']"}
                ),
            ),
        ]

    return table.toolbar[
        leading_buttons or [],
        button(
            icon="maximize",
            variant="ghost",
            title="Show Table Full Screen",
            **htmx(
                hx_post=render_table_url,
                hx_swap="none",
                hx_include="[data-hx-include='always']",
                hx_vals={"action": TOGGLE_FULLSCREEN_ACTION},
            ),
        ),
        sort_and_filter_buttons,
    ]


def cell_click_attrs[T](column: Column[T]) -> dict:
    """Stop an ``actions`` cell's clicks from bubbling to the row selection toggle.

    One attr on the cell beats a ``stopPropagation`` on every button inside.
    The cell-kind modifier class itself is now emitted by ``table.td(kind=...)``.
    """
    if column.kind == "actions":
        return {"hx-on:click": "event.stopPropagation()"}
    return {}


def render_header_cell[T](
    column: Column[T],
    col_idx: int,
    query: Query,
    *,
    table_header_click_url: str,
    wrapper_div_id: str,
    state_div_id: str,
    col_idx_offset: int = 0,
    enable_sort_and_filter: bool = True,
) -> y.Node:
    """One ``table.th`` with sort/filter icons and the resize handle.

    ``col_idx_offset`` shifts the resizer's ``data-col-idx`` past any leading
    non-resizable columns (the tree table prepends an expand column at grid
    index 0, so it passes ``col_idx_offset=1``). When ``enable_sort_and_filter``
    is ``False`` the header renders as plain text — no sort link, no icons — but
    keeps the resize handle.
    """
    resize = table.resize_handle(
        col_idx + col_idx_offset,
        title=f"Resize column `{column.label}`",
    )

    if not enable_sort_and_filter:
        return table.th(kind=column.kind)[column.header, resize]

    is_sort: SortDirection | None = (
        "asc"
        if query.is_asc(column.key)
        else "desc"
        if query.is_desc(column.key)
        else None
    )
    label = y.a(
        **htmx(
            hx_post=table_header_click_url,
            hx_target=f"#{wrapper_div_id}",
            hx_swap="outerHTML",
            hx_include="[data-hx-include='always']",
            hx_vals={"column_key": column.key},
            as_dict=True,
        ),
        href="#",
    )[column.header]

    return table.th(
        is_sort=is_sort,
        is_filter=query.is_active_filter(column.key),
        kind=column.kind,
    )[label, resize]


def column_widths_to_css_cols[T](
    columns: tuple[Column[T], ...],
    *,
    leading: str | None = None,
) -> str:
    """Build the ``--hx-table--cols`` grid track string.

    The trailing ``minmax(10px, auto)`` track pairs with the trailing
    placeholder ``<th>``/``<td>`` rendered by each table — it gives the
    rightmost column resizer something to drag against. ``leading`` is
    prepended verbatim when set; the hierarchical table uses it to
    reserve the expand column.
    """
    items: list[str] = []
    if leading is not None:
        items.append(leading)

    for col in columns:
        if isinstance(col.width, Flex):
            items.append(f"minmax({col.width.min_width}, {col.width.weight}fr)")
        elif isinstance(col.width, Fixed):
            items.append(col.width.width)

    items.append("minmax(10px, auto)")

    return " ".join(items)


type EmptyStateProvider = y.Node | SyncOrAsyncFn[Query, y.Node]
"""Static node or a sync/async producer that receives the current :class:`Query`.

Use this on a data table to control what's shown beneath the column
header when ``source.fetch()`` returns no rows. A bare ``y.Node`` is the
common case; a callable lets the message react to the active filter
(e.g. ``"No matches for your filter"`` vs. ``"No items yet"``). The
component wraps the resolved node in ``<tr><td colspan="N">…</td></tr>``
so callers don't need to know the column count.
"""


async def resolve_empty_state(
    provider: EmptyStateProvider | None, query: Query
) -> y.Node:
    """Materialize an :data:`EmptyStateProvider` into a concrete node.

    ``None`` returns the default ``"No items to display"``. A callable
    with at least one required positional parameter is treated as a
    producer and invoked with ``query`` (awaited if it returns an
    ``Awaitable``). Anything else passes through unchanged — htpy
    ``Element`` instances are callable but their ``__call__`` only takes
    ``**kwargs``, so the arity check distinguishes them from real
    producers.
    """
    if provider is None:
        return "No items to display"
    if callable(provider):
        try:
            sig = inspect.signature(provider)
            takes_query = any(
                p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
                and p.default is Parameter.empty
                for p in sig.parameters.values()
            )
        except (TypeError, ValueError):
            takes_query = False
        if takes_query:
            producer = cast(Callable[[Query], y.Node | Awaitable[y.Node]], provider)
            result = producer(query)
            if isinstance(result, Awaitable):
                result = await result
            return result
    return cast(y.Node, provider)


def render_empty_row(content: y.Node) -> y.Node:
    """Wrap empty-state content in a full-width body row.

    The ``empty`` cell kind carries ``hx-table__cell--empty``, whose CSS spans
    every column via ``grid-column: 1 / -1``.
    """
    return table.tr[table.td(kind="empty")[content]]
