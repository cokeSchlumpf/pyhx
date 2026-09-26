"""DataTable demo page — Bundesliga 2023/24 standings + a hierarchical tree example."""

from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Annotated

import htpy as y
import pyhx.components as c
from pyhx.utils import lorem_ipsum

from pydantic import BaseModel

from pyhx.core import WebAppRouter
from pyhx.components.data.sources.source import Query
from pyhx.components.data.sources.simple_hierarchical_data_source import (
    SimpleHierarchicalDataSource,
)

from samples.components._snippets import snippets

src = snippets(__file__)


# docs:start team_model
class Team(BaseModel):
    id: int
    name: str
    points: int
    goals_for: int
    goals_against: int


# docs:end team_model


TEAMS: list[Team] = [
    Team(id=1, name="Bayer 04 Leverkusen", points=84, goals_for=89, goals_against=24),
    Team(id=2, name="VfB Stuttgart", points=73, goals_for=78, goals_against=39),
    Team(id=3, name="FC Bayern München", points=72, goals_for=94, goals_against=45),
    Team(id=4, name="RB Leipzig", points=65, goals_for=77, goals_against=39),
    Team(id=5, name="Borussia Dortmund", points=63, goals_for=68, goals_against=43),
    Team(id=6, name="Eintracht Frankfurt", points=47, goals_for=51, goals_against=51),
    Team(id=7, name="TSG Hoffenheim", points=46, goals_for=68, goals_against=66),
    Team(id=8, name="1. FC Heidenheim", points=46, goals_for=50, goals_against=55),
    Team(id=9, name="SC Freiburg", points=45, goals_for=42, goals_against=52),
    Team(id=10, name="Werder Bremen", points=43, goals_for=48, goals_against=54),
    Team(id=11, name="FC Augsburg", points=42, goals_for=46, goals_against=64),
    Team(id=12, name="VfL Wolfsburg", points=40, goals_for=43, goals_against=52),
    Team(id=13, name="1. FSV Mainz 05", points=39, goals_for=44, goals_against=53),
    Team(
        id=14,
        name="Borussia Mönchengladbach",
        points=39,
        goals_for=53,
        goals_against=68,
    ),
    Team(id=15, name="1. FC Union Berlin", points=33, goals_for=33, goals_against=58),
    Team(id=16, name="VfL Bochum", points=33, goals_for=37, goals_against=68),
    Team(id=17, name="1. FC Köln", points=27, goals_for=27, goals_against=60),
    Team(id=18, name="SV Darmstadt 98", points=17, goals_for=37, goals_against=87),
]


# docs:start columns
COLUMNS: tuple[c.Column[Team], ...] = (
    c.Column(
        key="id",
        label="#",
        header="#",
        render=lambda t: str(t.id),
        width=c.Fixed("60px"),
        filter_type=c.NumericFilter(),
    ),
    c.Column(
        key="name",
        label="Verein",
        header="Verein",
        render=lambda t: t.name,
        width=c.Flex(weight=4),
        filter_type=c.TextFilter(),
    ),
    c.Column(
        key="points",
        label="Punkte",
        header="Punkte",
        render=lambda t: str(t.points),
        width=c.Flex(weight=1, min_width="80px"),
        filter_type=c.NumericFilter(),
    ),
    c.Column(
        key="goals_for",
        label="Tore",
        header="Tore",
        render=lambda t: str(t.goals_for),
        width=c.Flex(weight=1, min_width="80px"),
        filter_type=c.NumericFilter(),
    ),
    c.Column(
        key="goals_against",
        label="Gegentore",
        header="Gegentore",
        render=lambda t: str(t.goals_against),
        width=c.Flex(weight=1, min_width="80px"),
        filter_type=c.NumericFilter(),
    ),
)
# docs:end columns


router = WebAppRouter()
# docs:start table
_table = c.DataTable[Team](
    routes=router, name="bundesliga", source=TEAMS, columns=COLUMNS
)
# docs:end table


