"""``can_create`` is resolved per request: a producer gates the create button, drawer and submit."""

import asyncio

from pydantic import BaseModel

from pyhx.components.data.data_page import DataPage
from pyhx.components.data.sources.query import Query
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.core.fragment import FragmentFactory
from pyhx.core.page import PageDecoratorFactory


class Person(BaseModel):
    id: int
    name: str


class _Routes:
    def __init__(self) -> None:
        self.fragment = FragmentFactory([])
        self.page = PageDecoratorFactory([])


def _page(can_create) -> tuple[DataPage, SimpleDataSource]:
    source = SimpleDataSource([Person(id=1, name="Ann")])
    page = DataPage(routes=_Routes(), path="/people", source=source, type=Person, can_create=can_create)
    return page, source


def _create_button_shown(page: DataPage) -> bool:
    return page.section.open_create_form.url() in str(asyncio.run(page.section.render_actions()))


def test_a_producer_returning_false_hides_the_create_button():
    async def not_allowed() -> bool:
        return False

    page, _ = _page(not_allowed)

    assert not _create_button_shown(page)


def test_a_producer_returning_true_shows_the_create_button():
    page, _ = _page(lambda: True)

    assert _create_button_shown(page)


def test_a_plain_bool_still_works():
    assert _create_button_shown(_page(True)[0])
    assert not _create_button_shown(_page(False)[0])


def test_drawer_and_submit_are_refused_when_creating_is_not_allowed():
    page, source = _page(lambda: False)

    assert asyncio.run(page.section._on_create_item_click()) is None
    assert asyncio.run(page.section._on_create_form_submit(Person(id=2, name="Bob"))) is None
    assert asyncio.run(source.count(Query())) == 1
