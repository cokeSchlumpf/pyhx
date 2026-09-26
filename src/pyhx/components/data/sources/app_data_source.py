"""``DataSource`` adapter that bridges request-scoped, dependency-injected domain functions.

Domain code in app projects typically exposes operations as plain
functions whose first two parameters are explicit dependencies — a
registry ``R`` (holding repositories / services) and the acting
``User``. Those functions know nothing about HTTP or request scoping;
that's the point.

The UI primitives (:class:`~pyhx.components.data.data_table.DataTable`,
:class:`~pyhx.components.data.data_form.DataForm`, etc.) consume a
:class:`DataSource` / :class:`ReadOnlyDataSource` — a request-scoped,
no-explicit-dependencies protocol. This module is the bridge: at every
protocol call it resolves the registry from
:meth:`~pyhx.core.app_context.AppContext.get` and the user from
:attr:`~pyhx.core.request_context.RequestContext.user`, then invokes
the matching domain operation with ``(registry, user, *protocol_args)``.

Four shapes are offered against the same dispatch core:

* :class:`AppReadOnlyDataSourceBase` — abstract base for read-only
  sources. Subclass and implement three ``do_*`` methods.
* :class:`AppReadOnlyDataSource` — concrete read-only variant whose
  three operations are passed as constructor kwargs.
* :class:`AppDataSourceBase` — abstract base for mutating sources.
  Extends the read-only base and adds four mutation ``do_*`` methods.
* :class:`AppDataSource` — concrete mutating variant whose seven
  operations are passed as constructor kwargs.

The domain stays HTTP-agnostic; the UI gets a clean ``DataSource``.
"""

import inspect
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from commons.users import User

from pyhx.core.request_context import RequestContext

from ._query import value_of
from .query import Query
from .source import DataSource, Page, ReadOnlyDataSource


def _default_get_id(item: Any) -> str:
    """Default :meth:`AppReadOnlyDataSourceBase.do_get_id` — reads the ``"id"`` field.

    Uses :func:`value_of` to support attribute access (Pydantic models,
    dataclasses, plain classes) and dict-key lookup. Same default
    behaviour as :class:`SimpleDataSource`.
    """
    return str(value_of(item, "id"))


class AppReadOnlyDataSourceBase[R, T](ReadOnlyDataSource[T], ABC):
    """Abstract :class:`ReadOnlyDataSource` with dependency-injected operations.

    Subclass and implement the three abstract ``do_*`` methods. Each
    receives the registry (pulled from :class:`AppContext` by the
    ``registry_type`` passed to ``__init__``) and the acting
    :class:`User` (from the current :class:`RequestContext`), plus the
    protocol-level arguments. The methods are declared ``async def`` —
    inside, call sync code directly (just ``return value``) or
    ``await`` async code.

    Generic parameters:

    * ``R`` — the registry type. Must be present in the WebApp's
      :class:`AppContext`; missing → :class:`LookupError`.
    * ``T`` — the item type exposed via the :class:`ReadOnlyDataSource`
      protocol.
    """

    def __init__(self, registry_type: type[R]) -> None:
        """Pin the registry-type key used to pull the registry per request."""
        self._registry_type = registry_type

    # --- Abstract operations — implement these in your subclass --------------

    @abstractmethod
    async def do_fetch(
        self, registry: R, user: User, query: Query
    ) -> list[T] | Page[T]:
        """List items for ``query``. Return a plain list or a :class:`Page`.

        A plain list is auto-wrapped into a :class:`Page` with
        ``total = len(items)``. Return a :class:`Page` explicitly when
        ``total`` should differ from the visible items (paginated UI).
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

    async def fetch(self, query: Query) -> Page[T]:
        result = await self._dispatch(self.do_fetch, query)
        # Domain operations often return a plain list; wrap into a Page
        # so the protocol contract holds. See ``do_fetch`` for the
        # total-count semantics.
        if isinstance(result, list):
            return Page(items=result, total=len(result))
        return result

    async def get_id(self, item: T) -> str:
        return await self.do_get_id(item)

    async def find_by_id(self, id: str) -> T | None:
        return await self._dispatch(self.do_find_by_id, id)

    async def get_by_id(self, id: str) -> T:
        return await self._dispatch(self.do_get_by_id, id)


class AppReadOnlyDataSource[R, T](AppReadOnlyDataSourceBase[R, T]):
    """A :class:`ReadOnlyDataSource` whose operations are passed as functions.

    Each constructor kwarg is a domain function with signature
    ``(registry, user, *protocol_args)``. Both sync and async functions
    are accepted; async results are awaited at call time.

    ``get_id`` defaults to reading the ``"id"`` field on the item;
    override when the id lives elsewhere or needs computation.
    """

    def __init__(
        self,
        registry_type: type[R],
        *,
        fetch: Callable[
            [R, User, Query], list[T] | Page[T] | Awaitable[list[T] | Page[T]]
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
        self, registry: R, user: User, query: Query
    ) -> list[T] | Page[T]:
        return await self._await_if_needed(self._fetch(registry, user, query))

    async def do_find_by_id(self, registry: R, user: User, id: str) -> T | None:
        return await self._await_if_needed(self._find_by_id(registry, user, id))

    async def do_get_by_id(self, registry: R, user: User, id: str) -> T:
        return await self._await_if_needed(self._get_by_id(registry, user, id))

    async def do_get_id(self, item: T) -> str:
        return await self._await_if_needed(self._get_id(item))


class AppDataSourceBase[R, T](AppReadOnlyDataSourceBase[R, T], DataSource[T]):
    """Abstract :class:`DataSource` with dependency-injected operations.

    Extends :class:`AppReadOnlyDataSourceBase` with the four mutation
    abstract methods. Read methods, dispatch core, and ``__init__`` are
    inherited unchanged.

    Generic parameters:

    * ``R`` — the registry type. Must be present in the WebApp's
      :class:`AppContext`; missing → :class:`LookupError`.
    * ``T`` — the item type exposed via the :class:`DataSource`
      protocol.

    Examples
    --------
    >>> class ActivityGroupsSource(AppDataSourceBase[AppRegistry, ActivityGroup]):
    ...     def __init__(self) -> None:
    ...         super().__init__(AppRegistry)
    ...
    ...     async def do_fetch(self, registry, user, query):
    ...         return list_activity_groups(registry, user, query)
    ...
    ...     async def do_find_by_id(self, registry, user, id):
    ...         return find_activity_group_by_id(registry, user, id)
    ...
    ...     # ... do_get_by_id / do_create / do_update / do_delete / do_delete_by_id
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


class AppDataSource[R, T](AppDataSourceBase[R, T]):
    """A :class:`DataSource` whose operations are passed as functions.

    Each constructor kwarg is a domain function with signature
    ``(registry, user, *protocol_args)``. Both sync and async functions
    are accepted; async results are awaited at call time.

    ``get_id`` defaults to reading the ``"id"`` field on the item;
    override when the id lives elsewhere or needs computation.
    """

    def __init__(
        self,
        registry_type: type[R],
        *,
        fetch: Callable[
            [R, User, Query], list[T] | Page[T] | Awaitable[list[T] | Page[T]]
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
        self, registry: R, user: User, query: Query
    ) -> list[T] | Page[T]:
        return await self._await_if_needed(self._fetch(registry, user, query))

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