# --- Selectable flat-table variants -----------------------------------------
#
# Same data and columns as the read-only table above, two extra DataTable
# instances differing only in `select_mode`. Each gets its own `name` so the
# constructor can register its own fragments. Pre-selected ids let the demo
# show the visual state without a wired-up click handler.

# docs:start table_single
_table_single = c.DataTable[Team](
    routes=router,
    name="bundesliga-single",
    source=TEAMS,
    columns=COLUMNS,
    select_mode="single",
)
# docs:end table_single
# docs:start table_multi
_table_multi = c.DataTable[Team](
    routes=router,
    name="bundesliga-multi",
    source=TEAMS,
    columns=COLUMNS,
    select_mode="multi",
)
# docs:end table_multi
_TEAMS_SINGLE_SELECTED: list[str] = ["3"]
_TEAMS_MULTI_SELECTED: list[str] = ["1", "5", "9"]


# ---------------------------------------------------------------------------
# Hierarchical example — a fictional org chart served by
# ``SimpleHierarchicalDataSource``. The UI is rendered ad-hoc below as a
# ``<table role="treegrid">`` to demonstrate the data source's per-level
# ``fetch`` contract; once the dedicated ``HierarchicalDataTable`` component
# is finished it will replace this hand-rolled render.
# ---------------------------------------------------------------------------


# docs:start org_model
class OrgUnit(BaseModel):
    id: str
    parent_id: str | None
    name: str
    head_count: int


# docs:end org_model


ORG_CHART: list[OrgUnit] = [
    # Roots
    OrgUnit(id="ceo", parent_id=None, name="Office of the CEO", head_count=4),
    OrgUnit(id="board", parent_id=None, name="Board", head_count=7),
    # Direct reports
    OrgUnit(id="eng", parent_id="ceo", name="Engineering", head_count=120),
    OrgUnit(id="sales", parent_id="ceo", name="Sales", head_count=80),
    OrgUnit(id="ops", parent_id="ceo", name="Operations", head_count=35),
    # Engineering sub-teams
    OrgUnit(id="backend", parent_id="eng", name="Backend", head_count=42),
    OrgUnit(id="frontend", parent_id="eng", name="Frontend", head_count=28),
    OrgUnit(id="platform", parent_id="eng", name="Platform", head_count=22),
    OrgUnit(id="qa", parent_id="eng", name="QA", head_count=18),
    # Backend pods
    OrgUnit(id="be-api", parent_id="backend", name="API", head_count=14),
    OrgUnit(id="be-data", parent_id="backend", name="Data Pipelines", head_count=12),
    # Sales sub-teams
    OrgUnit(id="sales-eu", parent_id="sales", name="EMEA", head_count=30),
    OrgUnit(id="sales-us", parent_id="sales", name="Americas", head_count=35),
    OrgUnit(id="sales-apac", parent_id="sales", name="APAC", head_count=15),
]


# docs:start org_columns
ORG_COLUMNS: tuple[c.Column[OrgUnit], ...] = (
    c.Column(
        key="name",
        label="Unit",
        header="Unit",
        render=lambda o: o.name,
        width=c.Flex(weight=4),
        filter_type=c.TextFilter(),
    ),
    c.Column(
        key="head_count",
        label="Headcount",
        header="Headcount",
        render=lambda o: str(o.head_count),
        width=c.Flex(weight=1, min_width="100px"),
        filter_type=c.NumericFilter(),
    ),
)
# docs:end org_columns


# A flat list with `parent_id` references → wrapped as a hierarchical source.
# `id_field` / `parent_id_field` defaults match the model.
# docs:start org_table
_org_source: SimpleHierarchicalDataSource[OrgUnit] = SimpleHierarchicalDataSource(
    ORG_CHART
)
_org_table = c.HierarchicalDataTable[OrgUnit](
    routes=router, name="org-chart", source=_org_source, columns=ORG_COLUMNS
)
# docs:end org_table


# --- Selectable variants -----------------------------------------------------
#
# Same data, two extra HierarchicalDataTable instances differing only in
# `select_mode`. Each gets its own `name` so the constructor can register
# its own fragments without clashing with the read-only `_org_table` above.
#
# In single mode the table renders `aria-selected="true|false"` per row.
# In multi mode it also adds `aria-multiselectable="true"` on the table
# itself, telling AT that more than one row may be selected at a time.

