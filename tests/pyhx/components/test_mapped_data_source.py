import asyncio

from pydantic import BaseModel

from pyhx.components.data.sources.filter import Condition, StringContains
from pyhx.components.data.sources.mapped_data_source import (
    MappedDataSource,
    MappedHierarchicalDataSource,
    MappedReadOnlyDataSource,
    MappedReadOnlyHierarchicalDataSource,
)
from pyhx.components.data.sources.simple_data_source import SimpleDataSource
from pyhx.components.data.sources.simple_hierarchical_data_source import (
    SimpleHierarchicalDataSource,
)
from pyhx.components.data.sources.sort import SortOrder
from pyhx.components.data.sources.query import Query


# Inner type (what the source actually holds) and outer type (what the
# adapter exposes). Outer renames ``raw_name`` to ``display_name`` to
# exercise the ``map_query`` path.
class Inner(BaseModel):
    id: str
    raw_name: str
    parent_id: str | None = None


class Outer(BaseModel):
    id: str
    display_name: str
    parent_id: str | None = None


async def inner_to_outer(item: Inner) -> Outer:
    return Outer(id=item.id, display_name=item.raw_name, parent_id=item.parent_id)


async def outer_to_inner(item: Outer) -> Inner:
    return Inner(id=item.id, raw_name=item.display_name, parent_id=item.parent_id)


async def rewrite_display_to_raw(query: Query) -> Query:
    return query.model_copy(
        update={
            "sort": [
                SortOrder(
                    key="raw_name" if s.key == "display_name" else s.key,
                    order=s.order,
                )
                for s in query.sort
            ],
            "filter": [
                Condition(
                    key="raw_name" if c.key == "display_name" else c.key,
                    values=c.values,
                )
                for c in query.filter
            ],
        }
    )


FLAT_DATA = [
    Inner(id="1", raw_name="Charlie"),
    Inner(id="2", raw_name="Alpha"),
    Inner(id="3", raw_name="Bravo"),
]


def make_flat_adapter() -> MappedDataSource[Inner, Outer]:
    return MappedDataSource(
        SimpleDataSource(list(FLAT_DATA)),
        inner_to_outer,
        outer_to_inner,
        rewrite_display_to_raw,
    )


def test_flat_fetch_maps_items_to_outer_type() -> None:
    adapter = make_flat_adapter()

    page = asyncio.run(adapter.fetch(Query()))

    assert all(isinstance(item, Outer) for item in page.items)
    assert {item.id: item.display_name for item in page.items} == {
        "1": "Charlie",
        "2": "Alpha",
        "3": "Bravo",
    }
    assert page.total == 3


def test_flat_query_mapping_translates_sort_key() -> None:
    adapter = make_flat_adapter()

    # Outer-facing sort key — adapter must rewrite it before passing to
    # the inner source, otherwise the sort would silently no-op.
    page = asyncio.run(
        adapter.fetch(Query(sort=[SortOrder(key="display_name", order="asc")]))
    )

    assert [item.display_name for item in page.items] == ["Alpha", "Bravo", "Charlie"]


def test_flat_query_mapping_translates_filter_key() -> None:
    adapter = make_flat_adapter()

    page = asyncio.run(
        adapter.fetch(
            Query(
                filter=[Condition(key="display_name", values=[StringContains(value="a")])]
            )
        )
    )

    assert {item.display_name for item in page.items} == {"Charlie", "Alpha", "Bravo"}


def test_flat_get_id_round_trips_through_reverse() -> None:
    adapter = make_flat_adapter()

    outer = asyncio.run(adapter.get_by_id("2"))
    assert outer.display_name == "Alpha"
    assert asyncio.run(adapter.get_id(outer)) == "2"


def test_flat_find_by_id_returns_none_for_miss() -> None:
    adapter = make_flat_adapter()

    assert asyncio.run(adapter.find_by_id("nope")) is None


def test_flat_create_writes_through_reverse_mapping() -> None:
    inner = SimpleDataSource[Inner]([])
    adapter = MappedDataSource(inner, inner_to_outer, outer_to_inner)

    asyncio.run(adapter.create(Outer(id="x", display_name="Hello")))

    inner_page = asyncio.run(inner.fetch(Query()))
    assert inner_page.items == [Inner(id="x", raw_name="Hello")]


def test_flat_update_writes_through_reverse_mapping() -> None:
    inner = SimpleDataSource[Inner]([Inner(id="x", raw_name="Old")])
    adapter = MappedDataSource(inner, inner_to_outer, outer_to_inner)

    asyncio.run(adapter.update(Outer(id="x", display_name="New")))

    assert inner._data == [Inner(id="x", raw_name="New")]


