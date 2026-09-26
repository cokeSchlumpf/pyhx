import asyncio
from dataclasses import dataclass, field

import pytest
from commons.users import AnonymousUser, AuthenticatedUser, User
from pydantic import BaseModel

from pyhx.components.data.sources import (
    AppHierarchicalDataSource,
    HierarchicalPage,
    Node,
    Query,
)
from pyhx.core.app_context import AppContext
from pyhx.core.request_context import RequestContext, set_request_context


# ----------------------------------------------------------------------------
# Test fixtures
# ----------------------------------------------------------------------------


class Item(BaseModel):
    id: str
    parent_id: str | None
    name: str


@dataclass
class Registry:
    items: dict[str, Item] = field(default_factory=dict)
    calls: list[tuple[str, tuple]] = field(default_factory=list)


def _install_context(registry: Registry | None = None, user: User | None = None) -> None:
    source: dict = {}
    if registry is not None:
        source[Registry.__name__] = registry
    set_request_context(
        RequestContext(
            user=user if user is not None else AnonymousUser(),
            app_context=AppContext(source),
        )
    )


def _children_of(reg: Registry, parent: str | None) -> list[Item]:
    return [it for it in reg.items.values() if it.parent_id == parent]


def _hierarchical_page(reg: Registry, parent: str | None) -> HierarchicalPage[Item]:
    items = _children_of(reg, parent)
    nodes = [Node(item=it, count=len(_children_of(reg, it.id))) for it in items]
    return HierarchicalPage(items=nodes, total=len(items))


# ----------------------------------------------------------------------------
# Sync path
# ----------------------------------------------------------------------------


def _sync_source() -> AppHierarchicalDataSource[Registry, Item]:
    def fetch(
        reg: Registry, user: User, query: Query, parent: str | None
    ) -> HierarchicalPage[Item]:
        reg.calls.append(("fetch", (user, query, parent)))
        return _hierarchical_page(reg, parent)

    def find_by_id(reg: Registry, user: User, id: str) -> Item | None:
        reg.calls.append(("find_by_id", (user, id)))
        return reg.items.get(id)

    def get_by_id(reg: Registry, user: User, id: str) -> Item:
        reg.calls.append(("get_by_id", (user, id)))
        return reg.items[id]

    def create(reg: Registry, user: User, item: Item) -> None:
        reg.calls.append(("create", (user, item)))
        reg.items[item.id] = item

    def update(reg: Registry, user: User, item: Item) -> None:
        reg.calls.append(("update", (user, item)))
        reg.items[item.id] = item

    def delete(reg: Registry, user: User, item: Item) -> None:
        reg.calls.append(("delete", (user, item)))
        del reg.items[item.id]

    def delete_by_id(reg: Registry, user: User, id: str) -> None:
        reg.calls.append(("delete_by_id", (user, id)))
        del reg.items[id]

    return AppHierarchicalDataSource[Registry, Item](
        Registry,
        fetch=fetch,
        find_by_id=find_by_id,
        get_by_id=get_by_id,
        create=create,
        update=update,
        delete=delete,
        delete_by_id=delete_by_id,
    )


def _seed_tree() -> Registry:
    # Three-level tree: root → a, b; a → a-1.
    return Registry(
        items={
            "root": Item(id="root", parent_id=None, name="Root"),
            "a": Item(id="a", parent_id="root", name="A"),
            "b": Item(id="b", parent_id="root", name="B"),
            "a-1": Item(id="a-1", parent_id="a", name="A1"),
        }
    )


class TestSyncFunctions:
    def test_fetch_root_level(self):
        reg = _seed_tree()
        _install_context(reg)
        src = _sync_source()
        page = asyncio.run(src.fetch(Query()))
        assert [n.item.id for n in page.items] == ["root"]
        # root has two direct children — `count` reflects that.
        assert page.items[0].count == 2

    def test_fetch_propagates_parent(self):
        reg = _seed_tree()
        _install_context(reg)
        src = _sync_source()
        page = asyncio.run(src.fetch(Query(), parent="a"))
        assert [n.item.id for n in page.items] == ["a-1"]
        # Confirm the parent arg flowed into the user function.
        last_fetch = [c for c in reg.calls if c[0] == "fetch"][-1]
        assert last_fetch[1][2] == "a"  # query, parent="a"

    def test_find_by_id_round_trips(self):
        reg = _seed_tree()
        _install_context(reg)
        src = _sync_source()
        assert asyncio.run(src.find_by_id("a-1")).id == "a-1"
        assert asyncio.run(src.find_by_id("nope")) is None

    def test_get_by_id_returns_item(self):
        reg = _seed_tree()
        _install_context(reg)
        src = _sync_source()
        assert asyncio.run(src.get_by_id("a")).name == "A"

    def test_create_update_delete(self):
        reg = _seed_tree()
        _install_context(reg)
        src = _sync_source()
        new = Item(id="a-2", parent_id="a", name="A2")
        asyncio.run(src.create(new))
        assert "a-2" in reg.items
        renamed = Item(id="a-2", parent_id="a", name="A2!")
        asyncio.run(src.update(renamed))
        assert reg.items["a-2"].name == "A2!"
        asyncio.run(src.delete(renamed))
        assert "a-2" not in reg.items

    def test_delete_by_id(self):
        reg = _seed_tree()
        _install_context(reg)
        src = _sync_source()
        asyncio.run(src.delete_by_id("a-1"))
        assert "a-1" not in reg.items