# docs:start org_table_single
_org_table_single = c.HierarchicalDataTable[OrgUnit](
    routes=router,
    name="org-chart-single",
    source=_org_source,
    columns=ORG_COLUMNS,
    select_mode="single-leafs",
)
# docs:end org_table_single
# docs:start org_table_multi
_org_table_multi = c.HierarchicalDataTable[OrgUnit](
    routes=router,
    name="org-chart-multi",
    source=_org_source,
    columns=ORG_COLUMNS,
    select_mode="multi",
)
# docs:end org_table_multi

# Pre-selected rows so the demo shows the selected state without needing a
# wired-up click handler. Single-select shows exactly one row picked; multi
# picks a few across different branches.
_SINGLE_SELECTED_IDS: list[str] = ["eng"]
_MULTI_SELECTED_IDS: list[str] = ["sales-us"]


# Render the demo with every expandable node already expanded — keeps the
# whole tree visible without needing the (not-yet-wired) expand-on-click flow.
_EXPANDED_ORG_IDS: list[str] = [
    o.id for o in ORG_CHART if any(c.parent_id == o.id for c in ORG_CHART)
]


# --- Empty-state variants ----------------------------------------------------
#
# Both data tables accept an `empty_state` parameter that controls what's
# rendered beneath the column header when the source returns no rows. The
# value is either a static `y.Node` or a sync/async callable receiving the
# current `Query` — useful for distinguishing "no items yet" from "no
# matches for the active filter".

_table_empty_default = c.DataTable[Team](
    routes=router, name="bundesliga-empty-default", source=[], columns=COLUMNS
)


# docs:start empty_dynamic
def _teams_empty_state(query: Query) -> y.Node:
    if query.is_active_filter_or_sort():
        return y.em["No teams match your filter."]
    return y.em["No teams yet — the season hasn't started."]


_table_empty_dynamic = c.DataTable[Team](
    routes=router,
    name="bundesliga-empty-dynamic",
    source=[],
    columns=COLUMNS,
    empty_state=_teams_empty_state,
)
# docs:end empty_dynamic

_org_table_empty = c.HierarchicalDataTable[OrgUnit](
    routes=router,
    name="org-chart-empty",
    source=SimpleHierarchicalDataSource[OrgUnit]([]),
    columns=ORG_COLUMNS,
    empty_state=y.em["No org units to display."],
)


# ---------------------------------------------------------------------------
# Auto-derived columns — DataTable[Release] reads ``c.annotations.*Column``
# markers off a Pydantic model and turns each annotated field into a
# ``Column[Release]`` automatically. Demonstrates:
#   * default columns derived from primitive field types
#   * explicit annotations with custom labels / widths / tooltips
#   * ``HiddenColumn`` — kept in the filter drawer but never rendered as a cell
#   * an explicit ``Column`` appended as an "actions" column
#   * ``columns_order`` as a whitelist + ordering for a second variant
# ---------------------------------------------------------------------------


# docs:start release_model
class ReleaseStatus(str, Enum):
    stable = "stable"
    beta = "beta"
    deprecated = "deprecated"


STATUS_OPTIONS = (
    c.Option(label="Stable", value="stable"),
    c.Option(label="Beta", value="beta"),
    c.Option(label="Deprecated", value="deprecated"),
)

TAG_OPTIONS = (
    c.Option(label="Server", value="server"),
    c.Option(label="Desktop", value="desktop"),
    c.Option(label="Cloud", value="cloud"),
    c.Option(label="IoT", value="iot"),
)


