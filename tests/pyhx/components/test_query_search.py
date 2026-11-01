"""Search and counts on the query and the data sources (T-008)."""

import asyncio
from enum import Enum

from commons.users import AnonymousUser, User
from pydantic import BaseModel
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select

from pyhx.components.data.sources import (
    AppReadOnlyDataSource,
    AppReadOnlyDataSourceBase,
)
from pyhx.components.data.sources._query import apply_query, count_matches
from pyhx.components.data.sources.filter import (
    Condition,
    StringEquals,
    TextChoiceEquals,
)
from pyhx.components.data.sources.mapped_data_source import MappedReadOnlyDataSource
from pyhx.components.data.sources.query import Query
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.components.data.sources.sort import SortOrder
from pyhx.components.data.sources.source import Page, ReadOnlyDataSource
from pyhx.components.data.sources.sql_query import apply_sql_query
from pyhx.core.app_context import AppContext
from pyhx.core.request_context import RequestContext, set_request_context


class Status(str, Enum):
    open = "Offen"
    closed = "Abgeschlossen"


class Case(BaseModel):
    id: str
    name: str
    number: str | None
    status: Status


CASES = [
    Case(id="1", name="David Meier", number="IV-01", status=Status.open),
    Case(id="2", name="Sandra Keller", number="IV-02", status=Status.closed),
    Case(id="3", name="Peter Meierhans", number=None, status=Status.closed),
]


def _ids(query: Query) -> list[str]:
    items, _ = apply_query(CASES, query)
    return [c.id for c in items]


class TestInMemorySearch:
    def test_matches_contains_ignoring_case(self):
        assert _ids(Query(search="MEIER", search_keys=["name"])) == ["1", "3"]

    def test_any_key_matches(self):
        assert _ids(Query(search="iv-02", search_keys=["name", "number"])) == ["2"]

    def test_none_value_never_matches(self):
        assert _ids(Query(search="None", search_keys=["number"])) == []

    def test_enum_is_searched_by_value(self):
        assert _ids(Query(search="abgeschl", search_keys=["status"])) == ["2", "3"]

    def test_no_keys_or_no_term_is_no_search(self):
        assert _ids(Query(search="meier")) == ["1", "2", "3"]
        assert _ids(Query(search=None, search_keys=["name"])) == ["1", "2", "3"]

    def test_search_is_and_combined_even_with_filter_mode_any(self):
        query = Query(
            filter_mode="any",
            filter=[Condition(key="id", values=[StringEquals(value="2")])],
            search="meier",
            search_keys=["name"],
        )
        assert _ids(query) == []

    def test_count_matches_includes_search(self):
        assert count_matches(CASES, Query(search="meier", search_keys=["name"])) == 2
        assert count_matches(CASES, Query()) == 3


class TestQuery:
    def test_clear_removes_search_but_keeps_keys(self):
        query = Query(search="x", search_keys=["name"])
        query.clear()
        assert query.search is None
        assert query.search_keys == ["name"]

    def test_search_counts_as_active(self):
        assert Query(search="x").is_active_filter_or_sort()
        assert not Query().is_active_filter_or_sort()

    def test_extract_keeps_search_on_remaining(self):
        query = Query(
            sort=[SortOrder(key="name", order="asc")],
            search="x",
            search_keys=["name", "number"],
        )
        remaining, extracted = query.extract("name")
        assert remaining.search == "x"
        assert remaining.search_keys == ["name", "number"]
        assert extracted.search is None
        assert extracted.search_keys == []


class TestSqlSearch:
    def _run(self, query: Query) -> list[int]:
        engine = create_engine("sqlite://")
        metadata = MetaData()
        table = Table(
            "cases",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String),
            Column("number", String),
        )
        metadata.create_all(engine)
        with engine.begin() as conn:
            conn.execute(
                table.insert(),
                [
                    {"id": 1, "name": "David Meier", "number": "IV-01"},
                    {"id": 2, "name": "Sandra Keller", "number": "100%"},
                    {"id": 3, "name": "Peter Meierhans", "number": "IV_03"},
                ],
            )
            stmt = apply_sql_query(
                select(table.c.id).order_by(table.c.id), query, table.c
            )
            return [row[0] for row in conn.execute(stmt)]

    def test_search_ignores_case_over_keys(self):
        assert self._run(Query(search="MEIER", search_keys=["name"])) == [1, 3]
        assert self._run(Query(search="iv-01", search_keys=["name", "number"])) == [1]

    def test_wildcards_match_literally(self):
        assert self._run(Query(search="%", search_keys=["number"])) == [2]
        assert self._run(Query(search="_", search_keys=["number"])) == [3]

    def test_unmapped_keys_are_skipped(self):
        assert self._run(Query(search="meier", search_keys=["unknown"])) == [1, 2, 3]

    def test_search_and_filter_combine(self):
        query = Query(
            filter_mode="any",
            filter=[Condition(key="id", values=[StringEquals(value="2")])],
            search="meier",
            search_keys=["name"],
        )
        assert self._run(query) == []


