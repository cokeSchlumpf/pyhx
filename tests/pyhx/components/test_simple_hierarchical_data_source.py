import asyncio

from pydantic import BaseModel

from pyhx.components.data.sources.filter import Condition, StringContains
from pyhx.components.data.sources.simple_hierarchical_data_source import (
    SimpleHierarchicalDataSource,
)
from pyhx.components.data.sources.sort import SortOrder
from pyhx.components.data.sources.query import Query


class Org(BaseModel):
    id: str
    parent_id: str | None
    name: str


# A 3-level tree:
#
#   root-a              (no parent)
#     ├─ a-1            (parent_id="root-a")
#     │    └─ a-1-i     (parent_id="a-1")
#     └─ a-2
#   root-b
#     └─ b-1
#
DATA: list[Org] = [
    Org(id="root-a", parent_id=None, name="Alpha"),
    Org(id="root-b", parent_id=None, name="Beta"),
    Org(id="a-1", parent_id="root-a", name="Alpha One"),
    Org(id="a-2", parent_id="root-a", name="Alpha Two"),
    Org(id="b-1", parent_id="root-b", name="Beta One"),
    Org(id="a-1-i", parent_id="a-1", name="Alpha One i"),
]


def test_root_level_returns_parentless_items_with_child_counts() -> None:
    src = SimpleHierarchicalDataSource(DATA)

    page = asyncio.run(src.fetch(Query()))

    assert [n.item.id for n in page.items] == ["root-a", "root-b"]
    assert page.total == 2
    counts = {n.item.id: n.count for n in page.items}
    assert counts == {"root-a": 2, "root-b": 1}


def test_descend_one_level() -> None:
    src = SimpleHierarchicalDataSource(DATA)

    page = asyncio.run(src.fetch(Query(), parent="root-a"))

    assert [n.item.id for n in page.items] == ["a-1", "a-2"]
    assert page.total == 2
    counts = {n.item.id: n.count for n in page.items}
    assert counts == {"a-1": 1, "a-2": 0}


def test_leaf_count_is_zero() -> None:
    src = SimpleHierarchicalDataSource(DATA)

    page = asyncio.run(src.fetch(Query(), parent="a-2"))

    assert page.items == []
    assert page.total == 0


def test_filter_narrows_items_and_counts() -> None:
    src = SimpleHierarchicalDataSource(DATA)

    # Show only "*One*" children under root-a.
    query = Query(filter=[Condition(key="name", values=[StringContains(value="One")])])
    page = asyncio.run(src.fetch(query, parent="root-a"))

    assert [n.item.id for n in page.items] == ["a-1"]
    assert page.total == 1
    # `a-1`'s direct child `a-1-i` ("Alpha One i") also matches the filter,
    # so the count survives. If it didn't match, count would be 0.
    assert page.items[0].count == 1


def test_filter_aware_count_partially_matching_children() -> None:
    # Add an extra child of root-a that won't match the "One" filter.
    data = DATA + [Org(id="a-3", parent_id="root-a", name="Gamma")]
    src = SimpleHierarchicalDataSource(data)

    # Without filter: root-a has 3 children.
    page = asyncio.run(src.fetch(Query()))
    counts = {n.item.id: n.count for n in page.items}
    assert counts["root-a"] == 3

    # With "*One*" filter: only a-1 ("Alpha One") matches → count is 1.
    # Even though a-2 and a-3 still exist as DOM-level children, the
    # disclosure honestly reports what the user will see on expand.
    query = Query(filter=[Condition(key="name", values=[StringContains(value="One")])])
    page = asyncio.run(src.fetch(query))
    counts = {n.item.id: n.count for n in page.items}
    # root-a's name doesn't contain "One" — wait, neither does Alpha. The
    # root level itself filters out items not matching, but `a-1-i` survives
    # under root-a -> root-a wouldn't appear because its name is "Alpha". So
    # this assertion verifies behaviour by directly querying root-a's level.
    page = asyncio.run(src.fetch(query, parent="root-a"))
    # a-1 matches the filter and itself has a child (a-1-i) that also matches
    # → a-1's count under this filter is 1.
    assert [n.item.id for n in page.items] == ["a-1"]
    assert page.items[0].count == 1


def test_sort_orders_within_level() -> None:
    src = SimpleHierarchicalDataSource(DATA)

    query = Query(sort=[SortOrder(key="name", order="desc")])
    page = asyncio.run(src.fetch(query, parent="root-a"))

    assert [n.item.name for n in page.items] == ["Alpha Two", "Alpha One"]


def test_paging_within_level() -> None:
    src = SimpleHierarchicalDataSource(DATA)

    query = Query(offset=1, limit=1)
    page = asyncio.run(src.fetch(query, parent="root-a"))

    assert [n.item.id for n in page.items] == ["a-2"]
    # `total` is the post-filter level count, ignoring offset/limit.
    assert page.total == 2


def test_get_id_uses_configured_field() -> None:
    src = SimpleHierarchicalDataSource(DATA)
    assert asyncio.run(src.get_id(DATA[0])) == "root-a"


def test_dict_items_via_field_keys() -> None:
    data: list[dict] = [
        {"id": "x", "parent_id": None, "label": "X"},
        {"id": "y", "parent_id": "x", "label": "Y"},
    ]
    src = SimpleHierarchicalDataSource(data)

    root = asyncio.run(src.fetch(Query()))
    assert [n.item["id"] for n in root.items] == ["x"]
    assert root.items[0].count == 1

    child = asyncio.run(src.fetch(Query(), parent="x"))
    assert [n.item["id"] for n in child.items] == ["y"]
    assert child.items[0].count == 0


