import asyncio
from dataclasses import dataclass, field

import pytest
from commons.users import AnonymousUser, AuthenticatedUser, User
from pydantic import BaseModel

from pyhx.components.data.sources import (
    AppDataSource,
    Page,
    Query,
)
from pyhx.core.app_context import AppContext
from pyhx.core.request_context import RequestContext, set_request_context


# ----------------------------------------------------------------------------
# Test fixtures
# ----------------------------------------------------------------------------


class Item(BaseModel):
    id: str
    name: str


@dataclass
class Registry:
    """Stand-in for a real domain registry, plus a recording log so tests
    can assert what was called."""

    items: dict[str, Item] = field(default_factory=dict)
    calls: list[tuple[str, tuple]] = field(default_factory=list)


def _install_context(registry: Registry | None = None, user: User | None = None) -> None:
    """Seed an :class:`AppContext` (with optional registry) + user on the
    current :class:`RequestContext`."""
    source: dict = {}
    if registry is not None:
        source[Registry.__name__] = registry
    set_request_context(
        RequestContext(
            user=user if user is not None else AnonymousUser(),
            app_context=AppContext(source),
        )
    )


# ----------------------------------------------------------------------------
# Sync function path
# ----------------------------------------------------------------------------


def _sync_source() -> AppDataSource[Registry, Item]:
    def fetch(reg: Registry, user: User, query: Query) -> list[Item]:
        reg.calls.append(("fetch", (user, query)))
        return list(reg.items.values())

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

    return AppDataSource[Registry, Item](
        Registry,
        fetch=fetch,
        find_by_id=find_by_id,
        get_by_id=get_by_id,
        create=create,
        update=update,
        delete=delete,
        delete_by_id=delete_by_id,
    )


class TestSyncFunctions:
    def test_fetch_returns_wrapped_page(self):
        reg = Registry(items={"a": Item(id="a", name="alpha")})
        _install_context(reg)
        src = _sync_source()
        page = asyncio.run(src.fetch(Query()))
        assert isinstance(page, Page)
        assert [i.id for i in page.items] == ["a"]
        assert page.total == 1
        assert reg.calls[0][0] == "fetch"

    def test_find_by_id_passes_registry_and_user(self):
        user = AuthenticatedUser(display_name="Alice")
        reg = Registry(items={"a": Item(id="a", name="alpha")})
        _install_context(reg, user=user)
        src = _sync_source()
        result = asyncio.run(src.find_by_id("a"))
        assert result is not None and result.id == "a"
        assert reg.calls == [("find_by_id", (user, "a"))]

    def test_find_by_id_miss_returns_none(self):
        _install_context(Registry())
        src = _sync_source()
        assert asyncio.run(src.find_by_id("nope")) is None

    def test_get_by_id_returns_item(self):
        reg = Registry(items={"a": Item(id="a", name="alpha")})
        _install_context(reg)
        src = _sync_source()
        assert asyncio.run(src.get_by_id("a")).name == "alpha"

    def test_create_update_delete(self):
        reg = Registry()
        _install_context(reg)
        src = _sync_source()
        item = Item(id="a", name="alpha")
        asyncio.run(src.create(item))
        assert reg.items == {"a": item}
        renamed = Item(id="a", name="ALPHA")
        asyncio.run(src.update(renamed))
        assert reg.items["a"].name == "ALPHA"
        asyncio.run(src.delete(renamed))
        assert reg.items == {}

    def test_delete_by_id(self):
        reg = Registry(items={"a": Item(id="a", name="alpha")})
        _install_context(reg)
        src = _sync_source()
        asyncio.run(src.delete_by_id("a"))
        assert reg.items == {}


# ----------------------------------------------------------------------------
# Async function path
# ----------------------------------------------------------------------------