class _FetchOnly(ReadOnlyDataSource[Case]):
    """A source written before search and counts existed."""

    async def fetch(self, query: Query) -> Page[Case]:
        return Page(items=CASES, total=len(CASES))

    async def get_id(self, item: Case) -> str:
        return item.id

    async def find_by_id(self, id: str) -> Case | None:
        return None

    async def get_by_id(self, id: str) -> Case:
        raise KeyError(id)


class TestSourceCapabilities:
    def test_existing_source_has_no_search_and_no_count(self):
        source = _FetchOnly()
        assert source.supports_search is False
        assert asyncio.run(source.count(Query())) is None

    def test_simple_source_searches_and_counts(self):
        source = SimpleDataSource(list(CASES))
        query = Query(
            filter=[
                Condition(
                    key="status", values=[TextChoiceEquals(value="Abgeschlossen")]
                )
            ],
            search="meier",
            search_keys=["name"],
        )
        assert source.supports_search is True
        assert asyncio.run(source.count(query)) == 1
        assert [c.id for c in asyncio.run(source.fetch(query)).items] == ["3"]

    def test_mapped_source_delegates(self):
        async def ident(c: Case) -> Case:
            return c

        seen: list[Query] = []

        async def map_query(q: Query) -> Query:
            seen.append(q)
            return q.model_copy(update={"search_keys": ["name"]})

        mapped = MappedReadOnlyDataSource(
            SimpleDataSource(list(CASES)), ident, ident, map_query
        )
        assert mapped.supports_search is True
        assert asyncio.run(mapped.count(Query(search="meier"))) == 2
        assert len(seen) == 1
        assert (
            MappedReadOnlyDataSource(_FetchOnly(), ident, ident).supports_search
            is False
        )


class _Registry:
    pass


def _install_context() -> None:
    set_request_context(
        RequestContext(
            user=AnonymousUser(),
            app_context=AppContext({_Registry.__name__: _Registry()}),
        )
    )


class TestAppSources:
    def test_base_defaults_to_no_count_and_no_search(self):
        class Source(AppReadOnlyDataSourceBase[_Registry, Case]):
            async def do_fetch(self, registry, user, query):
                return list(CASES)

            async def do_find_by_id(self, registry, user, id):
                return None

            async def do_get_by_id(self, registry, user, id):
                raise KeyError(id)

        _install_context()
        source = Source(_Registry)
        assert source.supports_search is False
        assert asyncio.run(source.count(Query())) is None

    def test_base_count_dispatches_with_registry_and_user(self):
        calls: list[tuple[object, User, Query]] = []

        class Source(AppReadOnlyDataSourceBase[_Registry, Case]):
            supports_search = True

            async def do_fetch(self, registry, user, query):
                return list(CASES)

            async def do_find_by_id(self, registry, user, id):
                return None

            async def do_get_by_id(self, registry, user, id):
                raise KeyError(id)

            async def do_count(self, registry, user, query):
                calls.append((registry, user, query))
                return 42

        _install_context()
        source = Source(_Registry)
        assert source.supports_search is True
        assert asyncio.run(source.count(Query(search="x"))) == 42
        assert isinstance(calls[0][0], _Registry)
        assert calls[0][2].search == "x"

    def test_function_variant_takes_count_and_supports_search(self):
        _install_context()
        plain = AppReadOnlyDataSource[_Registry, Case](
            _Registry,
            fetch=lambda r, u, q: list(CASES),
            find_by_id=lambda r, u, id: None,
            get_by_id=lambda r, u, id: CASES[0],
        )
        assert plain.supports_search is False
        assert asyncio.run(plain.count(Query())) is None

        async def count(r, u, q):
            return 7

        counting = AppReadOnlyDataSource[_Registry, Case](
            _Registry,
            fetch=lambda r, u, q: list(CASES),
            find_by_id=lambda r, u, id: None,
            get_by_id=lambda r, u, id: CASES[0],
            count=count,
            supports_search=True,
        )
        assert counting.supports_search is True
        assert asyncio.run(counting.count(Query())) == 7
