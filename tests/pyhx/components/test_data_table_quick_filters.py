"""Quick filters, search and URL parameters of DataTable (T-008)."""

import html
import json
import re
from enum import Enum
from typing import Annotated
from urllib.parse import parse_qs

import htpy as y
from fastapi.testclient import TestClient
from pydantic import BaseModel

import pyhx.components.data.annotations as a
from pyhx.components.data.data_table import DataTable
from pyhx.components.data.quick_filter import QuickFilter, QuickFilters, TableSearch
from pyhx.components.data.sources.filter import Condition, TextChoiceIn
from pyhx.components.data.sources.query import Query
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.components.data.sources.source import Page, ReadOnlyDataSource
from pyhx.components.view_model import Option
from pyhx.core import WebApp


class Status(str, Enum):
    new = "New"
    active = "Active"
    done = "Done"


STATUS_OPTIONS = [Option(label=s.value, value=s.value) for s in Status]


class Project(BaseModel):
    id: Annotated[str, a.HiddenColumn()]
    name: Annotated[str, a.TextColumn(label="Name", searchable=True)]
    owner: Annotated[str, a.TextColumn(label="Owner", searchable=True)]
    status: Annotated[
        Status,
        a.TextColumn(
            label="Status", filter=a.MultipleChoiceFilter(options=STATUS_OPTIONS)
        ),
    ]
    code: Annotated[str, a.TextColumn(label="Code")]


PROJECTS = [
    Project(id="1", name="Aurora", owner="Anna", status=Status.new, code="P-01"),
    Project(id="2", name="Borealis", owner="Ben", status=Status.active, code="P-02"),
    Project(id="3", name="Comet", owner="Anna", status=Status.active, code="P-03"),
    Project(id="4", name="Dune", owner="Dora", status=Status.done, code="P-04"),
]


def _status(*values: str) -> Condition:
    return Condition(key="status", values=[TextChoiceIn(values=list(values))])


QUICK_FILTERS = QuickFilters(
    presets=[
        QuickFilter(key="all", label="All"),
        QuickFilter(key="open", label="Open", filter=[_status("New", "Active")]),
        QuickFilter(key="done", label="Done", filter=[_status("Done")]),
    ],
    counts=True,
    label="Views",
)


class CountingSource(SimpleDataSource[Project]):
    def __init__(self, data: list[Project]) -> None:
        super().__init__(data)
        self.counted: list[Query] = []

    async def count(self, query: Query) -> int:
        self.counted.append(query)
        return await super().count(query)


class NoSearchSource(ReadOnlyDataSource[Project]):
    async def fetch(self, query: Query) -> Page[Project]:
        return Page(items=PROJECTS, total=len(PROJECTS))

    async def get_id(self, item: Project) -> str:
        return item.id

    async def find_by_id(self, id: str) -> Project | None:
        return None

    async def get_by_id(self, id: str) -> Project:
        raise KeyError(id)


def _app(**kwargs) -> tuple[TestClient, DataTable[Project]]:
    hx = WebApp()
    kwargs.setdefault("source", CountingSource(list(PROJECTS)))
    table = DataTable(routes=hx, name="projects", type=Project, **kwargs)

    @hx.page("/projects", title="Projects")
    async def page() -> y.Node:
        return await table.render()

    return TestClient(hx.create_app()), table


STATE = "projects_hx_table_state"


def _state(text: str) -> str:
    match = re.search(rf'name="{STATE}" value="([^"]*)"', text)
    assert match, "no table state in response"
    return html.unescape(match.group(1))


def _query(text: str) -> Query:
    return Query.model_validate(json.loads(_state(text))["query"])


def _names(text: str) -> list[str]:
    return [n for n in ("Aurora", "Borealis", "Comet", "Dune") if f">{n}<" in text]


def _checked(text: str) -> list[str]:
    return re.findall(r'value="(\w+)" checked', text)


def _url_params(text: str) -> tuple[list[str], dict[str, list[str]]]:
    keys = re.search(r'data-hx-url-param-keys="([^"]*)"', text)
    values = re.search(r'data-hx-url-params="([^"]*)"', text)
    assert keys and values
    return keys.group(1).split(","), parse_qs(html.unescape(values.group(1)))


