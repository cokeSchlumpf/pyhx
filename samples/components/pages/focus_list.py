"""Focus list demo page."""

from typing import NamedTuple

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from pyhx.core.primitives import htmx, styles
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()


class Item(NamedTuple):
    """A sample row. ``status`` / ``owner`` are the extra columns the table
    variant lays out; cards / plain only use ``title`` + ``body``."""

    id: str
    title: str
    body: str
    status: str
    owner: str


ITEMS: list[Item] = [
    Item(
        "strategy",
        "FY25 Growth Strategy",
        "Three-horizon plan covering core defence, adjacent expansion and "
        "two venture bets. Owners assigned per workstream with quarterly gates.",
        "Active",
        "M. Wellner",
    ),
    Item(
        "audit",
        "Q2 Controls Audit",
        "Walkthrough of the revenue and procurement controls. Two design gaps "
        "raised, both with agreed remediation dates inside the quarter.",
        "In review",
        "S. Klein",
    ),
    Item(
        "migration",
        "Platform Migration",
        "Lift-and-reshape of the reporting stack onto the shared data platform. "
        "Cutover rehearsed twice; rollback window is the first weekend of July.",
        "On track",
        "R. Vogt",
    ),
    Item(
        "hiring",
        "Hiring Plan",
        "Eight roles across engineering and delivery. Pipeline healthy for six; "
        "the two principal roles need an external search partner.",
        "At risk",
        "P. Adler",
    ),
]


def _lead(body: str) -> str:
    """First sentence of the body, used as the collapsed one-liner."""
    return body.split(". ")[0] + "."


# --- htmx wiring (shared) ---
# Re-render the *whole* list so only one item is ever active, and let htmx run
# the swap inside a View Transition for the lift / resize.


def _swap() -> dict:
    return htmx(
        hx_target="closest .hx-focus-list",
        hx_swap="outerHTML transition:true",
        as_dict=True,
    )


def _edit(variant: c.FocusListVariant, id: str) -> dict:
    return htmx(hx_post=select.url(variant=variant, id=id), **_swap())


def _close(variant: c.FocusListVariant) -> dict:
    return htmx(hx_post=cancel.url(variant=variant), **_swap())


def _backdrop(variant: c.FocusListVariant, selected: str | None) -> y.Node | None:
    # Transparent overlay over the locked rows while one is focused, wired to
    # clear the selection on click. The component only emits the div.
    if selected is None:
        return None
    return c.focus_list.backdrop(**_close(variant))


# --- cards / plain: free-form <div> rows with identical content ---


def _div_content(item: Item, active: bool, variant: c.FocusListVariant) -> y.Node:
    if active:
        return y.fragment[
            y.h3[item.title],
            y.p[item.body],
            c.button("Cancel", **_close(variant)),
        ]
    return y.fragment[
        y.h3[item.title],
        y.p(**styles("text-muted"))[_lead(item.body)],
        c.button("Edit", appearance="primary", **_edit(variant, item.id)),
    ]


# docs:start cards_demo
def render_cards(selected: str | None = None) -> y.Node:
    items = [
        c.focus_list.card_item(
            _div_content(it, it.id == selected, "cards"),
            id=f"cards-{it.id}",  # namespaced so view-transition-names stay unique
            active=it.id == selected,
        )
        for it in ITEMS
    ]
    return c.focus_list.cards(items, backdrop=_backdrop("cards", selected))
# docs:end cards_demo


# docs:start plain_demo
def render_plain(selected: str | None = None) -> y.Node:
    items = [
        c.focus_list.plain_item(
            _div_content(it, it.id == selected, "plain"),
            id=f"plain-{it.id}",
            active=it.id == selected,
        )
        for it in ITEMS
    ]
    return c.focus_list.plain(items, backdrop=_backdrop("plain", selected))
# docs:end plain_demo


# --- table: column-driven rows of cells ---

# The table variant is column-driven: one set of columns defines the header,
# the column widths (c.Flex / c.Fixed), and the alignment (kind) each body cell
# inherits by position. The "actions" kind right-aligns the action column.
# docs:start table_demo
COLUMNS = [
    c.focus_list.table_column("Initiative", width=c.Flex(weight=2)),
    c.focus_list.table_column("Status"),
    c.focus_list.table_column("Owner"),
    c.focus_list.table_column("", width=c.Fixed("7rem"), kind="actions"),
]