def test_flat_delete_by_id_passes_id_through() -> None:
    inner = SimpleDataSource[Inner]([Inner(id="x", raw_name="Doomed")])
    adapter = MappedDataSource(inner, inner_to_outer, outer_to_inner)

    asyncio.run(adapter.delete_by_id("x"))

    assert inner._data == []


def test_flat_delete_writes_through_reverse_mapping() -> None:
    inner = SimpleDataSource[Inner]([Inner(id="x", raw_name="Doomed")])
    adapter = MappedDataSource(inner, inner_to_outer, outer_to_inner)

    asyncio.run(adapter.delete(Outer(id="x", display_name="Doomed")))

    assert inner._data == []


def test_read_only_variant_does_not_expose_mutation_methods() -> None:
    # Static-typing-wise, ``MappedReadOnlyDataSource`` is not a
    # ``DataSource`` so the type system already prevents accidental
    # ``create``/``update``/``delete`` calls. Confirm the class also
    # lacks these methods at runtime.
    adapter = MappedReadOnlyDataSource(
        SimpleDataSource(list(FLAT_DATA)), inner_to_outer, outer_to_inner
    )
    assert not hasattr(adapter, "create")
    assert not hasattr(adapter, "update")
    assert not hasattr(adapter, "delete")
    assert not hasattr(adapter, "delete_by_id")


def test_identity_mapping_round_trip_matches_inner() -> None:
    # With no mapping changes the adapter must be transparent.
    async def identity_inner(item: Inner) -> Inner:
        return item

    inner = SimpleDataSource(list(FLAT_DATA))
    adapter = MappedDataSource[Inner, Inner](inner, identity_inner, identity_inner)

    inner_page = asyncio.run(inner.fetch(Query()))
    outer_page = asyncio.run(adapter.fetch(Query()))
    assert [i.id for i in outer_page.items] == [i.id for i in inner_page.items]
    assert outer_page.total == inner_page.total


# --- Hierarchical ---

HIERARCHICAL_DATA = [
    Inner(id="root", raw_name="Root", parent_id=None),
    Inner(id="a", raw_name="Alpha", parent_id="root"),
    Inner(id="b", raw_name="Bravo", parent_id="root"),
    Inner(id="a-1", raw_name="Alpha One", parent_id="a"),
]


def make_hierarchical_adapter() -> MappedHierarchicalDataSource[Inner, Outer]:
    return MappedHierarchicalDataSource(
        SimpleHierarchicalDataSource(list(HIERARCHICAL_DATA)),
        inner_to_outer,
        outer_to_inner,
        rewrite_display_to_raw,
    )


def test_hierarchical_fetch_maps_items_and_preserves_count() -> None:
    adapter = make_hierarchical_adapter()

    page = asyncio.run(adapter.fetch(Query()))
    assert [n.item.display_name for n in page.items] == ["Root"]
    # Root has 2 direct children ("Alpha", "Bravo") in the inner source.
    # The mapped adapter preserves ``count`` unchanged.
    assert page.items[0].count == 2

    children = asyncio.run(adapter.fetch(Query(), parent="root"))
    assert {n.item.id for n in children.items} == {"a", "b"}
    counts = {n.item.id: n.count for n in children.items}
    assert counts == {"a": 1, "b": 0}


def test_hierarchical_query_mapping_applies_at_level() -> None:
    adapter = make_hierarchical_adapter()

    page = asyncio.run(
        adapter.fetch(
            Query(sort=[SortOrder(key="display_name", order="desc")]),
            parent="root",
        )
    )

    assert [n.item.display_name for n in page.items] == ["Bravo", "Alpha"]


def test_hierarchical_get_by_id_returns_outer() -> None:
    adapter = make_hierarchical_adapter()

    outer = asyncio.run(adapter.get_by_id("a-1"))
    assert isinstance(outer, Outer)
    assert outer.display_name == "Alpha One"


def test_hierarchical_create_writes_through_reverse() -> None:
    inner = SimpleHierarchicalDataSource(list(HIERARCHICAL_DATA))
    adapter = MappedHierarchicalDataSource(inner, inner_to_outer, outer_to_inner)

    asyncio.run(
        adapter.create(Outer(id="c", display_name="Charlie", parent_id="root"))
    )

    page = asyncio.run(inner.fetch(Query(), parent="root"))
    assert {n.item.id for n in page.items} == {"a", "b", "c"}


def test_hierarchical_read_only_lacks_mutations() -> None:
    adapter = MappedReadOnlyHierarchicalDataSource(
        SimpleHierarchicalDataSource(list(HIERARCHICAL_DATA)),
        inner_to_outer,
        outer_to_inner,
    )
    assert not hasattr(adapter, "create")
    assert not hasattr(adapter, "update")
    assert not hasattr(adapter, "delete")
    assert not hasattr(adapter, "delete_by_id")