class Release(BaseModel):
    id: Annotated[int, c.annotations.HiddenColumn()]
    version: Annotated[
        str,
        c.annotations.TextColumn(
            label="Version",
            width=c.Fixed("120px"),
        ),
    ]
    codename: Annotated[
        str,
        c.annotations.TextColumn(
            label="Codename",
            tooltip="Internal release codename.",
            width=c.Flex(weight=2),
        ),
    ]
    released: Annotated[date, c.annotations.DateColumn(label="Released")]
    downloads: Annotated[int, c.annotations.NumericColumn(label="Downloads")]
    is_lts: Annotated[bool, c.annotations.BooleanColumn(label="LTS")]
    # Multi-select filter with a developer-chosen control (checkbox fieldset),
    # exactly like forms let you pick a form-field control.
    status: Annotated[
        ReleaseStatus,
        c.annotations.TextColumn(
            label="Status",
            filter=c.annotations.MultipleChoiceFilter(
                control=c.annotations.CheckboxFieldsetControl(options=STATUS_OPTIONS),
            ),
        ),
    ]
    # list[str] column: renders as pills, filters by set intersection.
    tags: Annotated[
        list[str],
        c.annotations.TextListColumn(
            label="Tags",
            filter=c.annotations.TextListFilter(
                control=c.annotations.DropdownControl(options=TAG_OPTIONS),
            ),
        ),
    ]


# docs:end release_model


RELEASES: list[Release] = [
    Release(
        id=1,
        version="22.04",
        codename="Jammy Jellyfish",
        released=date(2022, 4, 21),
        downloads=18_400_000,
        is_lts=True,
        status=ReleaseStatus.stable,
        tags=["server", "desktop"],
    ),
    Release(
        id=2,
        version="22.10",
        codename="Kinetic Kudu",
        released=date(2022, 10, 20),
        downloads=2_100_000,
        is_lts=False,
        status=ReleaseStatus.deprecated,
        tags=["desktop"],
    ),
    Release(
        id=3,
        version="23.04",
        codename="Lunar Lobster",
        released=date(2023, 4, 20),
        downloads=4_800_000,
        is_lts=False,
        status=ReleaseStatus.deprecated,
        tags=["cloud", "iot"],
    ),
    Release(
        id=4,
        version="23.10",
        codename="Mantic Minotaur",
        released=date(2023, 10, 12),
        downloads=6_300_000,
        is_lts=False,
        status=ReleaseStatus.stable,
        tags=["server", "cloud"],
    ),
    Release(
        id=5,
        version="24.04",
        codename="Noble Numbat",
        released=date(2024, 4, 25),
        downloads=12_700_000,
        is_lts=True,
        status=ReleaseStatus.stable,
        tags=["server", "desktop", "cloud"],
    ),
    Release(
        id=6,
        version="24.10",
        codename="Oracular Oriole",
        released=date(2024, 10, 10),
        downloads=3_400_000,
        is_lts=False,
        status=ReleaseStatus.beta,
        tags=["iot"],
    ),
]


# One explicit column tacked on for actions — illustrates the merge: derived
# columns come first (in field order), explicit columns are appended.
# docs:start release_actions
_RELEASE_ACTIONS: tuple[c.Column[Release], ...] = (
    c.Column(
        key="actions",
        label="",
        header="",
        render=lambda r: c.button(
            label="View",
            variant="ghost",
            size="sm",
        ),
        width=c.Fixed("90px"),
    ),
)
# docs:end release_actions


# Default variant: derived columns in field order, then the actions column.
# `id` is annotated with HiddenColumn — it won't render but stays in the
# filter drawer as a NumericFilter.
# docs:start release_table
_release_table = c.DataTable[Release](
    routes=router,
    name="releases",
    source=RELEASES,
    type=Release,
    columns=_RELEASE_ACTIONS,
)
# docs:end release_table


# Reordered variant: `columns_order` is an authoritative whitelist. Anything
# not listed here is dropped entirely — no render, no filter, no sort. Note
# `id` is omitted on purpose to prove that this even removes the otherwise-
# hidden-but-filterable column from the drawer.
# docs:start release_reordered
_release_table_reordered = c.DataTable[Release](
    routes=router,
    name="releases-reordered",
    source=RELEASES,
    type=Release,
    columns=_RELEASE_ACTIONS,
    columns_order=[
        "version",
        "status",
        "tags",
        "is_lts",
        "released",
        "downloads",
        "actions",
    ],
)
# docs:end release_reordered


