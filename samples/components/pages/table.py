"""Table demo page.

Exercises the ``table`` primitive and its namespaced child tags
(``table.thead`` / ``table.tbody`` / ``table.tfoot`` / ``table.tr`` /
``table.th`` / ``table.td``). Each section renders a live table followed by the
exact source that produced it.
"""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from samples.components._snippets import snippets

src = snippets(__file__)


router = WebAppRouter()


# A small, realistic dataset: pioneering figures in computing.
PEOPLE: tuple[tuple[str, str, str, str], ...] = (
    ("Ada Lovelace", "United Kingdom", "1815", "First published algorithm"),
    ("Alan Turing", "United Kingdom", "1912", "Turing machine, Enigma"),
    ("Grace Hopper", "United States", "1906", "Compilers, COBOL"),
    ("John von Neumann", "Hungary / US", "1903", "Stored-program architecture"),
    ("Katherine Johnson", "United States", "1918", "Orbital mechanics"),
    ("Dennis Ritchie", "United States", "1941", "C, Unix"),
)


# Cell-kind sample: a small product catalogue. Columns exercise the numeric,
# date, boolean, list and actions cell kinds; name stays a plain text cell.
# (name, price, updated, in_stock, tags)
PRODUCTS: tuple[tuple[str, str, str, bool, tuple[str, ...]], ...] = (
    ("Widget", "1,299.00", "2026-01-14", True, ("new", "featured")),
    ("Gadget", "49.50", "2025-11-02", False, ("sale",)),
    ("Gizmo", "8,750.00", "2026-03-21", True, ("featured", "limited", "eco")),
    ("Doohickey", "12.00", "2025-08-30", True, ()),
)


def _bool_cell(value: bool) -> y.Node:
    """Render a boolean as a check (true) or dash (false) icon."""
    return c.icon("check") if value else c.icon("minus")


# Tree sample: a small org hierarchy. Each row carries its tree `level`; rows
# with children also carry `is_expanded`. (name, level, headcount, is_expanded)
# `is_expanded is None` marks a leaf (no toggle).
TREE_ROWS: tuple[tuple[str, int, str, bool | None], ...] = (
    ("Engineering", 1, "48", True),
    ("Frontend", 2, "12", True),
    ("Web app", 3, "7", None),
    ("Design system", 3, "5", None),
    ("Backend", 2, "18", False),
    ("Platform", 2, "18", None),
    ("Marketing", 1, "9", False),
)


def _tree_expand_cell(is_expanded: bool | None) -> y.Node:
    """Leading expand-column cell: a toggle button for parents, empty for leaves.

    Leaf rows (``is_expanded is None``) render an empty cell; parent rows render
    a chevron button. No click behaviour is wired up here.
    """
    if is_expanded is None:
        return c.table.td[""]
    chevron = "chevron-down" if is_expanded else "chevron-right"
    return c.table.td[
        c.button(icon=chevron, variant="ghost", size="sm", aria_label="Toggle"),
    ]


# Simple calendar sample: one month (July), 31 days.
CAL_DAYS = 31
WEEKDAY_LETTERS = ("M", "T", "W", "T", "F", "S", "S")
CALENDAR_PROJECTS = ("Website redesign", "Mobile app", "API migration", "Data warehouse")


# Stacked-bar chart sample: each project's effort split across phases as
# fractions of the column height (design / build / QA). Percentages need not
# sum to 1 — any remainder shows as empty space at the top of the bar.
STACK_ROWS = (
    ("Website redesign", "A. Okafor", "48,000", (
        c.StackChartItem(color=c.Color.info(), title="Design — 40%", percent=c.Pct.of(40)),
        c.StackChartItem(color=c.Color.success(), title="Build — 40%", percent=c.Pct.of(40)),
        c.StackChartItem(color=c.Color.warning(), title="QA — 15%", percent=c.Pct.of(15)),
    )),
    ("Mobile app", "R. Silva", "72,500", (
        c.StackChartItem(color=c.Color.info(), title="Design — 25%", percent=c.Pct.of(25)),
        c.StackChartItem(color=c.Color.success(), title="Build — 55%", percent=c.Pct.of(55)),
        c.StackChartItem(color=c.Color.warning(), title="QA — 20%", percent=c.Pct.of(20)),
    )),
    ("API migration", "T. Nguyen", "31,000", (
        c.StackChartItem(color=c.Color.info(), title="Design — 15%", percent=c.Pct.of(15)),
        c.StackChartItem(color=c.Color.success(), title="Build — 35%", percent=c.Pct.of(35)),
        c.StackChartItem(color=c.Color.warning(), title="QA — 10%", percent=c.Pct.of(10)),
    )),
)