def _post(client: TestClient, table: DataTable, page_text: str, **form: str) -> str:
    response = client.post(
        table.render_table_fragment.url(),
        data={STATE: _state(page_text), **form},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    return response.text


class TestRendering:
    def test_without_options_nothing_changes(self):
        client, _ = _app(source=list(PROJECTS), columns_order=["code"])
        text = client.get("/projects").text
        assert "hx-table__filter-bar" not in text
        assert "data-hx-url-param-keys" not in text

    def test_pills_are_a_labelled_radio_group_with_counts(self):
        client, _ = _app(quick_filters=QUICK_FILTERS)
        text = client.get("/projects").text
        assert 'role="radiogroup"' in text
        assert 'aria-label="Views"' in text
        assert "All 4" in text and "Open 3" in text and "Done 1" in text
        assert _checked(text) == ["all"]

    def test_no_count_calls_when_counts_are_off(self):
        source = CountingSource(list(PROJECTS))
        client, _ = _app(
            source=source,
            quick_filters=QuickFilters(presets=QUICK_FILTERS.presets),
        )
        text = client.get("/projects").text
        assert "All 4" not in text and ">All<" in text
        assert source.counted == []

    def test_source_without_count_shows_no_number(self):
        client, _ = _app(source=NoSearchSource(), quick_filters=QUICK_FILTERS)
        text = client.get("/projects").text
        assert ">All<" in text

    def test_search_field_needs_a_searchable_column_and_a_supporting_source(self):
        client, _ = _app(search=TableSearch(label="Find", placeholder="Name, owner"))
        text = client.get("/projects").text
        assert 'type="search"' in text
        assert "Find" in text and 'placeholder="Name, owner"' in text

        client, _ = _app(source=NoSearchSource())
        assert 'type="search"' not in client.get("/projects").text

        client, _ = _app(columns_order=["code", "status"])
        assert 'type="search"' not in client.get("/projects").text


class TestQuickFilterClick:
    def test_choosing_a_pill_filters_and_keeps_sort_and_search(self):
        client, table = _app(quick_filters=QUICK_FILTERS)
        page = client.get("/projects?q=anna").text
        text = _post(
            client, table, page, action="quick_filter", projects_quick_filter="open"
        )
        assert _names(text) == ["Aurora", "Comet"]
        assert _checked(text) == ["open"]
        query = _query(text)
        assert query.search == "anna"
        assert query.filter == [_status("New", "Active")]

    def test_unknown_preset_is_ignored(self):
        client, table = _app(quick_filters=QUICK_FILTERS)
        page = client.get("/projects").text
        text = _post(
            client, table, page, action="quick_filter", projects_quick_filter="nope"
        )
        assert _names(text) == ["Aurora", "Borealis", "Comet", "Dune"]

    def test_drawer_condition_on_the_preset_column_is_custom(self):
        client, table = _app(quick_filters=QUICK_FILTERS)
        state = {"query": Query(filter=[_status("Active")]).model_dump(mode="json")}
        text = client.post(
            table.render_table_fragment.url(),
            data={STATE: json.dumps(state)},
            headers={"HX-Request": "true"},
        ).text
        assert _checked(text) == []
        keys, values = _url_params(text)
        assert "view" in keys and "view" not in values


class TestSearch:
    def test_search_filters_and_preserves_the_field(self):
        client, table = _app(quick_filters=QUICK_FILTERS)
        page = client.get("/projects").text
        assert "hx-preserve" not in page
        text = _post(client, table, page, action="search", projects_search="  ANN ")
        assert _names(text) == ["Aurora", "Comet"]
        assert "hx-preserve" in text
        assert _query(text).search == "ANN"
        # counts follow the search
        assert "All 2" in text and "Open 2" in text and "Done 0" in text

    def test_empty_term_removes_the_search(self):
        client, table = _app()
        page = client.get("/projects?q=anna").text
        text = _post(client, table, page, action="search", projects_search="")
        assert _query(text).search is None
        assert len(_names(text)) == 4

    def test_search_keys_come_from_the_columns_not_the_state(self):
        client, table = _app()
        state = {"query": {"search": "P-0", "search_keys": ["code"]}}
        text = client.post(
            table.render_table_fragment.url(),
            data={STATE: json.dumps(state)},
            headers={"HX-Request": "true"},
        ).text
        assert _names(text) == []
        assert _query(text).search_keys == ["name", "owner"]

    def test_clear_removes_the_search(self):
        client, table = _app()
        page = client.get("/projects?q=anna").text
        text = client.post(
            table.clear_sort_and_filter_fragment.url(),
            data={STATE: _state(page)},
            headers={"HX-Request": "true"},
        ).text
        assert _query(text).search is None
        assert 'value=""' in text


class TestUrl:
    def test_deep_link_with_a_preset_and_a_search(self):
        client, _ = _app(quick_filters=QUICK_FILTERS)
        text = client.get("/projects?view=open&q=ann").text
        assert _names(text) == ["Aurora", "Comet"]
        assert _checked(text) == ["open"]
        assert 'value="ann"' in text
        keys, values = _url_params(text)
        assert keys == ["view", "q"]
        assert values == {"view": ["open"], "q": ["ann"]}

    def test_preset_without_conditions_is_not_written(self):
        client, _ = _app(quick_filters=QUICK_FILTERS)
        _, values = _url_params(client.get("/projects?view=all").text)
        assert values == {}

    def test_unknown_preset_in_url_is_ignored(self):
        client, _ = _app(quick_filters=QUICK_FILTERS)
        text = client.get("/projects?view=nope").text
        assert len(_names(text)) == 4
        assert _checked(text) == ["all"]

    def test_url_param_keys_are_read_and_written(self):
        client, _ = _app(quick_filters=QUICK_FILTERS, url_param_keys=["status"])
        text = client.get("/projects?status=Done").text
        assert _names(text) == ["Dune"]
        # multi-select column: read back as TextChoiceIn, so the preset matches
        assert _checked(text) == ["done"]
        keys, values = _url_params(text)
        assert keys == ["view", "status", "q"]
        assert values == {"view": ["done"], "status": ["Done"]}

    def test_multi_value_condition_is_not_representable(self):
        client, _ = _app(quick_filters=QUICK_FILTERS, url_param_keys=["status"])
        _, values = _url_params(client.get("/projects?view=open").text)
        assert values == {"view": ["open"]}

    def test_single_select_column_reads_text_choice_equals(self):
        class Row(BaseModel):
            id: Annotated[str, a.HiddenColumn()]
            name: Annotated[str, a.TextColumn(label="Name")]
            status: Status

        hx = WebApp()
        rows = [Row(id="1", name="Aurora", status=Status.new)]
        table = DataTable(
            routes=hx, name="rows", source=rows, type=Row, url_param_keys=["status"]
        )

        @hx.page("/rows", title="Rows")
        async def page() -> y.Node:
            return await table.render()

        client = TestClient(hx.create_app())
        assert ">Aurora<" in client.get("/rows?status=New").text
        assert ">Aurora<" not in client.get("/rows?status=Done").text

    def test_url_params_can_be_switched_off(self):
        client, _ = _app(
            quick_filters=QuickFilters(presets=QUICK_FILTERS.presets, url_param=None),
            search=TableSearch(url_param=None),
        )
        text = client.get("/projects?view=done&q=x").text
        assert len(_names(text)) == 4
        assert "data-hx-url-param-keys" not in text

    def test_query_method_reflects_the_url(self):
        seen: list[Query] = []

        hx = WebApp()
        table = DataTable(
            routes=hx,
            name="projects",
            source=list(PROJECTS),
            type=Project,
            quick_filters=QUICK_FILTERS,
        )

        @hx.page("/projects", title="Projects")
        async def page() -> y.Node:
            seen.append(await table.query())
            return await table.render()

        TestClient(hx.create_app()).get("/projects?view=done")
        assert seen[0].filter == [_status("Done")]
        assert seen[0].is_active_filter_or_sort()


class TestDrawer:
    def test_drawer_shows_and_keeps_the_search(self):
        client, table = _app(quick_filters=QUICK_FILTERS)
        page = client.get("/projects?view=open&q=ann").text
        drawer_url = table.filter_drawer.render_drawer_fragment.url()

        opened = client.post(
            drawer_url, data={STATE: _state(page)}, headers={"HX-Request": "true"}
        ).text
        assert "“ann”" in opened
        assert 'name="search" value="ann"' in opened
        # the preset's condition is a normal condition in the drawer
        assert 'name="filter[0].key" value="status"' in opened

        applied = client.post(
            drawer_url,
            data={
                STATE: _state(page),
                "origin": "drawer",
                "action": "apply",
                "search": "ann",
                "filter[0].key": "status",
                "filter[0].values[0].kind": "text_choice_in",
                "filter[0].values[0].values": "New",
            },
            headers={"HX-Request": "true"},
        ).text
        assert _query(applied).search == "ann"
        assert _names(applied) == ["Aurora"]
        assert _checked(applied) == []  # custom

    def test_drawer_clear_removes_the_search(self):
        client, table = _app()
        page = client.get("/projects?q=ann").text
        cleared = client.post(
            table.filter_drawer.render_drawer_fragment.url(),
            data={
                STATE: _state(page),
                "origin": "drawer",
                "action": "clear",
                "search": "ann",
            },
            headers={"HX-Request": "true"},
        ).text
        assert _query(cleared).search is None