# ---------------------------------------------------------------------------
# DateColumn formatting — four variants of `format=` on the same `released`
# field, side-by-side on the same rows. `LocalizedDateFormat` picks the
# locale from the request's Accept-Language header via
# `pyhx.core.primitives.negotiate_locale` (default supported set: en/de/it/fr).
# ---------------------------------------------------------------------------


# docs:start release_dates_model
class ReleaseDates(BaseModel):
    version: Annotated[
        str,
        c.annotations.TextColumn(label="Version", width=c.Fixed("100px")),
    ]
    iso: Annotated[
        date,
        c.annotations.DateColumn(label="ISO", format=c.annotations.IsoDateFormat()),
    ]
    pattern: Annotated[
        date,
        c.annotations.DateColumn(
            label="Pattern (short)",
            format=c.annotations.PatternDateFormat.short(),
        ),
    ]
    localized: Annotated[
        date,
        c.annotations.DateColumn(
            label="Localized (medium)",
            format=c.annotations.LocalizedDateFormat(width="medium"),
        ),
    ]
    relative: Annotated[
        date,
        c.annotations.DateColumn(
            label="Relative",
            format=c.annotations.RelativeDateFormat(),
        ),
    ]


# docs:end release_dates_model


_RELEASE_DATES: list[ReleaseDates] = [
    ReleaseDates(
        version=r.version,
        iso=r.released,
        pattern=r.released,
        localized=r.released,
        relative=r.released,
    )
    for r in RELEASES
]

# docs:start release_dates_table
_release_dates_table = c.DataTable[ReleaseDates](
    routes=router,
    name="release-dates",
    source=_RELEASE_DATES,
    type=ReleaseDates,
)
# docs:end release_dates_table


# ---------------------------------------------------------------------------
# DateTimeColumn formatting — a `datetime` field (date + time-of-day). The
# `auto` column is a bare `datetime` with no annotation: it auto-derives a
# `DateTimeColumn` whose default format is `RelativeDateFormat`. The remaining
# columns pin explicit formats that keep the time component.
# ---------------------------------------------------------------------------


# docs:start release_timestamps_model
class ReleaseTimestamps(BaseModel):
    version: Annotated[
        str,
        c.annotations.TextColumn(label="Version", width=c.Fixed("100px")),
    ]
    # Bare `datetime` → auto-derived DateTimeColumn, default relative format.
    auto: datetime
    iso: Annotated[
        datetime,
        c.annotations.DateTimeColumn(
            label="ISO", format=c.annotations.IsoDateFormat()
        ),
    ]
    pattern: Annotated[
        datetime,
        c.annotations.DateTimeColumn(
            label="Pattern (HH:mm:ss)",
            format=c.annotations.PatternDateFormat(pattern="%d %b %Y %H:%M:%S"),
        ),
    ]
    localized: Annotated[
        datetime,
        c.annotations.DateTimeColumn(
            label="Localized (medium)",
            format=c.annotations.LocalizedDateTimeFormat(width="medium"),
        ),
    ]


# docs:end release_timestamps_model


# Give each release a distinct instant in the recent past so the `auto`
# (relative) column reads naturally ("3 days ago", …). Anchored to UTC.
_NOW = datetime(2024, 10, 12, 9, 30, 45, tzinfo=timezone.utc)
_RELEASE_TIMESTAMPS: list[ReleaseTimestamps] = [
    ReleaseTimestamps(
        version=r.version,
        auto=_NOW - timedelta(days=index, hours=3, minutes=17),
        iso=_NOW - timedelta(days=index, hours=3, minutes=17),
        pattern=_NOW - timedelta(days=index, hours=3, minutes=17),
        localized=_NOW - timedelta(days=index, hours=3, minutes=17),
    )
    for index, r in enumerate(RELEASES)
]


# docs:start release_timestamps_table
_release_timestamps_table = c.DataTable[ReleaseTimestamps](
    routes=router,
    name="release-timestamps",
    source=_RELEASE_TIMESTAMPS,
    type=ReleaseTimestamps,
)
# docs:end release_timestamps_table


