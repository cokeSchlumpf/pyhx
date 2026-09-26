"""Page-header navigation demo — one area, four pages, one navigation.

Shows the ``navigation`` argument of :func:`pyhx.components.page_header`:
a secondary navigation rendered inside the page header, used to switch
between related pages of the same application area.

All four pages share :func:`_navigation`, which builds the same link list
for every page and marks exactly one item active. The pages differ in what
they put *around* that navigation, so the demo covers the combinations that
matter:

* **Overview** — breadcrumbs, title, actions and navigation (the full header).
* **Hotspots** — a ``DataTable`` inside a ``page_section``: the section header
  pins below the page header *including* its navigation row, and the table
  header pins below the section header.
* **Suppliers** — navigation without breadcrumbs and without actions, above a
  ``DataTable`` placed directly in the page: its sticky header pins right
  below the navigation row.
* **Settings** — navigation above a long page, to verify that the header
  (title row *and* navigation row) stays pinned while the page scrolls.

Both tables are long enough to scroll, because the sticky offsets
(``--hx-table--sticky-top`` and ``--page-section--top``) are derived from the
shared ``--page-header--height`` token, which grows by the navigation row.
"""

from itertools import product

import htpy as y
import pyhx.components as c

from pydantic import BaseModel

from pyhx.core import WebAppRouter
from pyhx.utils import lorem_ipsum


router = WebAppRouter()


# --- Hotspots (table inside a page_section) ---


class Hotspot(BaseModel):
    id: int
    stage: str
    topic: str
    severity: str
    score: int


_STAGES = (
    "Raw materials",
    "Manufacturing",
    "Logistics",
    "Retail",
    "Use phase",
    "End of life",
)

_TOPICS = (
    "Water use",
    "Land use",
    "Energy mix",
    "Waste",
    "Emissions",
    "Packaging",
)

# One row per stage/topic combination (36) — enough to scroll the page so the
# sticky section and table headers can be observed.
HOTSPOTS: list[Hotspot] = [
    Hotspot(
        id=i,
        stage=stage,
        topic=topic,
        severity=("Low", "Medium", "High")[i % 3],
        score=30 + (i * 7) % 65,
    )
    for i, (stage, topic) in enumerate(product(_STAGES, _TOPICS), start=1)
]


HOTSPOT_COLUMNS: tuple[c.Column[Hotspot], ...] = (
    c.Column(
        key="stage",
        label="Stage",
        header="Stage",
        render=lambda h: h.stage,
        width=c.Flex(weight=2),
        filter_type=c.TextFilter(),
    ),
    c.Column(
        key="topic",
        label="Topic",
        header="Topic",
        render=lambda h: h.topic,
        width=c.Flex(weight=2),
        filter_type=c.TextFilter(),
    ),
    c.Column(
        key="severity",
        label="Severity",
        header="Severity",
        render=lambda h: h.severity,
        width=c.Flex(weight=1, min_width="120px"),
        filter_type=c.TextFilter(),
    ),
    c.Column(
        key="score",
        label="Score",
        header="Score",
        render=lambda h: str(h.score),
        width=c.Flex(weight=1, min_width="120px"),
        filter_type=c.NumericFilter(),
    ),
)


_hotspot_table = c.DataTable[Hotspot](
    routes=router, name="hotspots", source=HOTSPOTS, columns=HOTSPOT_COLUMNS
)


# --- Suppliers (table directly below the page header) ---


class Supplier(BaseModel):
    id: int
    name: str
    country: str
    category: str
    tier: str
    spend: int


_SUPPLIER_BASES = (
    ("Ardent Metals", "Germany", "Metals"),
    ("Baltic Textiles", "Poland", "Textiles"),
    ("Cortez Chemicals", "Spain", "Chemicals"),
    ("Delta Packaging", "Netherlands", "Packaging"),
    ("Elbe Logistics", "Germany", "Logistics"),
    ("Fjord Components", "Norway", "Components"),
    ("Granada Plastics", "Spain", "Plastics"),
    ("Helvetia Precision", "Switzerland", "Components"),
    ("Ionic Electronics", "Czechia", "Electronics"),
    ("Jura Coatings", "France", "Chemicals"),
)

_SUPPLIER_SITES = ("Nord", "Süd", "Ost", "West")

SUPPLIERS: list[Supplier] = [
    Supplier(
        id=i,
        name=f"{name} {site}",
        country=country,
        category=category,
        tier=f"Tier {i % 3 + 1}",
        spend=120_000 + (i * 37_000) % 880_000,
    )
    for i, ((name, country, category), site) in enumerate(
        product(_SUPPLIER_BASES, _SUPPLIER_SITES), start=1
    )
]


SUPPLIER_COLUMNS: tuple[c.Column[Supplier], ...] = (
    c.Column(
        key="name",
        label="Supplier",
        header="Supplier",
        render=lambda s: s.name,
        width=c.Flex(weight=3),
        filter_type=c.TextFilter(),
    ),
    c.Column(
        key="country",
        label="Country",
        header="Country",
        render=lambda s: s.country,
        width=c.Flex(weight=2),
        filter_type=c.TextFilter(),
    ),
    c.Column(
        key="category",
        label="Category",
        header="Category",
        render=lambda s: s.category,
        width=c.Flex(weight=2),
        filter_type=c.TextFilter(),
    ),
    c.Column(
        key="tier",
        label="Tier",
        header="Tier",
        render=lambda s: s.tier,
        width=c.Flex(weight=1, min_width="100px"),
        filter_type=c.TextFilter(),
    ),
    c.Column(
        key="spend",
        label="Spend (EUR)",
        header="Spend (EUR)",
        render=lambda s: f"{s.spend:,}".replace(",", "'"),
        width=c.Flex(weight=1, min_width="140px"),
        filter_type=c.NumericFilter(),
    ),
)


