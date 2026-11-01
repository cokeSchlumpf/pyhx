"""Quick filters, search and URL parameters through DataSection and DataPage (T-008)."""

import re
from typing import Annotated

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

import pyhx.components.data.annotations as a
from pyhx.components.data.data_page import DataPage
from pyhx.components.data.data_section import DataSection
from pyhx.components.data.quick_filter import QuickFilter, QuickFilters, TableSearch
from pyhx.components.data.sources.filter import Condition, TextChoiceEquals
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.components.data.sources.simple_hierarchical_data_source import (
    SimpleHierarchicalDataSource,
)
from pyhx.core import WebApp


class Person(BaseModel):
    id: Annotated[str, a.HiddenColumn(), a.HiddenField()]
    name: Annotated[str, a.TextColumn(label="Name", searchable=True)]
    team: Annotated[str, a.TextColumn(label="Team")]


PEOPLE = [
    Person(id="1", name="Ann", team="red"),
    Person(id="2", name="Bob", team="blue"),
]

RED = Condition(key="team", values=[TextChoiceEquals(value="red")])
QUICK_FILTERS = QuickFilters(
    presets=[
        QuickFilter(key="all", label="All"),
        QuickFilter(key="red", label="Red", filter=[RED]),
    ]
)


def _client(**kwargs) -> tuple[TestClient, DataPage]:
    hx = WebApp()
    page = DataPage(
        routes=hx,
        path="/people",
        source=SimpleDataSource(list(PEOPLE)),
        type=Person,
        **kwargs,
    )
    return TestClient(hx.create_app()), page


def _filter_sort_button(text: str) -> str:
    match = re.search(
        r"<button[^>]*>Filter &amp; Sort</button>|<button[^>]*>Filter & Sort</button>",
        text,
    )
    assert match
    return match.group(0)


def test_options_reach_the_table():
    _, page = _client(
        table_quick_filters=QUICK_FILTERS,
        table_search=TableSearch(label="Find"),
        table_url_param_keys=["team"],
    )
    table = page.section.table
    assert table.quick_filters is QUICK_FILTERS
    assert table.search.label == "Find"
    assert table.url_param_keys == ["team"]


def test_deep_link_opens_the_page_filtered():
    client, _ = _client(table_quick_filters=QUICK_FILTERS, table_search=TableSearch())
    text = client.get("/people?view=red").text
    assert "hx-table__filter-bar" in text
    assert ">Ann<" in text and ">Bob<" not in text
    assert 'type="search"' in text

    text = client.get("/people?q=bo").text
    assert ">Ann<" not in text and ">Bob<" in text


def test_url_param_keys_deep_link():
    client, _ = _client(table_url_param_keys=["team"])
    text = client.get("/people?team=blue").text
    assert ">Ann<" not in text and ">Bob<" in text


def test_filter_sort_button_is_highlighted_when_the_url_filters():
    client, _ = _client(table_quick_filters=QUICK_FILTERS)
    assert "primary" in _filter_sort_button(client.get("/people?view=red").text)
    assert "primary" not in _filter_sort_button(client.get("/people").text)


class Node(BaseModel):
    id: str
    name: str
    parent: str | None = None


@pytest.mark.parametrize(
    "kwargs",
    [{"table_quick_filters": QUICK_FILTERS}, {"table_search": TableSearch()}],
)
def test_hierarchical_source_rejects_quick_filters_and_search(kwargs):
    with pytest.raises(TypeError, match="flat"):
        DataSection(
            routes=WebApp(),
            path="/nodes",
            source=SimpleHierarchicalDataSource([Node(id="1", name="root")]),
            type=Node,
            **kwargs,
        )


def test_hierarchical_source_takes_url_param_keys():
    section = DataSection(
        routes=WebApp(),
        path="/nodes",
        source=SimpleHierarchicalDataSource([Node(id="1", name="root")]),
        type=Node,
        table_url_param_keys=["name"],
    )
    assert section.table.filter_drawer.url_param_keys == ["name"]
