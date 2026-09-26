import asyncio

from pydantic import BaseModel

from pyhx.core.fragment import FragmentFactory
from pyhx.core.page import PageDecoratorFactory
from pyhx.core.request_context import RequestContext, set_request_context
from pyhx.components.data.data_table import DataTable


class Person(BaseModel):
    name: str
    age: int


class _Routes:
    def __init__(self) -> None:
        self.fragment = FragmentFactory([])
        self.page = PageDecoratorFactory([])


PEOPLE = [Person(name="Ann", age=30), Person(name="Bob", age=25)]


def _render(**kwargs) -> str:
    set_request_context(RequestContext())
    table = DataTable(
        routes=_Routes(), name="people", source=PEOPLE, type=Person, **kwargs
    )
    return str(asyncio.run(table.render()))


def test_scrollable_wraps_table_in_scroll_container():
    html = _render(scrollable=True)
    assert "hx-table__scroll-container" in html


def test_not_scrollable_by_default():
    html = _render()
    assert "hx-table__scroll-container" not in html


def test_scrollable_keeps_wrapper_id_and_oob_for_re_render():
    # The htmx OOB swap target (wrapper id + hx-swap-oob) must stay on the
    # outer wrapper, not migrate onto the scroll container — otherwise a
    # re-render would replace the scroll box and lose the toolbar.
    html = _render(scrollable=True)
    assert 'id="people_wrapper"' in html
    assert "hx-swap-oob" in html
    # wrapper (with the id) comes before the scroll container in source order
    assert html.index("people_wrapper") < html.index("hx-table__scroll-container")