def _table_cells(item: Item, active: bool) -> list[c.FocusListCell]:
    if active:
        # The focused row expands into a detail view spanning every column.
        return [
            c.focus_list.table_cell(
                y.div(**styles("flex", "flex-col", "gap-sm"))[
                    y.strong[item.title],
                    y.p[item.body],
                    c.button("Cancel", **_close("table")),
                ],
                colspan="all",
            )
        ]
    # No per-cell alignment — the action cell inherits `kind="actions"` from its
    # column (COLUMNS), which right-aligns it. The whole row is the click target
    # (see render_table); the Edit button is the standard visual affordance and
    # carries no htmx of its own, so clicking it just bubbles up to the row's
    # handler (one request, no double-fire).
    return [
        c.focus_list.table_cell(item.title),
        c.focus_list.table_cell(item.status, **styles("text-muted")),
        c.focus_list.table_cell(item.owner),
        c.focus_list.table_cell(c.button("Edit", appearance="primary", type="button")),
    ]


def render_table(selected: str | None = None) -> y.Node:
    rows = []
    for it in ITEMS:
        active = it.id == selected
        # The whole collapsed row is clickable to open its detail view, with the
        # data-table hover affordance (`aria_selected`). The active row *is* the
        # open detail, so it carries no click handler.
        row_attrs = (
            {} if active else {"aria_selected": "false", **_edit("table", it.id)}
        )
        rows.append(
            c.focus_list.table_row(
                _table_cells(it, active),
                id=f"table-{it.id}",
                active=active,
                **row_attrs,
            )
        )
    # Header + column grid are derived from COLUMNS — no manual header row, no
    # hand-written `--hx-data-table-cols` string to keep in sync. ``id`` keeps
    # this table's header view-transition-name distinct from the selectable one.
    return c.focus_list.table(
        COLUMNS, rows, id="table-main", backdrop=_backdrop("table", selected)
    )
# docs:end table_demo


# --- Row-click to open: the whole row opens the detail view, no button ---
# The most natural fit for focus_list in a table: there is no action button at
# all — clicking a collapsed row opens its focus/detail view. Each collapsed row
# carries `aria_selected` (the clickable hover affordance) plus the open htmx;
# the open row spans the full width as the detail, with a Close action, and the
# backdrop closes it. This is the same focus model as above, minus the button.


def _open_row(id: str) -> dict:
    return htmx(hx_post=open_row.url(id=id), **_swap())


def _close_row() -> dict:
    return htmx(hx_post=close_row.url(), **_swap())


# docs:start click_table_demo
CLICK_COLUMNS = [
    c.focus_list.table_column("Initiative", width=c.Flex(weight=2)),
    c.focus_list.table_column("Status"),
    c.focus_list.table_column("Owner"),
]


def render_click_table(selected: str | None = None) -> y.Node:
    rows = []
    for it in ITEMS:
        active = it.id == selected
        if active:
            cells = [
                c.focus_list.table_cell(
                    y.div(**styles("flex", "flex-col", "gap-sm"))[
                        y.strong[it.title],
                        y.p[it.body],
                        c.button("Close", **_close_row()),
                    ],
                    colspan="all",
                )
            ]
            row_attrs: dict = {}
        else:
            cells = [
                c.focus_list.table_cell(it.title),
                c.focus_list.table_cell(it.status, **styles("text-muted")),
                c.focus_list.table_cell(it.owner),
            ]
            # No button — the row itself opens the detail. `aria_selected` gives
            # the clickable hover affordance.
            row_attrs = {"aria_selected": "false", **_open_row(it.id)}
        rows.append(
            c.focus_list.table_row(cells, id=f"click-{it.id}", active=active, **row_attrs)
        )
    backdrop = c.focus_list.backdrop(**_close_row()) if selected else None
    return c.focus_list.table(CLICK_COLUMNS, rows, id="table-click", backdrop=backdrop)
# docs:end click_table_demo


@router.fragment.post("/focus-list/click-open/{id}")
async def open_row(id: str) -> y.Node:
    return render_click_table(selected=id)


@router.fragment.post("/focus-list/click-close")
async def close_row() -> y.Node:
    return render_click_table(selected=None)


