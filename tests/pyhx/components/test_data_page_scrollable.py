import asyncio

from pydantic import BaseModel

from pyhx.core.fragment import FragmentFactory
from pyhx.core.page import PageDecoratorFactory
from pyhx.core.request_context import RequestContext, set_request_context
from pyhx.components.data.data_page import DataPage
from pyhx.components.data.data_section import DataSection
from pyhx.components.data.sources.simple_data_source import SimpleDataSource


class Person(BaseModel):
    id: int
    name: str


class _Routes:
    def __init__(self) -> None:
        self.fragment = FragmentFactory([])
        self.page = PageDecoratorFactory([])


def _source() -> SimpleDataSource:
    return SimpleDataSource([Person(id=1, name="Ann")])


def _section(**kwargs) -> DataSection:
    return DataSection(
        routes=_Routes(), path="/people", source=_source(), type=Person, **kwargs
    )


def _page(**kwargs) -> DataPage:
    return DataPage(
        routes=_Routes(), path="/people", source=_source(), type=Person, **kwargs
    )


def test_section_scrollable_defaults_false():
    assert _section().table.scrollable is False


def test_section_scrollable_forwards_to_table():
    assert _section(table_scrollable=True).table.scrollable is True


def test_page_is_always_scrollable():
    # DataPage exposes no scrollable toggle — a full-page table always scrolls.
    assert _page().section.table.scrollable is True


def test_page_content_has_single_container():
    # No double-nested container: exactly one hx-container wraps the table.
    set_request_context(RequestContext())
    html = str(asyncio.run(_page().render_content()))
    assert html.count('class="hx-container') == 1


def test_page_content_renders_scroll_container_by_default():
    set_request_context(RequestContext())
    html = str(asyncio.run(_page().render_content()))
    assert "hx-table__scroll-container" in html