@router.page("/table", title="Table")
async def table_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Table"],
            y.p[
                "The ",
                y.code["c.table"],
                " primitive renders a ",
                y.code["<table>"],
                " inside a scroll container. Its child tags are exposed as "
                "attributes — ",
                y.code["table.thead"],
                ", ",
                y.code["table.tbody"],
                ", ",
                y.code["table.tr"],
                ", ",
                y.code["table.th"],
                ", ",
                y.code["table.td"],
                " — so you build the markup without importing each one.",
            ],
            # --- Basic table: header, body, footer -------------------------
            y.h2["Basic table"],
            y.p[
                "Compose a ",
                y.code["table.thead"],
                ", ",
                y.code["table.tbody"],
                " and optional ",
                y.code["table.tfoot"],
                " from ",
                y.code["table.tr"],
                " rows. Use ",
                y.code["table.th"],
                " for header cells and ",
                y.code["table.td"],
                " for data cells. With no explicit widths every column shares "
                "the available space equally.",
            ],
            # docs:start basic
            c.table[
                c.table.thead[
                    c.table.tr[
                        c.table.th["Name"],
                        c.table.th["Country"],
                        c.table.th["Born"],
                        c.table.th["Known for"],
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr[
                            c.table.td[name],
                            c.table.td[country],
                            c.table.td[born],
                            c.table.td[known_for],
                        ]
                        for name, country, born, known_for in PEOPLE
                    ]
                ],
                c.table.tfoot[
                    c.table.tr[
                        c.table.td[f"{len(PEOPLE)} people"],
                        c.table.td[""],
                        c.table.td[""],
                        c.table.td[""],
                    ]
                ],
            ],
            # docs:end basic
            c.code(
                [
                    # The actual call is the most important part — show it first
                    # (and active by default).
                    ("code", src.text("basic"), "python"),
                    ("imports", src.text("imports"), "python"),
                ]
            ),
            # --- Custom column widths --------------------------------------
            y.h2["Custom column widths"],
            y.p[
                "Pass ",
                y.code["column_widths"],
                " — a space-separated CSS grid track list — to size columns "
                "explicitly. Here ",
                y.code["Name"],
                " and ",
                y.code["Known for"],
                " get more room (",
                y.code["2fr"],
                " / ",
                y.code["3fr"],
                ") while ",
                y.code["Country"],
                " and ",
                y.code["Born"],
                " stay narrow (",
                y.code["1fr"],
                "). Fixed units such as ",
                y.code["120px"],
                " work too.",
            ],
            # docs:start column_widths
            c.table(column_widths="2fr 1fr 1fr 3fr")[
                c.table.thead[
                    c.table.tr[
                        c.table.th["Name"],
                        c.table.th["Country"],
                        c.table.th["Born"],
                        c.table.th["Known for"],
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr[
                            c.table.td[name],
                            c.table.td[country],
                            c.table.td[born],
                            c.table.td[known_for],
                        ]
                        for name, country, born, known_for in PEOPLE
                    ]
                ],
            ],
            # docs:end column_widths
            c.code([("code", src.text("column_widths"), "python")]),
            # --- Toolbar as table controls ---------------------------------
            y.h2["Toolbar"],
            y.p[
                "Pass ",
                y.code["controls=c.table.toolbar[...]"],
                " to render a control bar above the table — a natural home for "
                'add / filter / settings actions. The buttons below are for '
                "show; wire up your own handlers.",
            ],
            # docs:start toolbar
            c.table(
                controls=c.table.toolbar[
                    c.button("Add row", icon="plus", appearance="primary", size="sm"),
                    c.button(
                        icon="filter",
                        variant="ghost",
                        title="Filter",
                        aria_label="Filter",
                    ),
                    c.button(
                        icon="settings",
                        variant="ghost",
                        title="Settings",
                        aria_label="Settings",
                    ),
                ],
            )[
                c.table.thead[
                    c.table.tr[
                        c.table.th["Name"],
                        c.table.th["Country"],
                        c.table.th["Born"],
                        c.table.th["Known for"],
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr[
                            c.table.td[name],
                            c.table.td[country],
                            c.table.td[born],
                            c.table.td[known_for],
                        ]
                        for name, country, born, known_for in PEOPLE
                    ]
                ],
            ],
            # docs:end toolbar
            c.code([("code", src.text("toolbar"), "python")]),
            # --- Resize handles in headers ---------------------------------
            y.h2["Resizable columns"],
            y.p[
                "Add a ",
                y.code["c.table.resize_handle(col_idx, title)"],
                " to a header cell to let users drag-resize that column. Give it "
                "the column's zero-based index. Resizing happens in the browser; "
                "the trailing empty column soaks up the remaining space.",
            ],
            # docs:start resize
            c.table(column_widths="200px 160px 100px 240px 1fr")[
                c.table.thead[
                    c.table.tr[
                        c.table.th["Name", c.table.resize_handle(0, "Resize Name")],
                        c.table.th["Country", c.table.resize_handle(1, "Resize Country")],
                        c.table.th["Born", c.table.resize_handle(2, "Resize Born")],
                        c.table.th["Known for", c.table.resize_handle(3, "Resize Known for")],
                        c.table.th[""],  # filler — takes remaining space
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr[
                            c.table.td[name],
                            c.table.td[country],
                            c.table.td[born],
                            c.table.td[known_for],
                            c.table.td[""],  # filler
                        ]
                        for name, country, born, known_for in PEOPLE
                    ]
                ],
            ],
            # docs:end resize
            c.code([("code", src.text("resize"), "python")]),
            # --- Calendar: multi-line header -------------------------------
            y.h2["Multi-line header"],
            y.p[
                "Header rows are ordinary ",
                y.code["table.tr"],
                " rows, so they take the standard HTML ",
                y.code["rowspan"],
                " attribute; pass ",
                y.code["span=N"],
                " to a ",
                y.code["table.th"],
                " or ",
                y.code["table.td"],
                " to span N columns (",
                y.code["grid-column: span N"],
                ") — here a month spanning all day columns above weekday "
                "letters and date numbers.",
            ],
            # docs:start calendar
            # The table is wider than its container, so wrap it in a
            # `table.scroll_container` to get horizontal scrolling.
            c.table.scroll_container[
                c.table(column_widths=f"200px repeat({CAL_DAYS}, 44px)")[
                    c.table.thead[
                        # Row 1 — month, spanning all day columns.
                        c.table.tr[
                            c.table.th(rowspan=3)["Project Name"],
                            c.table.th(span=CAL_DAYS)["July"],
                        ],
                        # Row 2 — weekday letter.
                        c.table.tr[
                            c.table.th[""],
                            *[c.table.th[WEEKDAY_LETTERS[i % 7]] for i in range(CAL_DAYS)],
                        ],
                        # Row 3 — date number.
                        c.table.tr[
                            c.table.th[""],
                            *[c.table.th[str(i + 1)] for i in range(CAL_DAYS)],
                        ],
                    ],
                    c.table.tbody[
                        [
                            c.table.tr[
                                c.table.th[name],
                                *[c.table.td["x"] for _ in range(CAL_DAYS)],
                            ]
                            for name in CALENDAR_PROJECTS
                        ]
                    ],
                ],
            ],
            # docs:end calendar
            c.code([("code", src.text("calendar"), "python")]),
            # --- Cell kinds ------------------------------------------------
            y.h2["Cell kinds"],
            y.p[
                "Pass ",
                y.code["kind="],
                " to a ",
                y.code["table.td"],
                " or ",
                y.code["table.th"],
                " to style a cell for its content type: ",
                y.code["numeric"],
                " (right-aligned figures), ",
                y.code["date"],
                ", ",
                y.code["boolean"],
                ", ",
                y.code["list"],
                ", ",
                y.code["actions"],
                ", ",
                y.code["layout"],
                " and ",
                y.code["empty"],
                ". Give the header cell the same ",
                y.code["kind"],
                " to align the heading with its column.",
            ],
            # docs:start cell_kinds
            c.table(column_widths="2fr 1fr 1fr 90px 2fr 120px")[
                c.table.thead[
                    c.table.tr[
                        c.table.th["Product"],
                        c.table.th(kind="numeric")["Price"],
                        c.table.th(kind="date")["Updated"],
                        c.table.th(kind="boolean")["In stock"],
                        c.table.th(kind="list")["Tags"],
                        c.table.th(kind="actions")["Actions"],
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr[
                            c.table.td[name],
                            c.table.td(kind="numeric")[price],
                            c.table.td(kind="date")[updated],
                            c.table.td(kind="boolean")[_bool_cell(in_stock)],
                            c.table.td(kind="list")[
                                c.pill.container(*[c.pill(tag) for tag in tags])
                            ],
                            c.table.td(kind="actions")[
                                c.button(
                                    icon="edit-2",
                                    variant="ghost",
                                    size="sm",
                                    title="Edit",
                                    aria_label="Edit",
                                ),
                                c.button(
                                    icon="trash-2",
                                    variant="ghost",
                                    size="sm",
                                    title="Delete",
                                    aria_label="Delete",
                                ),
                            ],
                        ]
                        for name, price, updated, in_stock, tags in PRODUCTS
                    ]
                ],
            ],
            # docs:end cell_kinds
            c.code([("code", src.text("cell_kinds"), "python")]),
            # --- Layout cell -----------------------------------------------
            y.h2["Layout cell"],
            y.p[
                "The ",
                y.code["layout"],
                " kind removes the cell's default padding and layout so your own "
                "content owns the whole cell box — handy for stacking a primary "
                "and secondary line in a single column.",
            ],
            # docs:start layout_cell
            c.table(column_widths="2fr 1fr 1fr")[
                c.table.thead[
                    c.table.tr[
                        c.table.th["Person"],
                        c.table.th(kind="date")["Born"],
                        c.table.th["Country"],
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr[
                            c.table.td(kind="layout")[
                                y.div(
                                    style="display: flex; flex-direction: column; "
                                    "gap: 2px; padding: var(--hx-spacing-sm) "
                                    "var(--hx-spacing-md);"
                                )[
                                    y.strong[name],
                                    y.small(style="opacity: 0.6;")[known_for],
                                ]
                            ],
                            c.table.td(kind="date")[born],
                            c.table.td[country],
                        ]
                        for name, country, born, known_for in PEOPLE
                    ]
                ],
            ],
            # docs:end layout_cell
            c.code([("code", src.text("layout_cell"), "python")]),
            # --- Empty cell ------------------------------------------------
            y.h2["Empty state"],
            y.p[
                "The ",
                y.code["empty"],
                " kind spans every column and centres its content — use it for a "
                "single empty-state row when there is no data to show.",
            ],
            # docs:start empty_cell
            c.table(column_widths="2fr 1fr 1fr 1fr")[
                c.table.thead[
                    c.table.tr[
                        c.table.th["Name"],
                        c.table.th["Country"],
                        c.table.th["Born"],
                        c.table.th["Known for"],
                    ]
                ],
                c.table.tbody[
                    c.table.tr[
                        c.table.td(kind="empty")["No records found"],
                    ]
                ],
            ],
            # docs:end empty_cell
            c.code([("code", src.text("empty_cell"), "python")]),
            # --- Sort & filter headers -------------------------------------
            y.h2["Sort & filter headers"],
            y.p[
                "Header cells accept ",
                y.code["is_sort"],
                " (",
                y.code['"asc"'],
                " / ",
                y.code['"desc"'],
                ") and ",
                y.code["is_filter"],
                ", adding a trailing chevron or funnel icon. These render the "
                "affordance only — wire the actual sorting and filtering in your "
                "own handler.",
            ],
            # docs:start sort_filter
            c.table(column_widths="2fr 1fr 1fr 2fr")[
                c.table.thead[
                    c.table.tr[
                        c.table.th(is_sort="asc")["Name"],
                        c.table.th(is_filter=True)["Country"],
                        c.table.th(is_sort="desc", kind="numeric")["Born"],
                        c.table.th["Known for"],
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr[
                            c.table.td[name],
                            c.table.td[country],
                            c.table.td(kind="numeric")[born],
                            c.table.td[known_for],
                        ]
                        for name, country, born, known_for in PEOPLE
                    ]
                ],
            ],
            # docs:end sort_filter
            c.code([("code", src.text("sort_filter"), "python")]),
            # --- Selectable rows -------------------------------------------
            y.h2["Selectable rows"],
            y.p[
                "Rows accept ",
                y.code["is_selected"],
                ": ",
                y.code["False"],
                " marks a row selectable (pointer cursor + hover tint), ",
                y.code["True"],
                " keeps it highlighted, and ",
                y.code["None"],
                " leaves the row inert. The second row below is pre-selected.",
            ],
            # docs:start selectable
            c.table(column_widths="2fr 1fr 1fr 2fr")[
                c.table.thead[
                    c.table.tr[
                        c.table.th["Name"],
                        c.table.th["Country"],
                        c.table.th["Born"],
                        c.table.th["Known for"],
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr(is_selected=(i == 1))[
                            c.table.td[name],
                            c.table.td[country],
                            c.table.td[born],
                            c.table.td[known_for],
                        ]
                        for i, (name, country, born, known_for) in enumerate(PEOPLE)
                    ]
                ],
            ],
            # docs:end selectable
            c.code([("code", src.text("selectable"), "python")]),
            # --- Tree table (hierarchy) ------------------------------------
            y.h2["Tree table"],
            y.p[
                "Pass ",
                y.code["is_tree=True"],
                " for a hierarchical table with a leading expand column. Each row "
                "sets its ",
                y.code["level"],
                " (1-based) to control its indent; parent rows also set ",
                y.code["is_expanded"],
                ". ",
                y.code["column_widths"],
                " describes the data columns only — the expand column is added "
                "for you, and is required (a tree table needs explicit widths). "
                "Toggle behaviour is up to you.",
            ],
            # docs:start tree
            c.table(is_tree=True, column_widths="2fr 1fr")[
                c.table.thead[
                    c.table.tr[
                        c.table.th[""],  # leading expand column
                        c.table.th["Team"],
                        c.table.th(kind="numeric")["Headcount"],
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr(level=level, is_expanded=is_expanded)[
                            _tree_expand_cell(is_expanded),
                            c.table.td[name],
                            c.table.td(kind="numeric")[headcount],
                        ]
                        for name, level, headcount, is_expanded in TREE_ROWS
                    ]
                ],
            ],
            # docs:end tree
            c.code([("code", src.text("tree"), "python")]),
            # --- Indented rows without a toggle ----------------------------
            y.h2["Indented rows (no toggle)"],
            y.p[
                "The per-level indent keys off ",
                y.code["level"],
                " (→ ",
                y.code["aria-level"],
                ") alone, independent of ",
                y.code["is_tree"],
                ". Set ",
                y.code["level"],
                " on each row — without ",
                y.code["is_tree"],
                " and without an expand column — to render a static hierarchy: "
                "the first cell in each body row is indented one spacing step per "
                "level. The first cell may be a data ",
                y.code["td"],
                " or, as here, a row-header ",
                y.code["th"],
                ".",
            ],
            # docs:start tree_static
            c.table(column_widths="2fr 1fr")[
                c.table.thead[
                    c.table.tr[
                        c.table.th["Team"],
                        c.table.th(kind="numeric")["Headcount"],
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr(level=level)[
                            c.table.th(scope="row")[name],
                            c.table.td(kind="numeric")[headcount],
                        ]
                        for name, level, headcount, _ in TREE_ROWS
                    ]
                ],
            ],
            # docs:end tree_static
            c.code([("code", src.text("tree_static"), "python")]),
            # --- Stacked-bar chart cell ------------------------------------
            y.h2["Stacked-bar chart cell"],
            y.p[
                "Pass ",
                y.code["c.table.stack_chart_cell(items=[...])"],
                " to fill a cell with a vertical stacked-bar chart. Each ",
                y.code["c.StackChartItem"],
                " sets a ",
                y.code["color"],
                " (a ",
                y.code["c.Color"],
                "), a ",
                y.code["title"],
                " (shown on hover) and a ",
                y.code["percent"],
                " (0–1) for its share of the cell height. The cell has no "
                "padding so the bars meet its edges; segments stack from the "
                "bottom up, and any remainder shows as empty space on top. Give "
                "the cell a height (here via an inline ",
                y.code["style"],
                ") so the bars have room.",
            ],
            # docs:start stack_chart
            c.table(column_widths="2fr 1fr 1fr 120px")[
                c.table.thead[
                    c.table.tr[
                        c.table.th["Project"],
                        c.table.th["Lead"],
                        c.table.th(kind="numeric")["Budget"],
                        c.table.th["Effort mix"],
                    ]
                ],
                c.table.tbody[
                    [
                        c.table.tr[
                            c.table.td[name],
                            c.table.td[lead],
                            c.table.td(kind="numeric")[budget],
                            c.table.stack_chart_cell(
                                items=list(items), style="height: 96px"
                            ),
                        ]
                        for name, lead, budget, items in STACK_ROWS
                    ]
                ],
            ],
            # docs:end stack_chart
            c.code([("code", src.text("stack_chart"), "python")]),
        ]
    )
