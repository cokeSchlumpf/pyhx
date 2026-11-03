"""Page sections in the canvas design.

Included by :mod:`samples.canvas_layout.main`. ``/page-sections`` is a page with
more than one table: a page header, then one ``page_section`` per table. In the
canvas design a section is a heading on the canvas (no band, no line, not
sticky), and a ``DataTable`` in it is the same white card as the table of a
``DataPage``.
"""

import htpy as y

import pyhx.components as c
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.core import WebAppRouter
from samples.canvas_layout.data_page import Case, CaseStatus, _cases

router = WebAppRouter()

_open = [case for case in _cases() if case.status is not CaseStatus.closed]
_closed = [case for case in _cases() if case.status is CaseStatus.closed]

open_cases = c.DataTable[Case](
    routes=router,
    name="page-sections-open",
    source=SimpleDataSource(_open),
    type=Case,
    footer=c.TableFooter(label=("{n} Fall", "{n} Fälle")),
)

closed_cases = c.DataTable[Case](
    routes=router,
    name="page-sections-closed",
    source=SimpleDataSource(_closed),
    type=Case,
    footer=c.TableFooter(label=("{n} Fall", "{n} Fälle")),
)


@router.page("/page-sections", title="Page sections")
async def page_sections() -> y.Node:
    return y.fragment[
        c.page_header(
            breadcrumbs=c.page_header.breadcrumbs(y.a(href="/")["Canvas Layout"], "Page sections"),
            title=y.h1["Übersicht"],
            actions=c.button("Exportieren", variant="outline"),
        ),
        c.page_section(
            title=y.h2["Offene Fälle"],
            actions=y.span["neu, in Bearbeitung, Eingabe erforderlich"],
            content=await open_cases.render(),
        ),
        c.page_section(
            title=y.h2["Abgeschlossene Fälle"],
            content=await closed_cases.render(),
        ),
    ]
