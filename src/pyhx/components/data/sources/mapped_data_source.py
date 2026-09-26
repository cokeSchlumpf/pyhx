"""Generic mapping adapters for data sources.

Wraps a source of type ``A`` and exposes it as a source of type ``B`` via
two async mapping functions (``A → B`` and ``B → A``). An optional async
``map_query`` lets the wrapper translate outer-facing field names to the
inner source's vocabulary — sort keys, filter keys, and any other
``Query``-level state.

Four variants ship together so the type tells the truth about
mutability:

* :class:`MappedReadOnlyDataSource` / :class:`MappedDataSource` — flat.
* :class:`MappedReadOnlyHierarchicalDataSource` /
  :class:`MappedHierarchicalDataSource` — hierarchical.

IDs are opaque strings and pass through untouched, so
``outer.get_id(b) == inner.get_id(map_reverse(b))`` and
``find_by_id`` / ``get_by_id`` round-trip cleanly across the boundary.
"""

from collections.abc import Awaitable, Callable

from .source import (
    DataSource,
    HierarchicalDataSource,
    HierarchicalPage,
    Node,
    Page,
    Query,
    ReadOnlyDataSource,
    ReadOnlyHierarchicalDataSource,
)

type MapFn[A, B] = Callable[[A], Awaitable[B]]
"""Async mapping function from one item type to another."""

type QueryMapFn = Callable[[Query], Awaitable[Query]]
"""Async ``Query`` translator — typically remaps sort/filter field names."""


class MappedReadOnlyDataSource[A, B](ReadOnlyDataSource[B]):
    """Wraps a :class:`ReadOnlyDataSource` of ``A`` as a source of ``B``."""

    def __init__(
        self,
        source: ReadOnlyDataSource[A],
        map_forward: MapFn[A, B],
        map_reverse: MapFn[B, A],
        map_query: QueryMapFn | None = None,
    ) -> None:
        self._source = source
        self._map_forward = map_forward
        self._map_reverse = map_reverse
        self._map_query = map_query

    async def fetch(self, query: Query) -> Page[B]:
        inner_query = await self._map_query(query) if self._map_query else query
        page_a = await self._source.fetch(inner_query)
        items_b = [await self._map_forward(item) for item in page_a.items]
        return Page(items=items_b, total=page_a.total)

    async def get_id(self, item: B) -> str:
        return await self._source.get_id(await self._map_reverse(item))

    async def find_by_id(self, id: str) -> B | None:
        item_a = await self._source.find_by_id(id)
        return await self._map_forward(item_a) if item_a is not None else None

    async def get_by_id(self, id: str) -> B:
        return await self._map_forward(await self._source.get_by_id(id))


class MappedDataSource[A, B](MappedReadOnlyDataSource[A, B], DataSource[B]):
    """Mutable counterpart of :class:`MappedReadOnlyDataSource`."""

    def __init__(
        self,
        source: DataSource[A],
        map_forward: MapFn[A, B],
        map_reverse: MapFn[B, A],
        map_query: QueryMapFn | None = None,
    ) -> None:
        super().__init__(source, map_forward, map_reverse, map_query)
        self._source: DataSource[A] = source

    async def create(self, item: B) -> None:
        await self._source.create(await self._map_reverse(item))

    async def delete(self, item: B) -> None:
        await self._source.delete(await self._map_reverse(item))

    async def delete_by_id(self, id: str) -> None:
        await self._source.delete_by_id(id)

    async def update(self, item: B) -> None:
        await self._source.update(await self._map_reverse(item))


class MappedReadOnlyHierarchicalDataSource[A, B](ReadOnlyHierarchicalDataSource[B]):
    """Wraps a hierarchical source of ``A`` as one of ``B``.

    ``Node.count`` is preserved verbatim — field renames don't change
    cardinality, and the inner source already computed the filter-aware
    count against the (possibly translated) query.
    """

    def __init__(
        self,
        source: ReadOnlyHierarchicalDataSource[A],
        map_forward: MapFn[A, B],
        map_reverse: MapFn[B, A],
        map_query: QueryMapFn | None = None,
    ) -> None:
        self._source = source
        self._map_forward = map_forward
        self._map_reverse = map_reverse
        self._map_query = map_query

    async def fetch(
        self, query: Query, parent: str | None = None
    ) -> HierarchicalPage[B]:
        inner_query = await self._map_query(query) if self._map_query else query
        page_a = await self._source.fetch(inner_query, parent=parent)
        nodes_b = [
            Node(item=await self._map_forward(node.item), count=node.count)
            for node in page_a.items
        ]
        return HierarchicalPage(items=nodes_b, total=page_a.total)

    async def get_id(self, item: B) -> str:
        return await self._source.get_id(await self._map_reverse(item))

    async def find_by_id(self, id: str) -> B | None:
        item_a = await self._source.find_by_id(id)
        return await self._map_forward(item_a) if item_a is not None else None

    async def get_by_id(self, id: str) -> B:
        return await self._map_forward(await self._source.get_by_id(id))


class MappedHierarchicalDataSource[A, B](
    MappedReadOnlyHierarchicalDataSource[A, B], HierarchicalDataSource[B]
):
    """Mutable counterpart of :class:`MappedReadOnlyHierarchicalDataSource`."""

    def __init__(
        self,
        source: HierarchicalDataSource[A],
        map_forward: MapFn[A, B],
        map_reverse: MapFn[B, A],
        map_query: QueryMapFn | None = None,
    ) -> None:
        super().__init__(source, map_forward, map_reverse, map_query)
        self._source: HierarchicalDataSource[A] = source

    async def create(self, item: B) -> None:
        await self._source.create(await self._map_reverse(item))

    async def delete(self, item: B) -> None:
        await self._source.delete(await self._map_reverse(item))

    async def delete_by_id(self, id: str) -> None:
        await self._source.delete_by_id(id)

    async def update(self, item: B) -> None:
        await self._source.update(await self._map_reverse(item))
