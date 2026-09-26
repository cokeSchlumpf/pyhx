"""In-memory :class:`DataSource` implementation."""

from ._query import apply_query, value_of
from .query import Query
from .source import DataSource, Page


class SimpleDataSource[T](DataSource[T]):
    """In-memory ``DataSource`` over a list. Filtering, sorting, and
    pagination run in Python against the data passed at construction —
    fine for tests, fixtures, and small datasets; reach for a
    database-backed source once you grow past a few thousand items.

    Items are addressed by string key. Attribute access is tried first
    (Pydantic models, dataclasses, plain classes); ``dict`` items fall
    back to key lookup. ``get_id`` reads ``id_field`` (default ``"id"``)
    the same way.

    The class implements the full :class:`DataSource` protocol — read
    operations plus :meth:`create` / :meth:`delete` / :meth:`delete_by_id`
    / :meth:`update`. Mutations are applied to the underlying list in
    place, so callers that retain a reference to the original list will
    see the same changes.
    """

    def __init__(self, data: list[T], *, id_field: str = "id") -> None:
        """Wrap ``data`` as a queryable source.

        Parameters
        ----------
        data : list[T]
            The items to serve. Held by reference; mutating the underlying
            list — either directly or through the source's own write
            methods — is visible to subsequent ``fetch`` calls.
        id_field : str, default "id"
            Name of the attribute / dict key used by :meth:`get_id` to
            address individual items.
        """
        self._data = data
        self._id_field = id_field

    async def fetch(self, query: Query) -> Page[T]:
        """Apply ``query`` against the wrapped sequence and return one page.

        Filter is evaluated first (no item is touched twice), then sort
        is applied (stable, lowest-priority first so the highest dominates),
        then ``offset`` / ``limit`` carve out the page. ``total`` reflects
        the post-filter count — paging-aware UI uses it for "page X of Y".

        Parameters
        ----------
        query : Query
            Sort, filter, and paging spec to apply.

        Returns
        -------
        Page[T]
            The items on this page plus the post-filter total.
        """
        items, total = apply_query(self._data, query)
        return Page(items=items, total=total)

    async def get_id(self, item: T) -> str:
        """Return the value of ``item.<id_field>`` coerced to ``str``."""
        return str(value_of(item, self._id_field))

    async def find_by_id(self, id: str) -> T | None:
        """Linear scan for the item whose :meth:`get_id` equals ``id``.

        ``O(N)`` in the size of the wrapped sequence — fine for the
        tests/fixtures scale this class is meant for; reach for a
        backend-indexed source once linear lookup hurts.
        """
        for item in self._data:
            if await self.get_id(item) == id:
                return item
        return None

    async def get_by_id(self, id: str) -> T:
        """Strict variant of :meth:`find_by_id` — raises on a miss.

        Raises
        ------
        KeyError
            If no item with the given ``id`` exists in the wrapped
            sequence.
        """
        item = await self.find_by_id(id)
        if item is None:
            raise KeyError(id)
        return item

    async def create(self, item: T) -> None:
        """Append ``item`` to the wrapped list.

        Raises
        ------
        KeyError
            If an item with the same id already exists. The flat source
            keys items by :meth:`get_id`; a duplicate would shadow the
            existing entry on subsequent reads, so the conflict is
            treated as a programming error.
        """
        new_id = await self.get_id(item)
        if await self.find_by_id(new_id) is not None:
            raise KeyError(f"id already in use: {new_id}")
        self._data.append(item)

    async def delete(self, item: T) -> None:
        """Remove the entry whose id matches ``item``'s id.

        Convenience wrapper around :meth:`delete_by_id` — useful when
        the caller already has the full item in hand. Note that identity
        is checked by id, not by object identity: passing a freshly
        constructed item with the right id works.
        """
        await self.delete_by_id(await self.get_id(item))

    async def delete_by_id(self, id: str) -> None:
        """Drop the item with the given ``id`` from the wrapped list.

        Raises
        ------
        KeyError
            If no item with the given ``id`` exists.
        """
        for idx, existing in enumerate(self._data):
            if await self.get_id(existing) == id:
                del self._data[idx]
                return
        raise KeyError(id)

    async def update(self, item: T) -> None:
        """Replace the entry whose id matches ``item``'s id with ``item``.

        Raises
        ------
        KeyError
            If no item with the given ``id`` exists. ``update`` is
            insert-or-fail, not upsert — call :meth:`create` to add a
            new row.
        """
        target_id = await self.get_id(item)
        for idx, existing in enumerate(self._data):
            if await self.get_id(existing) == target_id:
                self._data[idx] = item
                return
        raise KeyError(target_id)