# ---------------------------------------------------------------------------
# NumericColumn formatting — five variants of `format=` on the same `downloads`
# field, side-by-side. Default for `NumericColumn` is `LocalizedNumberFormat()`,
# so the "Default" column already picks up locale-aware separators.
# ---------------------------------------------------------------------------


# docs:start release_numbers_model
class ReleaseNumbers(BaseModel):
    version: Annotated[
        str,
        c.annotations.TextColumn(label="Version", width=c.Fixed("100px")),
    ]
    iso: Annotated[
        int,
        c.annotations.NumericColumn(
            label="ISO", format=c.annotations.IsoNumberFormat()
        ),
    ]
    pattern: Annotated[
        int,
        c.annotations.NumericColumn(
            label="Pattern (thousands)",
            format=c.annotations.PatternNumberFormat.thousands(),
        ),
    ]
    localized: Annotated[
        int,
        c.annotations.NumericColumn(label="Localized"),
    ]
    localized_compact: Annotated[
        int,
        c.annotations.NumericColumn(
            label="Compact",
            format=c.annotations.LocalizedNumberFormat(width="compact"),
        ),
    ]
    eur: Annotated[
        float,
        c.annotations.NumericColumn(
            label="EUR price",
            format=c.annotations.CurrencyNumberFormat(currency="EUR"),
        ),
    ]


# docs:end release_numbers_model


# Synthesize an EUR "price" by dividing downloads by 1e6 — just to have a
# realistic-looking currency value rather than tens-of-millions in euros.
_RELEASE_NUMBERS: list[ReleaseNumbers] = [
    ReleaseNumbers(
        version=r.version,
        iso=r.downloads,
        pattern=r.downloads,
        localized=r.downloads,
        localized_compact=r.downloads,
        eur=r.downloads / 1_000_000,
    )
    for r in RELEASES
]

# docs:start release_numbers_table
_release_numbers_table = c.DataTable[ReleaseNumbers](
    routes=router,
    name="release-numbers",
    source=_RELEASE_NUMBERS,
    type=ReleaseNumbers,
)
# docs:end release_numbers_table