class TestAsyncFunctions:
    def test_async_fetch_is_awaited(self):
        reg = Registry(items={"a": Item(id="a", name="alpha")})
        _install_context(reg)

        async def fetch(reg: Registry, user: User, query: Query) -> list[Item]:
            await asyncio.sleep(0)  # really async
            return list(reg.items.values())

        # Stub the rest with simple syncs.
        def _noop_id(reg: Registry, user: User, id: str): ...
        def _noop_item(reg: Registry, user: User, item: Item): ...

        src = AppDataSource[Registry, Item](
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
        assert page.total == 1

    def test_async_get_id_is_awaited(self):
        async def get_id(item: Item) -> str:
            await asyncio.sleep(0)
            return f"async-{item.id}"

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppDataSource[Registry, Item](
            Registry,
            fetch=lambda *a: [],
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
            get_id=get_id,
        )
        # No app_context needed for get_id — it doesn't touch deps.
        _install_context(None)
        assert asyncio.run(src.get_id(Item(id="a", name="alpha"))) == "async-a"


# ----------------------------------------------------------------------------
# Missing registry → LookupError
# ----------------------------------------------------------------------------


class TestMissingRegistry:
    def test_lookup_error_when_registry_not_in_app_context(self):
        # Install a RequestContext whose AppContext does NOT contain the
        # registry key.
        set_request_context(
            RequestContext(user=AnonymousUser(), app_context=AppContext({}))
        )
        src = _sync_source()
        with pytest.raises(LookupError):
            asyncio.run(src.fetch(Query()))


# ----------------------------------------------------------------------------
# `get_id` default and override
# ----------------------------------------------------------------------------


class TestGetId:
    def test_default_reads_id_field_on_pydantic_model(self):
        _install_context(None)
        src = _sync_source()
        assert asyncio.run(src.get_id(Item(id="a", name="alpha"))) == "a"

    def test_default_reads_id_key_on_dict(self):
        # Same default behaviour as SimpleDataSource: attribute first,
        # dict-key fallback via value_of.
        _install_context(None)

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppDataSource[Registry, dict](
            Registry,
            fetch=lambda *a: [],
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
        )
        assert asyncio.run(src.get_id({"id": "x", "name": "X"})) == "x"

    def test_override_takes_precedence(self):
        _install_context(None)

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppDataSource[Registry, Item](
            Registry,
            fetch=lambda *a: [],
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
            get_id=lambda item: f"prefix:{item.id}",
        )
        assert asyncio.run(src.get_id(Item(id="a", name="alpha"))) == "prefix:a"


# ----------------------------------------------------------------------------
# fetch wrapping: list → Page, Page → Page (untouched)
# ----------------------------------------------------------------------------


class TestFetchWrapping:
    def test_list_return_is_wrapped_into_page(self):
        reg = Registry(items={"a": Item(id="a", name="alpha")})
        _install_context(reg)
        src = _sync_source()
        page = asyncio.run(src.fetch(Query()))
        assert isinstance(page, Page)
        assert page.total == 1  # equals len(items) per wrapping rule

    def test_page_return_is_passed_through_unchanged(self):
        # When fetch already returns a Page (e.g. when the caller needs an
        # accurate total distinct from len(items)), AppDataSource hands it
        # back as-is.
        reg = Registry(items={"a": Item(id="a", name="alpha")})

        def fetch(reg: Registry, user: User, query: Query) -> Page[Item]:
            # `total=42` is intentionally different from `len(items)` —
            # this is exactly the case the pass-through path is for.
            return Page(items=list(reg.items.values()), total=42)

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppDataSource[Registry, Item](
            Registry,
            fetch=fetch,
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
        )
        _install_context(reg)
        page = asyncio.run(src.fetch(Query()))
        assert page.total == 42
        assert len(page.items) == 1


# ----------------------------------------------------------------------------
# User flows through
# ----------------------------------------------------------------------------


class TestUserPassthrough:
    def test_custom_user_arrives_in_function(self):
        seen: list[User] = []
        user = AuthenticatedUser(display_name="Bob")

        def fetch(reg: Registry, u: User, query: Query) -> list[Item]:
            seen.append(u)
            return []

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppDataSource[Registry, Item](
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

        def fetch(reg: Registry, u: User, query: Query) -> list[Item]:
            seen.append(u)
            return []

        def _noop_id(*a): ...
        def _noop_item(*a): ...

        src = AppDataSource[Registry, Item](
            Registry,
            fetch=fetch,
            find_by_id=_noop_id,
            get_by_id=_noop_id,
            create=_noop_item,
            update=_noop_item,
            delete=_noop_item,
            delete_by_id=_noop_id,
        )
        _install_context(Registry())  # no user → AnonymousUser default
        asyncio.run(src.fetch(Query()))
        assert isinstance(seen[0], AnonymousUser)
