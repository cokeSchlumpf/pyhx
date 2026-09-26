"""In-memory :class:`HierarchicalDataSource` implementation."""

from collections import defaultdict

from ._query import apply_query, count_matches, value_of
from .query import Query
from .source import HierarchicalDataSource, HierarchicalPage, Node


class SimpleHierarchicalDataSource[T](HierarchicalDataSource[T]):
    """In-memory ``HierarchicalDataSource`` over a flat adjacency-list.

    Each item carries an ``id`` and a ``parent_id`` (FK to self). Children
    of each parent are indexed once at construction time, so subsequent
    ``fetch`` calls only have to filter / sort / page the relevant slice.
    Suitable for tests, fixtures, and small datasets — reach for a real
    backend once you grow past a few thousand items.

    Items are addressed by string key. Attribute access is tried first
    (Pydantic models, dataclasses, plain classes); ``dict`` items fall
    back to key lookup. ``get_id`` reads ``id_field`` (default ``"id"``)
    the same way; the parent reference is read from ``parent_id_field``
    (default ``"parent_id"``).

    The class implements the full :class:`HierarchicalDataSource`
    protocol — read operations plus :meth:`create` / :meth:`delete` /
    :meth:`delete_by_id` / :meth:`update`. Mutations land on the
    underlying list *and* on the internal by-parent index, so the tree
    view stays consistent across subsequent ``fetch`` calls. Mutating
    the passed-in list directly (without going through the write
    methods) bypasses the index — see the constructor docstring.

    Semantic notes
    --------------
    * **Root items** are items whose ``parent_id`` is ``None``. They are
      returned by ``fetch(query, parent=None)``.
    * **``Node.count`` is always a known integer** (never ``None``). The
      data is in memory, so the exact child count is always computable.
    * **``count`` is filter-aware.** It reports how many direct children
      would survive the current ``query.filter`` if you expanded the node —
      so the disclosure ("3 children") matches what the user actually sees
      on expansion. Filters apply identically at every level the user
      descends into. Sort and paging do not affect ``count``.
    * **Orphans never appear.** An item whose ``parent_id`` doesn't match
      any other item's id is silently unreachable. There is no consistency
      check at construction or on mutation — deleting a node leaves its
      former children addressable via :meth:`find_by_id` but invisible to
      :meth:`fetch`.
    * **Cycles are not defended against.** Input must be acyclic; the
      class does not detect or reject loops.
    """

    def __init__(
        self,
        data: list[T],
        *,
        id_field: str = "id",
        parent_id_field: str = "parent_id",
    ) -> None:
        """Wrap ``data`` as a tree-shaped queryable source.

        Parameters
        ----------
        data : list[T]
            All items in the tree, flat. Held by reference; the
            child-by-parent index is built eagerly and is then kept in
            sync by the source's own write methods. Mutating the
            underlying list directly (``data.append(...)`` etc.) bypasses
            the index and leaves it stale — use :meth:`create` /
            :meth:`delete` / :meth:`delete_by_id` / :meth:`update`
            instead.
        id_field : str, default "id"
            Name of the attribute / dict key used by :meth:`get_id`.
        parent_id_field : str, default "parent_id"
            Name of the attribute / dict key holding the FK to the
            parent. ``None`` marks a root item.
        """
        self._data = data
        self._id_field = id_field
        self._parent_id_field = parent_id_field

        # O(N) once at construction → O(1) lookup per fetch.
        # Key is ``None`` for root items, ``str`` otherwise — matches the
        # ``parent`` parameter shape on :meth:`fetch`.
        self._by_parent: dict[str | None, list[T]] = defaultdict(list)
        for item in data:
            self._by_parent[self._parent_key(item)].append(item)

    async def fetch(
        self, query: Query, parent: str | None = None
    ) -> HierarchicalPage[T]:
        """Return one page of children at a single level of the tree.

        Parameters
        ----------
        query : Query
            Sort + filter + paging, applied to the direct children of
            ``parent``.
        parent : str | None
            Id of the parent node (as returned by :meth:`get_id`), or
            ``None`` for the root level.

        Returns
        -------
        HierarchicalPage[T]
            Matching children, each wrapped in :class:`Node` with its
            filter-aware direct-child count attached (see the class
            docstring for ``count`` semantics).
        """
        siblings = self._by_parent.get(parent, [])
        items, total = apply_query(siblings, query)
        nodes = [
            Node(
                item=it,
                count=count_matches(
                    self._by_parent.get(await self.get_id(it), []), query
                ),
            )
            for it in items
        ]
        return HierarchicalPage(items=nodes, total=total)

    async def get_id(self, item: T) -> str:
        """Return the value of ``item.<id_field>`` coerced to ``str``."""
        return str(value_of(item, self._id_field))

    async def find_by_id(self, id: str) -> T | None:
        """Linear scan across the wrapped tree for an item with this ``id``.

        ``O(N)`` in the total number of items — fine for the
        tests/fixtures scale this class is meant for. The scan walks the
        flat data sequence rather than the by-parent index, so an
        orphaned item (one whose ``parent_id`` points nowhere) is still
        addressable here even though it's invisible to :meth:`fetch`.
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
            tree (including orphans).
        """
        item = await self.find_by_id(id)
        if item is None:
            raise KeyError(id)
        return item

    async def create(self, item: T) -> None:
        """Append ``item`` to the tree and index it under its parent.

        The new item is placed in the per-parent bucket keyed by its
        current ``parent_id`` — so if that value matches an existing
        item's id, the new item becomes a direct child of that item on
        the next :meth:`fetch`. If the parent id points nowhere, the
        new item is an orphan: addressable via :meth:`find_by_id` but
        invisible to :meth:`fetch` (same policy as orphans loaded at
        construction).

        Raises
        ------
        KeyError
            If an item with the same id already exists anywhere in the
            tree.
        """
        new_id = await self.get_id(item)
        if await self.find_by_id(new_id) is not None:
            raise KeyError(f"id already in use: {new_id}")
        self._data.append(item)
        self._by_parent[self._parent_key(item)].append(item)

    async def delete(self, item: T) -> None:
        """Remove the entry whose id matches ``item``'s id.

        Convenience wrapper around :meth:`delete_by_id`. Children are
        *not* cascaded — see that method for the full policy.
        """
        await self.delete_by_id(await self.get_id(item))

    async def delete_by_id(self, id: str) -> None:
        """Drop the item with the given ``id`` from the tree.

        Children of the removed item are not cascaded: they remain in
        ``_data`` (and stay addressable via :meth:`find_by_id`) and
        still sit in ``_by_parent[id]``, so an explicit
        ``fetch(query, parent=id)`` will keep returning them. A natural
        root-down tree walk, however, can no longer reach that parent
        — so during normal browsing they behave like orphans.

        Raises
        ------
        KeyError
            If no item with the given ``id`` exists in the wrapped
            tree.
        """
        for idx, existing in enumerate(self._data):
            if await self.get_id(existing) == id:
                del self._data[idx]
                bucket = self._by_parent.get(self._parent_key(existing))
                if bucket is not None:
                    bucket.remove(existing)
                return
        raise KeyError(id)

    async def update(self, item: T) -> None:
        """Replace the entry whose id matches ``item``'s id with ``item``.

        Keeps the by-parent index consistent — if the new item's
        ``parent_id`` differs from the old item's, the entry is moved
        between buckets so subsequent ``fetch(parent=…)`` calls see it
        under the new parent.

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
                old_key = self._parent_key(existing)
                new_key = self._parent_key(item)
                self._data[idx] = item

                if old_key == new_key:
                    bucket = self._by_parent[old_key]
                    for j, b_item in enumerate(bucket):
                        if await self.get_id(b_item) == target_id:
                            bucket[j] = item
                            break
                else:
                    self._by_parent[old_key].remove(existing)
                    self._by_parent[new_key].append(item)
                return
        raise KeyError(target_id)

    def _parent_key(self, item: T) -> str | None:
        """Bucket key under which ``item`` lives in ``_by_parent``.

        Centralises the ``None``-or-``str(pid)`` coercion so every
        mutation path stays in lock-step with the index built in
        ``__init__``.
        """
        pid = value_of(item, self._parent_id_field)
        return None if pid is None else str(pid)
