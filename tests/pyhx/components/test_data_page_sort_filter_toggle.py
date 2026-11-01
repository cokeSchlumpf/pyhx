import asyncio

from fastapi import Request
from pydantic import BaseModel

from pyhx.core.fragment import FragmentFactory
from pyhx.core.page import PageDecoratorFactory
from pyhx.core.request_context import RequestContext, set_request_context
from pyhx.components.data.data_page import DataPage
from pyhx.components.data.sources.query import Query
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.components.data.sources.sort import SortOrder


class Person(BaseModel):
    id: int
    name: str


class _Routes:
    def __init__(self) -> None:
        self.fragment = FragmentFactory([])
        self.page = PageDecoratorFactory([])


def _page(**kwargs) -> DataPage:
    return DataPage(
        routes=_Routes(),
        path="/people",
        source=SimpleDataSource([Person(id=1, name="Ann")]),
        type=Person,
        **kwargs,
    )


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


def test_flag_defaults_to_true_and_forwards_to_table():
    page = _page()
    assert page.section.enable_sort_and_filter is True
    assert page.section.table.enable_sort_and_filter is True


def test_flag_forwards_disabled_to_table():
    page = _page(table_enable_sort_and_filter=False)
    assert page.section.enable_sort_and_filter is False
    assert page.section.table.enable_sort_and_filter is False


def test_page_header_shows_filter_button_when_enabled():
    page = _page()  # can_create defaults to True
    html = str(asyncio.run(page.section.render_actions()))
    assert "/_components/filter-drawer/" in html


def test_page_header_hides_filter_button_when_disabled():
    page = _page(table_enable_sort_and_filter=False)
    html = str(asyncio.run(page.section.render_actions()))
    assert "/_components/filter-drawer/" not in html


def test_filter_sort_button_starts_neutral_on_first_paint():
    # render_actions() also includes the (always-primary) "Create Person"
    # button, so isolate just the filter/sort button's own tag before
    # asserting on its class list.
    page = _page()
    html = str(asyncio.run(page.section.render_actions()))
    start = html.index(f'id="{page.section.filter_sort_button_id}"')
    button_html = html[start : html.index("</button>", start)]
    assert "hx-button--neutral" in button_html
    assert "hx-button--primary" not in button_html


def test_filter_sort_button_highlights_for_an_active_query():
    page = _page()
    active = Query(sort=[SortOrder(key="name", order="asc")])
    html = str(asyncio.run(page.section._render_filter_sort_button(active)))
    assert f'id="{page.section.filter_sort_button_id}"' in html
    assert "hx-button--primary" in html


def test_table_is_wired_with_the_page_header_button_hook_when_enabled():
    page = _page()
    # Bound methods aren't `is`-identical across attribute accesses even when they wrap the same instance + function, so compare by equality instead.
    assert page.section.table.update_query_fragment == (
        page.section._render_filter_sort_button
    )


def test_table_is_not_wired_with_the_hook_when_disabled():
    page = _page(table_enable_sort_and_filter=False)
    assert page.section.table.update_query_fragment is None


def test_table_render_includes_the_highlighted_oob_button():
    """End-to-end: an interactive table update (here, via the public
    ``render()`` seam the filter drawer itself uses) carries a fresh,
    correctly-highlighted copy of the page-header button, tagged for an
    out-of-band swap. Only true for genuine htmx requests
    """
    _install_htmx_request()
    try:
        page = _page()
        active = Query(sort=[SortOrder(key="name", order="asc")])
        html = str(asyncio.run(page.section.table.render(query=active)))
        assert f'id="{page.section.filter_sort_button_id}"' in html
        assert "hx-button--primary" in html
        assert 'hx-swap-oob="outerHTML"' in html
    finally:
        _clear_request()