def _render(variant: c.FocusListVariant, selected: str | None) -> y.Node:
    """Dispatch a URL's variant to its typed renderer (used by the routes)."""
    match variant:
        case "cards":
            return render_cards(selected)
        case "plain":
            return render_plain(selected)
        case "table":
            return render_table(selected)


@router.fragment.post("/focus-list/{variant}/select/{id}")
async def select(variant: c.FocusListVariant, id: str) -> y.Node:
    return _render(variant, selected=id)


@router.fragment.post("/focus-list/{variant}/cancel")
async def cancel(variant: c.FocusListVariant) -> y.Node:
    return _render(variant, selected=None)


@router.page("/focus-list", title="Focus list")
async def focus_list_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Focus list"],
            y.p[
                "A ",
                y.code["c.focus_list"],
                " is a vertical list where selecting one item pulls it into ",
                "focus: the active item lifts while the others ",
                y.strong["dim and lock"],
                " (they stop taking pointer input), funnelling attention onto the ",
                "single active row. Selection is server-driven — clicking ",
                y.strong["Edit"],
                " posts to a fragment that re-renders the list with that row ",
                "active; ",
                y.strong["Cancel"],
                " clears it.",
            ],
            y.p[
                "Because the list is swapped wholesale by htmx, the smooth lift / ",
                "resize is driven by the ",
                y.strong["View Transitions API"],
                " (htmx opts in via ",
                y.code['hx-swap="outerHTML transition:true"'],
                "), with each item carrying a stable ",
                y.code["view-transition-name"],
                " so it morphs in place rather than snapping.",
            ],
            y.p[
                "While a row is focused the list also passes ",
                y.code["c.focus_list.backdrop(...)"],
                " to the list helper's ",
                y.code["backdrop="],
                " argument — a transparent overlay above the locked rows (and below the ",
                "active one) that intercepts clicks on the rest of the list. The ",
                "component only emits the div; here it's wired with the same ",
                y.strong["Cancel"],
                " behaviour so clicking anywhere outside the focused row closes ",
                "it.",
            ],
            y.h2["Cards variant"],
            y.p[
                "Spaced, rounded, shadowed cards on the page surface. The active ",
                "card lifts with a stronger shadow; the rest fade back.",
            ],
            y.div(style="margin-block: 1rem;")[render_cards(),],
            c.code([
                ("code", src.text("cards_demo"), "python"),
                ("imports", src.text("imports"), "python"),
            ]),
            y.h2["Plain variant"],
            y.p[
                "Flush rows divided by a single 1px rule (the same neutral the ",
                "data tables use) — no gaps, no rounded corners, no resting ",
                "shadow. Only the active row gains a shadow and lifts above its ",
                "neighbours.",
            ],
            y.div(style="margin-block: 1rem;")[render_plain(),],
            c.code([("code", src.text("plain_demo"), "python")]),
            y.h2["Table variant"],
            y.p[
                "Real ",
                y.code["<table>"],
                " markup — ",
                y.code["tbody → tr → td"],
                " — laid out with CSS grid like the data tables, so the rows still ",
                "lift and morph. It's column-driven: a set of ",
                y.code["c.focus_list.table_column(...)"],
                " defines the header, the widths (",
                y.code["c.Flex"],
                " / ",
                y.code["c.Fixed"],
                ", reused from the data tables), and the ",
                y.code["kind"],
                " each cell inherits for alignment. Collapsed rows show the ",
                "columns; the focused row spans the full width as a detail view.",
            ],
            y.div(style="margin-block: 1rem;")[render_table(),],
            c.code([("code", src.text("table_demo"), "python")]),
            y.h2["Row-click to open (no button)"],
            y.p[
                "The same focus model as above, but with ",
                y.strong["no action button"],
                " — the whole row is the trigger. Each collapsed row carries ",
                y.code['aria-selected="false"'],
                " for the clickable hover affordance plus its own open htmx, so ",
                "clicking anywhere on the row opens its detail view; the open row ",
                "spans the full width with a ",
                y.strong["Close"],
                " action. Hover a row to see the cell tint, then click to open.",
            ],
            y.div(style="margin-block: 1rem;")[render_click_table(),],
            c.code([("code", src.text("click_table_demo"), "python")]),
        ]
    )
