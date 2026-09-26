"""``HierarchicalDataSource`` adapter for request-scoped, dependency-injected domain operations.

Hierarchical sibling of :mod:`.app_data_source` — same shape, same
dispatch semantics, just hits the
:class:`~.source.HierarchicalDataSource` /
:class:`~.source.ReadOnlyHierarchicalDataSource` protocols. ``fetch``
carries the extra ``parent`` axis and returns a
:class:`HierarchicalPage[T]` whose items are :class:`Node[T]`
(item + child-count).

See :mod:`.app_data_source` for the full rationale and the four-class
pattern (read-only ABC + read-only fn-passing + mutating ABC +
mutating fn-passing).
"""

import inspect
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from commons.users import User

from pyhx.core.request_context import RequestContext

from .app_data_source import _default_get_id
from .source import (
    HierarchicalDataSource,
    HierarchicalPage,
    Query,
    ReadOnlyHierarchicalDataSource,
)


class AppReadOnlyHierarchicalDataSourceBase[R, T](
    ReadOnlyHierarchicalDataSource[T], ABC
):
    """Abstract :class:`ReadOnlyHierarchicalDataSource` with dependency-injected operations.

    Hierarchical analogue of :class:`AppReadOnlyDataSourceBase`.
    ``do_fetch`` receives an extra ``parent`` argument and must return
    a :class:`HierarchicalPage[T]` — no list-wrapping convenience,
    since the :class:`Node[T]` child-count policy is part of the
    domain contract.
    """

    def __init__(self, registry_type: type[R]) -> None:
        """Pin the registry-type key used to pull the registry per request."""
        self._registry_type = registry_type

    # --- Abstract operations — implement these in your subclass --------------

    @abstractmethod
    async def do_fetch(
        self, registry: R, user: User, query: Query, parent: str | None
    ) -> HierarchicalPage[T]:
        """Return one level of the tree.

        ``parent=None`` means the root level. Returns a
        :class:`HierarchicalPage[T]` whose items are :class:`Node[T]`;
        each node's ``count`` drives whether the UI shows an expand
        affordance.
        """

    @abstractmethod
    async def do_find_by_id(self, registry: R, user: User, id: str) -> T | None:
        """Return the item with ``id``, or ``None`` if it doesn't exist."""

    @abstractmethod
    async def do_get_by_id(self, registry: R, user: User, id: str) -> T:
        """Return the item with ``id``. Raise when missing."""

    async def do_get_id(self, item: T) -> str:
        """Read the id off ``item``. Defaults to the ``"id"`` field — override if needed."""
        return _default_get_id(item)

    # --- Dispatch core -------------------------------------------------------

    def _resolve_deps(self) -> tuple[R, User]:
        """Pull ``(registry, user)`` from the current request context.

        Raises :class:`LookupError` (propagated from
        :meth:`AppContext.get`) if no entry of ``self._registry_type``
        is registered on the WebApp.
        """
        ctx = RequestContext.get()
        registry = ctx.app_context.get(self._registry_type)
        return registry, ctx.user

    async def _dispatch(self, fn: Callable[..., Awaitable[Any]], *args: Any) -> Any:
        """Await ``fn(registry, user, *args)``.

        ``fn`` is always one of the ``do_*`` coroutine methods, so the
        call is unconditionally awaited.
        """
        registry, user = self._resolve_deps()
        return await fn(registry, user, *args)

    @staticmethod
    async def _await_if_needed(value: Any) -> Any:
        """Await ``value`` if it's an awaitable; pass it through otherwise.

        Used by the function-passing concrete subclasses to bridge their
        stored sync-or-async callables into the ``async def do_*``
        contract.
        """
        if inspect.isawaitable(value):
            return await value
        return value

    # --- Protocol implementations — delegate to do_* -------------------------

    async def fetch(
        self, query: Query, parent: str | None = None
    ) -> HierarchicalPage[T]:
        # No list-wrapping — the operation returns HierarchicalPage[T]
        # directly. See ``do_fetch`` for the child-count rationale.
        return await self._dispatch(self.do_fetch, query, parent)

    async def get_id(self, item: T) -> str:
        return await self.do_get_id(item)

    async def find_by_id(self, id: str) -> T | None:
        return await self._dispatch(self.do_find_by_id, id)

    async def get_by_id(self, id: str) -> T:
        return await self._dispatch(self.do_get_by_id, id)


