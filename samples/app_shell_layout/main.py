"""App Shell layout sample.

Run with::

    poetry run fastapi dev samples/app_shell_layout/main.py

The home page links to every demo; the side nav exposes the layout
scenarios as a separate group. Pages are declared in sibling modules
under :mod:`samples.app_shell_layout.pages` and attached via
:class:`WebAppRouter`.
"""

import htpy as y
import pyhx.components as c

from pyhx.core import WebApp
from pyhx.page_templates import AppShell

from .pages import (
    data_page,
    drawer,
    mobile_preview,
    page_header,
    page_navigation,
    scenarios,
    table_view,
)


hx = WebApp(
    title="App Shell Layout",
    default_page_template=AppShell(mode="app", compact_main_navigation=False),
)

hx.include_router(scenarios.router)
hx.include_router(mobile_preview.router)
hx.include_router(drawer.router)
hx.include_router(page_header.router)
hx.include_router(page_navigation.router)
hx.include_router(table_view.router)
hx.include_router(data_page.router)


@hx.page("/", title="Home")
async def home() -> y.Node:
    return c.container(
        y.article[
            y.h1["App Shell Layout Verification"],
            y.p[
                "Each sample exercises a specific app-shell layout scenario. ",
                "Resize the viewport below 768px on any sample to see the responsive drawer pattern, ",
                "or open the ",
                y.a(href=mobile_preview.mobile_preview.url())["mobile preview"],
                " to view the samples at iPhone width without resizing the browser.",
            ],
            y.ul[
                y.li[
                    y.a(href=scenarios.long_main_content.url())["Long Main Content"],
                    " — main longer than sidebar",
                ],
                y.li[
                    y.a(href=scenarios.long_nav_content.url())["Long Navigation Content"],
                    " — sidebar longer than main",
                ],
                y.li[
                    y.a(href=scenarios.long_content.url())["Long Content"],
                    " — both columns longer than viewport",
                ],
                y.li[
                    y.a(href=scenarios.app_mode.url())["App Mode"],
                    " — same layout, footer pinned to viewport bottom",
                ],
                y.li[
                    y.a(href=page_navigation.overview.url())["Page Navigation"],
                    " — page header with secondary navigation across four pages",
                ],
            ],
        ],
        width="medium",
    )


hx.navigation.set(
    {
        "": [
            hx.nav_item(home, icon="home", full_match=True),
            hx.nav_item(mobile_preview.mobile_preview, icon="smartphone"),
            hx.nav_item(drawer.drawer),
            hx.nav_item(page_header.page_header),
            hx.nav_item(page_navigation.overview, label="Page Navigation"),
            hx.nav_item(table_view.table_view),
            hx.nav_item(data_page.page, label="Data Page"),
        ],
        "Scenarios": [
            hx.nav_item(scenarios.long_content),
            hx.nav_item(scenarios.long_main_content),
            hx.nav_item(scenarios.long_nav_content),
            hx.nav_item(scenarios.app_mode),
        ],
    }
)


app = hx.create_app()
