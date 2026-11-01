"""Page header demo.

A simple page that renders the :func:`pyhx.components.page_header`
component above a long content area, so the scroll behaviour of the
header within the app shell can be verified.
"""

import htpy as y
import pyhx.components as c

from pydantic import BaseModel

from pyhx.core.primitives import styles
from pyhx.core import WebAppRouter, PageResponse
from pyhx.page_templates import AppShell
from pyhx.utils import lorem_ipsum

router = WebAppRouter()


class Team(BaseModel):
    id: int
    name: str
    points: int
    goals_for: int
    goals_against: int


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
]


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


_table = c.DataTable[Team](
    routes=router, name="bundesliga", source=TEAMS, columns=COLUMNS
)

# Separate instance for the page_section demo (own fragment routes / DOM ids).
_section_table = c.DataTable[Team](
    routes=router, name="bundesliga-section", source=TEAMS, columns=COLUMNS
)


def _build_page_header(*, with_breadcrumbs: bool) -> y.Node:
    return c.page_header(
        breadcrumbs=c.page_header.breadcrumbs(
            y.a(href="/")["Home"],
            "The current page",
        ) if with_breadcrumbs else None,
        title=y.h1["Page Header"],
        actions=y.fragment[
            c.pill("Some Status"),
            c.button("Test 2"),
            c.button("Test", appearance="primary"),
        ],
    )


@router.fragment.get("/page-header/with-breadcrumbs")
async def page_header_with_breadcrumbs() -> y.Node:
    return _build_page_header(with_breadcrumbs=True)


@router.fragment.get("/page-header/without-breadcrumbs")
async def page_header_without_breadcrumbs() -> y.Node:
    return _build_page_header(with_breadcrumbs=False)


@router.page("/page-header", title="Page Header")
async def page_header() -> PageResponse:
    return PageResponse(
        node=y.fragment[
            _build_page_header(with_breadcrumbs=True),
            c.container(
                y.fragment[
                    y.div(**styles("mb-md", class_="hx-page-header-demo__toggles"))[
                        c.button(
                            "Show breadcrumbs",
                            hx_get=page_header_with_breadcrumbs.url(),
                            hx_target=".hx-page-header",
                            hx_swap="outerHTML",
                        ),
                        " ",
                        c.button(
                            "Hide breadcrumbs",
                            hx_get=page_header_without_breadcrumbs.url(),
                            hx_target=".hx-page-header",
                            hx_swap="outerHTML",
                        ),
                    ],
                    y.p[
                        "The page header above sits at the top of the main column. ",
                        "The content below is intentionally long so the page scrolls.",
                    ],
                    await _table.render(),
                    y.hr,
                    lorem_ipsum(paragraphs=10),
                ],
                width="wide",
            ),
            # page_section siblings of the page_header: their width tracks the
            # header's `wide` container, and each section header sticks directly
            # below the page header while scrolling.
            c.page_section(
                title=y.h2["Standings"],
                actions=y.fragment[
                    c.pill("Season 23/24"),
                    c.button("Export"),
                ],
                content=y.fragment[
                    y.p[
                        "A data table inside a section: its sticky header pins "
                        "below this section header (not behind it)."
                    ],
                    await _section_table.render(),
                ],
            ),
            c.page_section(
                title=y.h2["Notes"],
                actions=c.button("Add note"),
                content=lorem_ipsum(paragraphs=20),
            ),
        ],
        page_template=AppShell(mode="app", compact_main_navigation=False)
    )