_supplier_table = c.DataTable[Supplier](
    routes=router, name="suppliers", source=SUPPLIERS, columns=SUPPLIER_COLUMNS
)


def _navigation(active: str) -> y.Node:
    """Build the area's navigation, marking ``active`` as the current page.

    Every page renders the same links through ``page_header.navigation`` and
    passes its own key, so the active item — the one that gets
    ``aria-current="page"`` — is the only difference between them.
    """
    return c.page_header.navigation(
        *[
            c.page_header.nav_item(label, href=href, active=key == active)
            for key, label, href in (
                ("overview", "Overview", overview.url()),
                ("hotspots", "Hotspots", hotspots.url()),
                ("suppliers", "Suppliers", suppliers.url()),
                ("settings", "Settings", settings.url()),
            )
        ],
        aria_label="Value chain views",
    )


def _breadcrumbs(current: str) -> y.Node:
    return c.page_header.breadcrumbs(
        y.a(href="/")["Home"],
        y.a(href=overview.url())["Value Chain"],
        current,
    )


@router.page("/page-navigation", title="Page Navigation")
async def overview() -> y.Node:
    return y.fragment[
        c.page_header(
            breadcrumbs=_breadcrumbs("Overview"),
            title=y.h1["Value Chain"],
            actions=y.fragment[
                c.pill("Draft"),
                c.button("Share"),
                c.button("Publish", appearance="primary"),
            ],
            navigation=_navigation("overview"),
        ),
        c.container(
            y.article[
                y.p[
                    "The navigation row below the title switches between the pages of ",
                    "this area. It lives ",
                    y.em["inside"],
                    " the page header, so the header's bottom border stays below the ",
                    "navigation and the active indicator sits directly on top of it.",
                ],
                y.p[
                    "The row is built with ",
                    y.code["page_header.navigation(...)"],
                    " from one ",
                    y.code["page_header.nav_item(...)"],
                    " per page; the item marked ",
                    y.code["active"],
                    " gets ",
                    y.code['aria-current="page"'],
                    ". Extra attributes on an item are forwarded to its anchor, ",
                    "so a link can just as well swap a fragment via htmx instead ",
                    "of navigating.",
                ],
                y.p[
                    "The main navigation in the sidebar keeps highlighting the area while ",
                    "you move between the pages, because all of them share the ",
                    y.code["/page-navigation"],
                    " path prefix.",
                ],
                y.p[
                    "Scroll the ",
                    y.a(href=suppliers.url())["Suppliers"],
                    " and ",
                    y.a(href=hotspots.url())["Hotspots"],
                    " pages to check that sticky table headers pin below the taller ",
                    "header — directly on the page and inside a section.",
                ],
                y.hr,
                lorem_ipsum(paragraphs=8),
            ],
            width="wide",
        ),
    ]


@router.page("/page-navigation/hotspots", title="Hotspots")
async def hotspots() -> y.Node:
    return y.fragment[
        c.page_header(
            breadcrumbs=_breadcrumbs("Hotspots"),
            title=y.h1["Hotspots"],
            actions=y.fragment[
                c.pill(f"{len(HOTSPOTS)} hotspots"),
                c.button("Export"),
            ],
            navigation=_navigation("hotspots"),
        ),
        c.container(
            y.p[
                "The table below sits inside a ",
                y.code["page_section"],
                ". Scrolling stacks three sticky rows: the app-shell header, the page ",
                "header (title row plus navigation row), then the section header — and ",
                "the table header pins directly below all of them.",
            ],
            width="wide",
        ),
        c.page_section(
            title=y.h2["By value chain stage"],
            actions=c.button("Add hotspot"),
            content=await _hotspot_table.render(),
        ),
        c.page_section(
            title=y.h2["Notes"],
            content=lorem_ipsum(paragraphs=12),
        ),
    ]


@router.page("/page-navigation/suppliers", title="Suppliers")
async def suppliers() -> y.Node:
    return y.fragment[
        c.page_header(
            title=y.h1["Suppliers"],
            navigation=_navigation("suppliers"),
        ),
        c.container(
            y.fragment[
                y.p[
                    "The same navigation on a minimal header: no breadcrumbs, no actions. ",
                    "The navigation row keeps its place at the bottom of the header, so the ",
                    "pages of an area stay visually aligned even when their headers carry ",
                    "different content.",
                ],
                y.p[
                    "The table sits directly in the page, without a ",
                    y.code["page_section"],
                    " in between. Scroll it: its sticky header pins below the navigation ",
                    "row, because the app shell derives ",
                    y.code["--hx-table--sticky-top"],
                    " from the shared ",
                    y.code["--page-header--height"],
                    " token, which grows when navigation is present.",
                ],
                await _supplier_table.render(),
                y.hr,
                lorem_ipsum(paragraphs=6),
            ],
            width="wide",
        ),
    ]


@router.page("/page-navigation/settings", title="Settings")
async def settings() -> y.Node:
    return y.fragment[
        c.page_header(
            breadcrumbs=_breadcrumbs("Settings"),
            title=y.h1["Settings"],
            actions=c.button("Save", appearance="primary"),
            navigation=_navigation("settings"),
        ),
        c.container(
            y.article[
                y.p[
                    "Scroll this page: the title row and the navigation row stick together ",
                    "below the app-shell header, and the navigation stays reachable while ",
                    "the content scrolls past.",
                ],
                y.hr,
                lorem_ipsum(paragraphs=30),
            ],
            width="wide",
        ),
    ]
