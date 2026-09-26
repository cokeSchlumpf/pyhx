import asyncio

from fastapi import Request
from pydantic import BaseModel

from pyhx.core.fragment import FragmentFactory
from pyhx.core.page import PageDecoratorFactory
from pyhx.core.request_context import RequestContext, set_request_context
from pyhx.components.data.data_table import DataTable
from pyhx.components.data.sources.query import Query
from pyhx.components.data.sources.sort import SortOrder


class Person(BaseModel):
    name: str
    age: int


class _Routes:
    def __init__(self) -> None:
        self.fragment = FragmentFactory([])
        self.page = PageDecoratorFactory([])


PEOPLE = [Person(name="Ann", age=30), Person(name="Bob", age=25)]


def _install_htmx_request() -> None:
    """Seed a RequestContext carrying the ``HX-Request`` header htmx sends
    on every fragment call it issues. the signal ``update_query_fragment``
    gates on to avoid rendering a literal, visible duplicate during a plain
    page load 
    """
    request = Request({"type": "http", "headers": [(b"hx-request", b"true")]})
    set_request_context(RequestContext(request=request))


def _clear_request() -> None:
    set_request_context(RequestContext())


def _render(**kwargs) -> str:
    _clear_request()
    table = DataTable(
        routes=_Routes(), name="people", source=PEOPLE, type=Person, **kwargs
    )
    return str(asyncio.run(table.render()))


def test_enabled_by_default_shows_sort_and_filter_controls():
    html = _render()
    assert "table-header-click" in html          # sortable header link
    assert "/_components/filter-drawer/" in html  # filter drawer button
    assert "clear-sort-and-filter" in html        # clear button


def test_disabled_hides_sort_and_filter_controls():
    html = _render(enable_sort_and_filter=False)
    assert "table-header-click" not in html
    assert "/_components/filter-drawer/" not in html
    assert "clear-sort-and-filter" not in html


def test_disabled_keeps_header_text_and_resizer():
    html = _render(enable_sort_and_filter=False)
    assert "Name" in html                          # header label still rendered
    assert "hx-table__col-resizer" in html         # resize handle preserved
    assert "toggle_fullscreen" in html             # maximize button preserved


def test_renders_via_table_primitive():
    html = _render()
    assert "hx-table__wrapper" in html
    assert 'class="hx-table"' in html
    assert "hx-data-table" not in html  # old markup fully gone


def _table_with_probe(**kwargs) -> tuple[DataTable, list[Query]]:
    seen: list[Query] = []

    async def probe(query: Query):
        seen.append(query)
        return "PROBE_MARKER"

    table = DataTable(
        routes=_Routes(),
        name="people",
        source=PEOPLE,
        type=Person,
        update_query_fragment=probe,
        **kwargs,
    )
    return table, seen


def test_no_hook_by_default_omits_extra_node():
    html = _render()
    assert "PROBE_MARKER" not in html


def test_update_query_fragment_skipped_on_plain_page_load():
    """Regression test: a hook is wired, but this is a plain (non-htmx)
    render, for example the very first full-page paint. There's no htmx JS
    running yet to swap an ``hx-swap-oob``-tagged node into place, so
    firing the hook here would render a second, literal, visible copy of
    whatever it returns instead of updating the existing one. Must stay
    silent until an actual htmx request comes in.
    """
    _clear_request()
    table, seen = _table_with_probe()
    query = Query(sort=[SortOrder(key="name", order="asc")])
    html = str(asyncio.run(table.render(query=query)))
    assert "PROBE_MARKER" not in html
    assert seen == []


def test_update_query_fragment_fires_on_render_with_the_current_query():
    _install_htmx_request()
    try:
        table, seen = _table_with_probe()
        query = Query(sort=[SortOrder(key="name", order="asc")])
        html = str(asyncio.run(table.render(query=query)))
        assert "PROBE_MARKER" in html
        assert seen == [query]
    finally:
        _clear_request()


def test_update_query_fragment_fires_via_clear_sort_and_filter_fragment():
    """Confirms the hook fires no matter which control triggers a re-render. All three
    query-mutating fragments funnel through the same ``_render_from_state``,
    so this exercises the toolbar's own "x" clear icon path directly.
    """
    _install_htmx_request()
    try:
        table, seen = _table_with_probe()
        response = asyncio.run(table.clear_sort_and_filter_fragment.render())
        assert "PROBE_MARKER" in str(response.node)
        assert seen == [Query()]
    finally:
        _clear_request()


def test_update_query_fragment_fires_via_table_header_click_fragment():
    """Same as above, for the column-header sort-toggle path."""
    _install_htmx_request()
    try:
        table, seen = _table_with_probe()
        response = asyncio.run(
            table.table_header_click_fragment.render(column_key="name")
        )
        assert "PROBE_MARKER" in str(response.node)
        assert seen == [Query(sort=[SortOrder(key="name", order="asc")])]
    finally:
        _clear_request()