@router.page("/data-table", title="Data Table")
async def data_table_page() -> y.Node:
    return c.container(
        y.article[
            c.markdown("""
                # Data Table

                Bundesliga 2023/24 final standings rendered through `DataTable[Team]`.
                The constructor accepts `source: ReadOnlyDataSource[T] | list[T]` — passing a
                plain `list[Team]` wraps it in a `SimpleDataSource` automatically.
            """),
            await _table.render(),
            c.code(
                [
                    ("model", src.text("team_model"), "python"),
                    ("columns", src.text("columns"), "python"),
                    ("table", src.text("table"), "python"),
                ]
            ),
            c.markdown("""
                ### Selectable rows

                Pass `select_mode="single"` or `select_mode="multi"` to make
                rows selectable on a flat `DataTable` as well. The component
                renders `aria-selected` on each row, `role="grid"` on the
                table, and `aria-multiselectable="true"` on the table itself
                in multi mode — so assistive tech announces the selection
                state correctly. Row ids come from `source.get_id(item)`.

                #### Single-select

                Exactly one row carries `aria-selected="true"` at a time. Here
                the Bayern row (id `3`) is pre-selected.
            """),
            await _table_single.render(is_selected=_TEAMS_SINGLE_SELECTED),
            c.markdown("""
                #### Multi-select

                Any subset of rows can be selected. Three rows from different
                parts of the table are pre-selected to show the non-contiguous
                selection state.
            """),
            await _table_multi.render(is_selected=_TEAMS_MULTI_SELECTED),
            c.code(
                [
                    ("single", src.text("table_single"), "python"),
                    ("multi", src.text("table_multi"), "python"),
                ]
            ),
            c.markdown("""
                ## Hierarchical data table

                A fictional org chart rendered through `HierarchicalDataTable[OrgUnit]`,
                backed by `SimpleHierarchicalDataSource[OrgUnit]`. The flat input is a
                `list[OrgUnit]` with `parent_id` references; the source pre-indexes
                children by parent at construction and exposes them through one call
                per level — `await source.fetch(query, parent=...)`. Each returned
                `Node[T]` carries a filter-aware direct-child count so the table knows
                whether to render an expand affordance.

                Here all expandable nodes are pre-expanded so the full tree is visible
                — the expand-on-click handler isn't wired yet on the component side.
            """),
            await _org_table.render(is_expanded=[]),
            c.code(
                [
                    ("model", src.text("org_model"), "python"),
                    ("columns", src.text("org_columns"), "python"),
                    ("table", src.text("org_table"), "python"),
                ]
            ),
            c.markdown("""
                ## Selectable rows

                Pass `select_mode="single"` or `select_mode="multi"` to make rows
                selectable. The component renders `aria-selected` on each row (and
                `aria-multiselectable="true"` on the table itself in multi mode) so
                the selection state is announced correctly by assistive tech. The two
                tables below use the same data and columns; only `select_mode` — and
                the pre-selected ids passed to `render(is_selected=…)` — differ.

                ### Single-select

                Exactly one row carries `aria-selected="true"` at a time. Here `"eng"`
                is pre-selected.
            """),
            await _org_table_single.render(
                is_expanded=_EXPANDED_ORG_IDS, is_selected=_SINGLE_SELECTED_IDS
            ),
            c.markdown("""
                ### Multi-select

                Any subset of rows can be selected. Here three rows across different
                branches are pre-selected to show the visual state for non-contiguous
                selection.
            """),
            await _org_table_multi.render(
                is_expanded=_EXPANDED_ORG_IDS, is_selected=_MULTI_SELECTED_IDS
            ),
            c.code(
                [
                    ("single", src.text("org_table_single"), "python"),
                    ("multi", src.text("org_table_multi"), "python"),
                ]
            ),
            c.markdown("""
                ## Empty state

                Both tables accept an `empty_state` parameter that controls
                what's rendered beneath the column header when the source
                returns no rows. The value is either a static `y.Node` or a
                sync/async callable receiving the current `Query` — useful
                for distinguishing "no items yet" from "no matches for the
                active filter". When unset, the default `"No items to
                display"` is rendered.

                ### Default

                No `empty_state` passed — the table falls back to the
                built-in `"No items to display"` message.
            """),
            await _table_empty_default.render(),
            c.markdown("""
                ### Query-aware callable

                The callback receives the current `Query`, so the message
                can react to whether a filter or sort is active. Open the
                filter drawer and apply a filter to see the message change.
            """),
            await _table_empty_dynamic.render(),
            c.code([("query-aware", src.text("empty_dynamic"), "python")]),
            c.markdown("""
                ### Hierarchical — static node

                On `HierarchicalDataTable`, the empty-state row is rendered
                only when the **top-level** fetch returns no items; empty
                sub-trees stay empty (they don't show a placeholder).
            """),
            await _org_table_empty.render(),
            c.markdown("""
                ## Auto-derived columns from a Pydantic model

                Pass a `type=` argument and the table walks the model's fields
                via `read_column_annotations`. Each field's `Annotated[…, c.annotations.*Column(…)]`
                marker (or its bare Python type, if no marker is set) becomes a
                `Column[T]`. Default cell renderers handle the primitive types
                — `str` / `int` / `float`, `bool` → "yes"/"no", `date` → ISO,
                `Enum` → its `.value`. `None` renders as an empty cell.

                The `Release` model below pins explicit labels and widths on
                some fields, leaves `status` to be derived from the
                `ReleaseStatus` enum (auto-built `ChoiceFilter`), and uses
                `HiddenColumn` on `id` so the row id never renders but stays in
                the filter drawer as a numeric filter. A single explicit
                `Column` ("actions") is appended via the `columns` tuple — that
                merge is "derived first, explicit appended" by default.
            """),
            await _release_table.render(),
            c.code(
                [
                    ("model", src.text("release_model"), "python"),
                    ("actions", src.text("release_actions"), "python"),
                    ("table", src.text("release_table"), "python"),
                ]
            ),
            c.markdown("""
                ### Reordering with `columns_order`

                Same model, same data, but `columns_order` is set. It acts as a
                whitelist *and* the authoritative order — columns whose key is
                not listed are dropped from everything (render, filter drawer,
                sort). In this variant `id` is excluded entirely, `status` and
                `is_lts` are pulled to the front, and the explicit `actions`
                column is positioned by name like any other.
            """),
            await _release_table_reordered.render(),
            c.code([("table", src.text("release_reordered"), "python")]),
            c.markdown("""
                ### DateColumn formatting

                `DateColumn.format` accepts four variants:

                * `IsoDateFormat()` — `2024-04-25` (default).
                * `PatternDateFormat(pattern=…)` — any `strftime` pattern,
                  plus `.short()` / `.long()` / `.numeric()` shortcuts.
                * `LocalizedDateFormat(width=…)` — `babel`-formatted, locale
                  picked from the request's `Accept-Language` header via
                  `pyhx.core.primitives.negotiate_locale`. Default supported
                  set is `en / de / it / fr` (override in `[app.pyhx.core]`).
                * `RelativeDateFormat()` — server-rendered relative time via
                  `humanize` (frozen at render, not ticking).

                Each row below shows the same `released` date rendered four
                ways. Reload with a different browser language (or set
                `Accept-Language` manually) to see the `Localized` column
                shift.
            """),
            await _release_dates_table.render(),
            c.code(
                [
                    ("model", src.text("release_dates_model"), "python"),
                    ("table", src.text("release_dates_table"), "python"),
                ]
            ),
            c.markdown("""
                ### DateTimeColumn formatting

                `DateTimeColumn` is the `datetime` counterpart of `DateColumn`
                — it renders the date **and** the time-of-day. A bare
                `datetime` field auto-derives one, defaulting to
                `RelativeDateFormat` (the `Auto` column below). `format=`
                accepts:

                * `RelativeDateFormat()` — `"3 hours ago"` (**the default**).
                * `IsoDateFormat()` — `2024-04-25T14:30:45+00:00`.
                * `PatternDateFormat(pattern=…)` — any `strftime` pattern,
                  including time (`"%d %b %Y %H:%M:%S"`).
                * `LocalizedDateTimeFormat(width=…)` — `babel`-formatted date
                  **and** time (`width="medium"` includes seconds), locale
                  from `Accept-Language`, instant moved into the viewer's
                  timezone (`hx_tz` cookie) first.

                Filtering is day-granularity: the drawer's date picker matches
                a datetime by its calendar date.
            """),
            await _release_timestamps_table.render(),
            c.code(
                [
                    ("model", src.text("release_timestamps_model"), "python"),
                    ("table", src.text("release_timestamps_table"), "python"),
                ]
            ),
            c.markdown("""
                ### NumericColumn formatting

                `NumericColumn.format` accepts four variants:

                * `IsoNumberFormat()` — raw `str(value)`, opt-in for debug.
                * `PatternNumberFormat(spec=…)` — Python format-spec, with
                  `.thousands()` / `.thousands_decimals()` / `.scientific()` /
                  `.percent()` shortcuts. Locale-independent.
                * `LocalizedNumberFormat(width=…)` — locale-aware via
                  `Accept-Language`. **This is the default for `NumericColumn`**,
                  so any auto-derived numeric column starts grouped (`1,234,567`
                  → `1.234.567` → `1 234 567` depending on locale). `width="compact"`
                  gives `"18M"` / `"18 Mio."` / `"18 M"`.
                * `CurrencyNumberFormat(currency=…)` — full locale-correct money
                  output (symbol placement, separators).

                Reload with a different browser language to see the locale and
                currency columns shift.
            """),
            await _release_numbers_table.render(),
            c.code(
                [
                    ("model", src.text("release_numbers_model"), "python"),
                    ("table", src.text("release_numbers_table"), "python"),
                ]
            ),
            lorem_ipsum(paragraphs=20),
        ]
    )