# ----------------------------------------------------------------------------
# Async path
# ----------------------------------------------------------------------------


class TestAsyncFunctions:
    def test_async_fetch_is_awaited(self):
        reg = _seed_tree()
        _install_context(reg)

        async def fetch(
            reg: Registry, user: User, query: Query, parent: str | None
        ) -> HierarchicalPage[Item]:
            await asyncio.sleep(0)
            return _hierarchical_page(reg, parent)

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppHierarchicalDataSource[Registry, Item](
            Registry,
            fetch=fetch,
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
        )
        page = asyncio.run(src.fetch(Query()))
        assert [n.item.id for n in page.items] == ["root"]


# ----------------------------------------------------------------------------
# Missing registry → LookupError
# ----------------------------------------------------------------------------


class TestMissingRegistry:
    def test_lookup_error_when_registry_not_in_app_context(self):
        set_request_context(
            RequestContext(user=AnonymousUser(), app_context=AppContext({}))
        )
        src = _sync_source()
        with pytest.raises(LookupError):
            asyncio.run(src.fetch(Query()))


# ----------------------------------------------------------------------------
# Parent arg flows through (None for root + child id)
# ----------------------------------------------------------------------------


class TestParentArg:
    def test_parent_none_for_root(self):
        reg = _seed_tree()
        _install_context(reg)
        src = _sync_source()
        asyncio.run(src.fetch(Query()))
        last_fetch = [c for c in reg.calls if c[0] == "fetch"][-1]
        assert last_fetch[1][2] is None

    def test_parent_id_passed_explicitly(self):
        reg = _seed_tree()
        _install_context(reg)
        src = _sync_source()
        asyncio.run(src.fetch(Query(), parent="root"))
        last_fetch = [c for c in reg.calls if c[0] == "fetch"][-1]
        assert last_fetch[1][2] == "root"


# ----------------------------------------------------------------------------
# get_id default + override
# ----------------------------------------------------------------------------


class TestGetId:
    def test_default_reads_id_field(self):
        _install_context(None)
        src = _sync_source()
        item = Item(id="x", parent_id=None, name="X")
        assert asyncio.run(src.get_id(item)) == "x"

    def test_default_works_on_dict_items(self):
        _install_context(None)

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppHierarchicalDataSource[Registry, dict](
            Registry,
            fetch=lambda *a: HierarchicalPage(items=[], total=0),
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
        )
        assert asyncio.run(src.get_id({"id": "y"})) == "y"

    def test_override_takes_precedence(self):
        _install_context(None)

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppHierarchicalDataSource[Registry, Item](
            Registry,
            fetch=lambda *a: HierarchicalPage(items=[], total=0),
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
            get_id=lambda item: f"prefix:{item.id}",
        )
        assert (
            asyncio.run(src.get_id(Item(id="a", parent_id=None, name="A")))
            == "prefix:a"
        )


# ----------------------------------------------------------------------------
# HierarchicalPage passes through unchanged
# ----------------------------------------------------------------------------


class TestHierarchicalPagePassthrough:
    def test_page_returned_as_is(self):
        # The strict-only return shape means whatever Page the domain
        # constructs lands at the caller untouched.
        custom_page = HierarchicalPage[Item](
            items=[
                Node(item=Item(id="x", parent_id=None, name="X"), count=42),
            ],
            total=999,
        )

        def fetch(*a, **kw) -> HierarchicalPage[Item]:
            return custom_page

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppHierarchicalDataSource[Registry, Item](
            Registry,
            fetch=fetch,
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
        )
        _install_context(Registry())
        result = asyncio.run(src.fetch(Query()))
        assert result is custom_page  # exact same object


# ----------------------------------------------------------------------------
# User flow-through
# ----------------------------------------------------------------------------


class TestUserPassthrough:
    def test_custom_user_arrives_in_function(self):
        seen: list[User] = []
        user = AuthenticatedUser(display_name="Bob")

        def fetch(
            reg: Registry, u: User, query: Query, parent: str | None
        ) -> HierarchicalPage[Item]:
            seen.append(u)
            return HierarchicalPage(items=[], total=0)

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppHierarchicalDataSource[Registry, Item](
            Registry,
            fetch=fetch,
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
        )
        _install_context(Registry(), user=user)
        asyncio.run(src.fetch(Query()))
        assert seen == [user]

    def test_anonymous_user_is_default(self):
        seen: list[User] = []

        def fetch(
            reg: Registry, u: User, query: Query, parent: str | None
        ) -> HierarchicalPage[Item]:
            seen.append(u)
            return HierarchicalPage(items=[], total=0)

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppHierarchicalDataSource[Registry, Item](
            Registry,
            fetch=fetch,
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
        )
        _install_context(Registry())
        asyncio.run(src.fetch(Query()))
        assert isinstance(seen[0], AnonymousUser)