class AppReadOnlyHierarchicalDataSource[R, T](
    AppReadOnlyHierarchicalDataSourceBase[R, T]
):
    """A :class:`ReadOnlyHierarchicalDataSource` whose operations are passed as functions.

    Each constructor kwarg is a domain function with signature
    ``(registry, user, *protocol_args)``. Both sync and async functions
    are accepted; async results are awaited at call time. ``fetch``
    must return a :class:`HierarchicalPage[T]` directly.

    ``get_id`` defaults to reading the ``"id"`` field on the item;
    override when the id lives elsewhere or needs computation.
    """

    def __init__(
        self,
        registry_type: type[R],
        *,
        fetch: Callable[
            [R, User, Query, str | None],
            HierarchicalPage[T] | Awaitable[HierarchicalPage[T]],
        ],
        find_by_id: Callable[[R, User, str], T | None | Awaitable[T | None]],
        get_by_id: Callable[[R, User, str], T | Awaitable[T]],
        get_id: Callable[[T], str | Awaitable[str]] = _default_get_id,
    ) -> None:
        super().__init__(registry_type)
        self._fetch = fetch
        self._find_by_id = find_by_id
        self._get_by_id = get_by_id
        self._get_id = get_id

    async def do_fetch(
        self, registry: R, user: User, query: Query, parent: str | None
    ) -> HierarchicalPage[T]:
        return await self._await_if_needed(self._fetch(registry, user, query, parent))

    async def do_find_by_id(self, registry: R, user: User, id: str) -> T | None:
        return await self._await_if_needed(self._find_by_id(registry, user, id))

    async def do_get_by_id(self, registry: R, user: User, id: str) -> T:
        return await self._await_if_needed(self._get_by_id(registry, user, id))

    async def do_get_id(self, item: T) -> str:
        return await self._await_if_needed(self._get_id(item))


class AppHierarchicalDataSourceBase[R, T](
    AppReadOnlyHierarchicalDataSourceBase[R, T], HierarchicalDataSource[T]
):
    """Abstract :class:`HierarchicalDataSource` with dependency-injected operations.

    Extends :class:`AppReadOnlyHierarchicalDataSourceBase` with the
    four mutation abstract methods. Read methods, dispatch core, and
    ``__init__`` are inherited unchanged.

    Generic parameters:

    * ``R`` — the registry type. Must be present in the WebApp's
      :class:`AppContext`; missing → :class:`LookupError`.
    * ``T`` — the item type exposed via the
      :class:`HierarchicalDataSource` protocol.
    """

    @abstractmethod
    async def do_create(self, registry: R, user: User, item: T) -> None:
        """Persist ``item`` as a new entry."""

    @abstractmethod
    async def do_update(self, registry: R, user: User, item: T) -> None:
        """Update an existing entry from ``item``."""

    @abstractmethod
    async def do_delete(self, registry: R, user: User, item: T) -> None:
        """Delete the entry represented by ``item``."""

    @abstractmethod
    async def do_delete_by_id(self, registry: R, user: User, id: str) -> None:
        """Delete the entry with ``id``."""

    # --- Mutation protocol implementations — delegate to do_* ----------------

    async def create(self, item: T) -> None:
        await self._dispatch(self.do_create, item)

    async def update(self, item: T) -> None:
        await self._dispatch(self.do_update, item)

    async def delete(self, item: T) -> None:
        await self._dispatch(self.do_delete, item)

    async def delete_by_id(self, id: str) -> None:
        await self._dispatch(self.do_delete_by_id, id)


class AppHierarchicalDataSource[R, T](AppHierarchicalDataSourceBase[R, T]):
    """A :class:`HierarchicalDataSource` whose operations are passed as functions.

    Each constructor kwarg is a domain function with signature
    ``(registry, user, *protocol_args)``. Both sync and async functions
    are accepted; async results are awaited at call time. ``fetch``
    must return a :class:`HierarchicalPage[T]` directly.

    ``get_id`` defaults to reading the ``"id"`` field on the item;
    override when the id lives elsewhere or needs computation.
    """

    def __init__(
        self,
        registry_type: type[R],
        *,
        fetch: Callable[
            [R, User, Query, str | None],
            HierarchicalPage[T] | Awaitable[HierarchicalPage[T]],
        ],
        find_by_id: Callable[[R, User, str], T | None | Awaitable[T | None]],
        get_by_id: Callable[[R, User, str], T | Awaitable[T]],
        create: Callable[[R, User, T], None | Awaitable[None]],
        update: Callable[[R, User, T], None | Awaitable[None]],
        delete: Callable[[R, User, T], None | Awaitable[None]],
        delete_by_id: Callable[[R, User, str], None | Awaitable[None]],
        get_id: Callable[[T], str | Awaitable[str]] = _default_get_id,
    ) -> None:
        super().__init__(registry_type)
        self._fetch = fetch
        self._get_id = get_id
        self._find_by_id = find_by_id
        self._get_by_id = get_by_id
        self._create = create
        self._update = update
        self._delete = delete
        self._delete_by_id = delete_by_id

    async def do_fetch(
        self, registry: R, user: User, query: Query, parent: str | None
    ) -> HierarchicalPage[T]:
        return await self._await_if_needed(self._fetch(registry, user, query, parent))

    async def do_find_by_id(self, registry: R, user: User, id: str) -> T | None:
        return await self._await_if_needed(self._find_by_id(registry, user, id))

    async def do_get_by_id(self, registry: R, user: User, id: str) -> T:
        return await self._await_if_needed(self._get_by_id(registry, user, id))

    async def do_create(self, registry: R, user: User, item: T) -> None:
        await self._await_if_needed(self._create(registry, user, item))

    async def do_update(self, registry: R, user: User, item: T) -> None:
        await self._await_if_needed(self._update(registry, user, item))

    async def do_delete(self, registry: R, user: User, item: T) -> None:
        await self._await_if_needed(self._delete(registry, user, item))

    async def do_delete_by_id(self, registry: R, user: User, id: str) -> None:
        await self._await_if_needed(self._delete_by_id(registry, user, id))

    async def do_get_id(self, item: T) -> str:
        return await self._await_if_needed(self._get_id(item))