def test_orphans_are_unreachable() -> None:
    data = [
        Org(id="root", parent_id=None, name="Root"),
        # references a non-existent parent — silently dropped from the tree
        Org(id="orphan", parent_id="ghost", name="Lost"),
    ]
    src = SimpleHierarchicalDataSource(data)

    root_page = asyncio.run(src.fetch(Query()))
    assert [n.item.id for n in root_page.items] == ["root"]
    assert root_page.items[0].count == 0


def test_find_by_id_returns_item_at_any_level() -> None:
    src = SimpleHierarchicalDataSource(DATA)

    assert asyncio.run(src.find_by_id("root-a")) == DATA[0]
    assert asyncio.run(src.find_by_id("a-1-i")) == DATA[5]


def test_find_by_id_returns_none_for_missing() -> None:
    src = SimpleHierarchicalDataSource(DATA)

    assert asyncio.run(src.find_by_id("nope")) is None


def test_find_by_id_reaches_orphans() -> None:
    # Counterpart to ``test_orphans_are_unreachable``: ``fetch`` hides
    # orphans, but ``find_by_id`` still resolves them so that a UI holding
    # only the id can recover the item.
    data = [
        Org(id="root", parent_id=None, name="Root"),
        Org(id="orphan", parent_id="ghost", name="Lost"),
    ]
    src = SimpleHierarchicalDataSource(data)

    assert asyncio.run(src.find_by_id("orphan")) == data[1]


def test_get_by_id_raises_keyerror_on_miss() -> None:
    src = SimpleHierarchicalDataSource(DATA)

    assert asyncio.run(src.get_by_id("a-1")) == DATA[2]
    try:
        asyncio.run(src.get_by_id("nope"))
    except KeyError as e:
        assert e.args == ("nope",)
    else:
        raise AssertionError("expected KeyError")


def test_create_adds_to_fetch_and_updates_parent_index() -> None:
    src = SimpleHierarchicalDataSource(list(DATA))
    asyncio.run(src.create(Org(id="a-3", parent_id="root-a", name="Alpha Three")))

    # Visible at the right level, and the root-a child count moved 2 -> 3.
    children = asyncio.run(src.fetch(Query(), parent="root-a"))
    assert [n.item.id for n in children.items] == ["a-1", "a-2", "a-3"]
    roots = asyncio.run(src.fetch(Query()))
    assert {n.item.id: n.count for n in roots.items} == {"root-a": 3, "root-b": 1}


def test_create_raises_on_duplicate_id() -> None:
    src = SimpleHierarchicalDataSource(list(DATA))
    try:
        asyncio.run(src.create(Org(id="root-a", parent_id=None, name="Dup")))
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")


def test_delete_by_id_drops_item_and_leaves_children_dangling() -> None:
    src = SimpleHierarchicalDataSource(list(DATA))
    asyncio.run(src.delete_by_id("a-1"))  # "a-1-i" used to live under "a-1"

    # ``a-1`` is gone from its parent's listing and from id-lookups.
    children = asyncio.run(src.fetch(Query(), parent="root-a"))
    assert [n.item.id for n in children.items] == ["a-2"]
    assert asyncio.run(src.find_by_id("a-1")) is None

    # Its former child stays in _data — still id-addressable, and still
    # returned by an explicit fetch(parent="a-1") because we don't cascade.
    # A root-down walk can no longer reach the "a-1" parent though, so in
    # practice the child becomes orphaned during normal browsing.
    assert asyncio.run(src.find_by_id("a-1-i")) is not None
    dangling = asyncio.run(src.fetch(Query(), parent="a-1"))
    assert [n.item.id for n in dangling.items] == ["a-1-i"]


def test_delete_raises_on_missing_id() -> None:
    src = SimpleHierarchicalDataSource(list(DATA))
    try:
        asyncio.run(src.delete_by_id("nope"))
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")


def test_update_replaces_in_place_for_same_parent() -> None:
    src = SimpleHierarchicalDataSource(list(DATA))
    asyncio.run(
        src.update(Org(id="a-1", parent_id="root-a", name="Alpha One (renamed)"))
    )

    children = asyncio.run(src.fetch(Query(), parent="root-a"))
    by_id = {n.item.id: n.item.name for n in children.items}
    assert by_id["a-1"] == "Alpha One (renamed)"


def test_update_reparents_when_parent_id_changes() -> None:
    src = SimpleHierarchicalDataSource(list(DATA))
    asyncio.run(src.update(Org(id="a-1", parent_id="root-b", name="Alpha One")))

    # No longer a child of root-a; now under root-b.
    under_a = asyncio.run(src.fetch(Query(), parent="root-a"))
    assert [n.item.id for n in under_a.items] == ["a-2"]
    under_b = asyncio.run(src.fetch(Query(), parent="root-b"))
    assert [n.item.id for n in under_b.items] == ["b-1", "a-1"]


def test_update_raises_on_missing_id() -> None:
    src = SimpleHierarchicalDataSource(list(DATA))
    try:
        asyncio.run(src.update(Org(id="nope", parent_id=None, name="Ghost")))
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
