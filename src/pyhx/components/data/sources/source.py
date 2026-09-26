"""The :class:`Query`/:class:`Page`/:class:`ReadOnlyDataSource` triple.

A :class:`ReadOnlyDataSource` accepts a :class:`Query` (sort + filter + paging) and
returns a :class:`Page` of items. The query model is intentionally flat —
``filter`` is a list of per-field :class:`Condition` objects combined
according to ``filter_mode`` — so it round-trips cleanly through the filter
drawer's form without any tree-walking.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from .query import Query


class Page[T](BaseModel):
    """One page of results returned by a :class:`ReadOnlyDataSource`.

    Attributes
    ----------
    items : list[T]
        The items on this page, post filter + sort + paging.
    total : int
        Total number of items in the source that match the filter,
        ignoring ``offset`` and ``limit``. Used to render pagination UI.
    """

    items: list[T]
    total: int


class ReadOnlyDataSource[T](ABC):
    """A queryable source of items of type ``T``.

    Implementations decide how to evaluate the query — e.g. an in-memory
    pass (:class:`SimpleDataSource`) or a database round-trip — but the
    contract is the same: take a :class:`Query`, return a :class:`Page`.
    """

    @abstractmethod
    async def fetch(self, query: Query) -> Page[T]:
        """Return the page matching ``query``."""

    @abstractmethod
    async def get_id(self, item: T) -> str:
        """Return a stable string identifier for ``item``.

        Used by the data table to key DOM nodes for row updates and by
        action buttons to address individual rows. Must be unique within
        the source.
        """

    @abstractmethod
    async def find_by_id(self, id: str) -> T | None:
        """Return the item whose :meth:`get_id` equals ``id``, or ``None``.

        The lookup-by-id counterpart to :meth:`fetch` — used when a UI
        action holds only the id round-tripped through the DOM (e.g. a
        row-action button, an htmx fragment payload) and needs the full
        ``T`` to act on. Implementations may hit the same backend as
        ``fetch``; callers should treat the call as potentially
        I/O-bound.

        Returns ``None`` for a missing id rather than raising — use
        :meth:`get_by_id` when "missing" should be treated as a bug.
        """

    @abstractmethod
    async def get_by_id(self, id: str) -> T:
        """Return the item whose :meth:`get_id` equals ``id``.

        Like :meth:`find_by_id` but treats "no such id" as a programming
        error rather than an expected outcome. Use this when the caller
        constructed ``id`` from a previously returned item (or from a
        link the same source generated) so a miss can only mean the
        source has been mutated underneath the caller.

        Raises
        ------
        KeyError
            If no item with the given ``id`` exists in the source.
        """


class DataSource[T](ReadOnlyDataSource[T]):
    """A :class:`ReadOnlyDataSource` that also supports mutation.

    Adds create / update / delete operations on top of the read methods.
    """

    @abstractmethod
    async def create(self, item: T) -> None: ...

    @abstractmethod
    async def delete(self, item: T) -> None: ...

    @abstractmethod
    async def delete_by_id(self, id: str) -> None: ...

    @abstractmethod
    async def update(self, item: T) -> None: ...


class Node[T](BaseModel):
    """One item in a hierarchical result, annotated with its child-count state.

    The data source returns ``Node[T]`` rather than bare ``T`` so the UI can
    decide, without a follow-up request, whether to render an expand affordance
    next to the item.

    Attributes
    ----------
    item : T
        The underlying domain object at this position in the tree.
    count : int | None
        Direct-child count state. ``0`` means the node is a leaf and has no
        children; a positive integer is the exact known count of direct
        children; ``None`` means the node is expandable but the count was not
        computed (typical when counting children is more expensive than the
        backend wants to pay eagerly).
    selectable : bool, default True
        Whether the row representing this node may be selected. The table's
        ``select_mode`` still governs whether selection happens at all and
        whether non-leaf rows participate; this flag lets a source veto an
        individual row on top of that — e.g. to exclude category headers
        from a leaf-selectable tree, or to grey out items the user lacks
        permission to pick.
    """

    item: T
    count: int | None
    selectable: bool = True

    def has_children(self) -> bool:
        return bool(self.count is None or self.count > 0)


class HierarchicalPage[T](BaseModel):
    """One page of sibling nodes at a single level of the tree.

    Returned by :meth:`ReadOnlyHierarchicalDataSource.fetch`. The shape mirrors
    :class:`Page` — same paging contract — but each entry is a :class:`Node`
    so the caller knows whether to render it as expandable.

    Attributes
    ----------
    items : list[Node[T]]
        The sibling nodes on this page, post filter + sort + paging applied
        within the parent's children.
    total : int
        Total number of children of the same parent matching the filter,
        ignoring ``offset`` and ``limit``. Used to render pagination UI within
        the level — *not* a transitive count across the whole subtree.
    """

    items: list[Node[T]]
    total: int


class ReadOnlyHierarchicalDataSource[T](ABC):
    """A queryable, lazy-loaded tree source of items of type ``T``.

    Like :class:`ReadOnlyDataSource` but with a ``parent`` axis: each
    call returns one level of the tree. The UI fetches the root level
    with ``parent=None`` and then re-fetches per-parent as the user
    expands nodes, so the source never has to materialise the whole
    tree up front.

    Filter, sort, and paging in :class:`Query` apply **per level** —
    i.e. to the direct children of ``parent``, not transitively across
    descendants. A common interpretation: filters narrow which siblings
    appear under each expanded parent, and ``total`` on the returned
    page is the count of matching siblings at that level.
    """

    @abstractmethod
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
            The id of the parent node, as previously produced by
            :meth:`get_id`. ``None`` requests the root level. Implementations
            should look the parent up internally rather than expecting a
            materialised ``T``.

        Returns
        -------
        HierarchicalPage[T]
            The matching children, each annotated with its own child-count
            state (see :class:`Node`).
        """
        ...

    @abstractmethod
    async def get_id(self, item: T) -> str:
        """Return a stable string identifier for ``item``.

        Used by the UI to key DOM nodes and to round-trip the parent id on
        expansion requests. Must be unique across the whole tree (not just
        within one level), because expansion of any node sends only this id
        back to :meth:`fetch`.
        """

    @abstractmethod
    async def find_by_id(self, id: str) -> T | None:
        """Return the item whose :meth:`get_id` equals ``id``, or ``None``.

        Tree-wide lookup — not restricted to a single level. Used when a
        UI action holds only the id round-tripped through the DOM (e.g.
        an on-select callback, a row-action button) and needs the full
        ``T`` to act on. Implementations may hit the same backend as
        :meth:`fetch`; callers should treat the call as potentially
        I/O-bound.

        Returns ``None`` for a missing id — use :meth:`get_by_id` when
        "missing" should be treated as a bug.
        """

    @abstractmethod
    async def get_by_id(self, id: str) -> T:
        """Strict variant of :meth:`find_by_id` — raises on a miss.

        Use when the caller constructed ``id`` from a previously
        returned item (or from a link the same source generated) so a
        miss can only mean the source has been mutated underneath the
        caller.

        Raises
        ------
        KeyError
            If no item with the given ``id`` exists in the source.
        """


class HierarchicalDataSource[T](ReadOnlyHierarchicalDataSource[T]):
    """A :class:`ReadOnlyHierarchicalDataSource` that also supports mutation.

    Adds create / update / delete operations on top of the read methods.
    """

    @abstractmethod
    async def create(self, item: T) -> None: ...

    @abstractmethod
    async def delete(self, item: T) -> None: ...

    @abstractmethod
    async def delete_by_id(self, id: str) -> None: ...

    @abstractmethod
    async def update(self, item: T) -> None: ...
