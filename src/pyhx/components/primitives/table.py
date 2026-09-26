"""The ``table`` primitive: a CSS-grid ``<table>`` with hx-flavoured child tags.

The module exposes a single public entry point — the :data:`table` factory. Call
or subscript it to build a table (``table(...)`` / ``table[...]``) and use its
attributes for the child tags (``table.thead`` / ``table.tbody`` / ``table.tr`` /
``table.th`` / ``table.td`` …). The cell and row tags accept hx custom props
(``kind``, ``is_sort``, ``is_selected``, ``level`` …) that resolve to BEM
classnames or ARIA attributes at render time.

Layout is driven by CSS custom properties on the ``<table>`` — chiefly
``--hx-table--cols`` (the grid track list). Column resizing (``resize_handle``)
is wired up client-side by ``pyhx.table.js``.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

import htpy as y
from markupsafe import Markup

from ...core.primitives import classnames as cx
from ...core.primitives import merge_styles
from ..view_model import Color, Pct
from ._element import _HxElement, _KxSimpleElementFactory
from .button import button
from .icon import icon

#: Semantic cell kinds. Each renders as a ``hx-table__cell--{kind}`` modifier
#: that aligns/styles the cell (e.g. ``numeric`` right-aligns with tabular
#: figures, ``empty`` spans all columns for an empty-state message).
CellKind = Literal[
    "layout", "list", "numeric", "date", "boolean", "actions", "empty", "text"
]

#: Active sort direction for a header cell — renders a trailing chevron icon.
SortDirection = Literal["asc", "desc"]


@dataclass(frozen=True)
class StackChartItem:
    color: Color
    title: str
    percent: Pct


class _KxTable(_HxElement):
    """The ``<table class="hx-table">`` primitive and its scroll wrapper.

    Renders a ``<div class="hx-table__wrapper">`` around a
    ``<table class="hx-table">`` whose column tracks come from the
    ``--hx-table--cols`` custom property. Built via the :data:`table` factory —
    ``table(...)`` sets options and ``table[...]`` supplies the child rows.
    """

    def __init__(
        self,
        *,
        column_widths: str | None = None,
        fullscreen: bool = False,
        is_tree: bool = False,
        scrollable: bool = False,
        controls: y.Node | None = None,
        children: y.Node | None = None,
        table_kwargs: Mapping[str, y.Attribute] | None = None,
        **kwargs: y.Attribute,
    ) -> None:
        """Configure the table.

        Args:
            column_widths: Space-separated CSS grid track list for the columns
                (e.g. ``"2fr 1fr 120px"``), assigned to ``--hx-table--cols``.
                When ``None`` the table auto-flows columns at
                ``minmax(142px, 1fr)`` each.
            fullscreen: Render the wrapper as a fixed, full-viewport overlay
                (``hx-table--fullscreen``).
            is_tree: Mark the ``<table>`` as ``role="treegrid"`` and prepend a
                leading expand-column track whose width scales with the deepest
                row ``level``. Requires ``column_widths`` (raises otherwise).
            scrollable: Wrap the ``<table>`` in a ``hx-table__scroll-container``
                (``overflow: auto``) so a table wider (or taller) than its box
                scrolls within a bordered container instead of overflowing its
                parent. The ``controls`` toolbar stays a direct child of the
                wrapper — it doesn't scroll with the body. Ignored while
                ``fullscreen`` is set (the fixed overlay is already the scroll
                box). Note: the container re-anchors the sticky header to its
                own top (``--hx-table--sticky-top: 0``).
            controls: Optional node rendered above the table inside the wrapper
                (typically a ``table.toolbar[...]``).
            children: Table body content; normally supplied via ``table[...]``
                rather than passed here.
            table_kwargs: Extra attributes forwarded to the inner ``<table>``
                element (``**kwargs`` go on the wrapper ``<div>`` instead).
            **kwargs: Extra attributes for the wrapper ``<div>``.

        Raises:
            ValueError: If ``is_tree`` is set without ``column_widths``.
        """
        if is_tree and column_widths is None:
            raise ValueError(
                "A tree table (is_tree=True) requires explicit `column_widths`: "
                "the leading expand-column track can only be prepended to a fixed "
                "track list, not the auto-flow columns used when column_widths is None."
            )

        self._column_widths = column_widths
        self._fullscreen = fullscreen
        self._is_tree = is_tree
        self._scrollable = scrollable
        self._controls = controls

        self._children = children
        self._table_kwargs = table_kwargs or {}
        self._kwargs = kwargs or {}

    def _render(self) -> y.Node:
        if self._column_widths is None:
            columns_style = "--hx-table--grid-auto-flow: column; --hx-table--auto-cols: minmax(142px, 1fr)"
        else:
            cols = self._column_widths
            if self._is_tree:
                # Reserve a leading track for the row's expand toggle; its width
                # scales with tree depth (see --hx-table--actual-expand-column-width).
                cols = f"var(--hx-table--actual-expand-column-width) {cols}"
            columns_style = f"--hx-table--cols: {cols}"

        table_kwargs = dict(self._table_kwargs)
        if self._is_tree:
            # role goes on the <table> (.hx-table) — the treegrid CSS keys off it
            # there, not on the wrapper div.
            table_kwargs["role"] = "treegrid"

        table_el = y.table(class_="hx-table", style=columns_style, **table_kwargs)[
            self._children
        ]
        # In fullscreen the wrapper itself is the scroll box (position: fixed;
        # overflow: auto), so an inner scroll container would just nest a second
        # scrollbar — skip the wrap there.
        if self._scrollable and not self._fullscreen:
            table_el = y.div(class_="hx-table__scroll-container")[table_el]

        return y.div(
            **cx(
                {
                    "hx-table__wrapper": True,
                    "hx-table--fullscreen": self._fullscreen,
                },
                **self._kwargs,
            )
        )[
            self._controls,
            table_el,
        ]


class _KxTableCell(_HxElement):
    """A table cell (``<td>``/``<th>``) whose hx custom props map to classnames.

    ``kind`` renders as a ``hx-table__cell--{kind}`` modifier alongside the
    base ``hx-table__cell`` class, the same way ``_KxTable`` maps
    ``fullscreen`` to ``hx-table--fullscreen``.
    """

    def __init__(
        self,
        element: y.Element,
        *args: Mapping[str, y.Attribute],
        kind: CellKind | None = None,
        span: int | None = None,
        children: y.Node | None = None,
        **kwargs: y.Attribute,
    ) -> None:
        if kind == "empty" and span is not None:
            raise ValueError(
                'kind="empty" already spans every column; drop `span` '
                "(the two are mutually exclusive)."
            )
        self._element = element
        self._args = args
        self._kind = kind
        self._span = span
        self._children = children
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        kwargs = dict(self._kwargs)
        if self._span is not None:
            kwargs = merge_styles({"--hx-table--cell-span": str(self._span)}, **kwargs)
        return self._element(
            *self._args,
            **cx(
                {
                    "hx-table__cell": True,
                    f"hx-table__cell--{self._kind}": self._kind is not None,
                },
                **kwargs,
            ),
        )[self._children]


class _KxTableHeaderCell(_KxTableCell):
    """A header cell (``<th>``) — a data cell plus header-specific attributes.

    Inherits the shared cell behaviour (``kind`` → ``hx-table__cell--{kind}``)
    and layers on sort/filter state, which render as trailing icons after the
    header content (chevron for the active sort direction, funnel when a filter
    is applied). Add further header-only props here as they arrive.

    The content (label + icons) is wrapped in a ``hx-table__cell-content`` span so
    the label and icons align on a single inline-flex baseline — mirroring the
    ``thead th a`` treatment in the data table.
    """

    def __init__(
        self,
        *args: Mapping[str, y.Attribute],
        is_sort: SortDirection | None = None,
        is_filter: bool = False,
        kind: CellKind | None = None,
        span: int | None = None,
        children: y.Node | None = None,
        **kwargs: y.Attribute,
    ) -> None:
        self._is_sort = is_sort
        self._is_filter = is_filter
        super().__init__(y.th, *args, kind=kind, span=span, children=children, **kwargs)

    def _render(self) -> y.Node:
        self._children = y.span(class_="hx-table__cell-content")[
            self._children,
            icon("chevron-up") if self._is_sort == "asc" else None,
            icon("chevron-down") if self._is_sort == "desc" else None,
            icon("filter") if self._is_filter else None,
        ]
        return super()._render()


class _KxTableCellFactory:
    """Creates fresh :class:`_KxTableCell` instances so children never leak between renders."""

    def __init__(self, element: y.Element) -> None:
        self._element = element

    def __call__(
        self,
        *args: Mapping[str, y.Attribute],
        kind: CellKind | None = None,
        span: int | None = None,
        **kwargs: y.Attribute,
    ) -> _KxTableCell:
        """Build a data cell for this factory's element (``<td>``).

        Args:
            *args: Positional attribute mappings forwarded to the element.
            kind: Cell-kind modifier → ``hx-table__cell--{kind}``.
            span: Number of grid columns the cell spans (→
                ``grid-column: span N``). ``None`` spans a single column.
                Mutually exclusive with ``kind="empty"``.
            **kwargs: Extra HTML attributes.
        """
        return _KxTableCell(
            self._element, *args, kind=kind, span=span, children=None, **kwargs
        )

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        return self()[children]


class _KxTableHeaderCellFactory:
    """Creates fresh :class:`_KxTableHeaderCell` instances so children never leak between renders."""

    def __call__(
        self,
        *args: Mapping[str, y.Attribute],
        is_sort: SortDirection | None = None,
        is_filter: bool = False,
        kind: CellKind | None = None,
        span: int | None = None,
        **kwargs: y.Attribute,
    ) -> _KxTableHeaderCell:
        """Build a header cell (``<th>``).

        Args:
            *args: Positional attribute mappings forwarded to the ``<th>``.
            is_sort: Active sort direction — renders a trailing chevron
                (``"asc"`` up / ``"desc"`` down).
            is_filter: When ``True``, render a trailing funnel icon.
            kind: Cell-kind modifier (see :class:`_KxTableCell`); setting the
                same kind as the column aligns the heading to match it.
            span: Number of grid columns the cell spans (→
                ``grid-column: span N``). ``None`` spans a single column.
                Mutually exclusive with ``kind="empty"``.
            **kwargs: Extra HTML attributes.
        """
        return _KxTableHeaderCell(
            *args,
            is_sort=is_sort,
            is_filter=is_filter,
            kind=kind,
            span=span,
            children=None,
            **kwargs,
        )

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        return self()[children]


class _KxTableRow(_HxElement):
    """A table row (``<tr>``) whose hx custom props map to ARIA state.

    ``is_selected`` / ``is_expanded`` render as ``aria-selected`` /
    ``aria-expanded`` with a ``"true"`` / ``"false"`` value; ``level`` renders as
    ``aria-level``. ``None`` omits the attribute entirely (ARIA needs the string
    value, not an HTML boolean attr).
    """

    def __init__(
        self,
        *args: Mapping[str, y.Attribute],
        is_selected: bool | None = None,
        is_expanded: bool | None = None,
        level: int | None = None,
        children: y.Node | None = None,
        **kwargs: y.Attribute,
    ) -> None:
        if is_selected is not None:
            kwargs["aria_selected"] = "true" if is_selected else "false"
        if is_expanded is not None:
            kwargs["aria_expanded"] = "true" if is_expanded else "false"
        if level is not None:
            kwargs["aria_level"] = level
        self._args = args
        self._children = children
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        return y.tr(*self._args, **self._kwargs)[self._children]


class _KxTableRowFactory:
    """Creates fresh :class:`_KxTableRow` instances so children never leak between renders."""

    def __call__(
        self,
        *args: Mapping[str, y.Attribute],
        is_selected: bool | None = None,
        is_expanded: bool | None = None,
        level: int | None = None,
        **kwargs: y.Attribute,
    ) -> _KxTableRow:
        """Build a table row (``<tr>``).

        Args:
            *args: Positional attribute mappings forwarded to the ``<tr>``.
            is_selected: Selection state → ``aria-selected`` (``"true"`` /
                ``"false"``); ``None`` omits it, leaving the row inert.
            is_expanded: Expansion state → ``aria-expanded``; ``None`` omits it
                for a leaf / non-expandable row.
            level: Tree depth → ``aria-level`` (1-based); indents the first cell
                in a tree table. ``None`` omits it.
            **kwargs: Extra HTML attributes.
        """
        return _KxTableRow(
            *args,
            is_selected=is_selected,
            is_expanded=is_expanded,
            level=level,
            children=None,
            **kwargs,
        )

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        return self()[children]


class _KxTableFactory:
    """Public entry point for the table primitive (the :data:`table` singleton).

    Call or subscript it to build a table (``table(...)`` / ``table[...]``), and
    use its attributes for the child tags:

    * ``thead`` / ``tbody`` / ``tfoot`` — plain htpy elements.
    * ``tr`` / ``th`` / ``td`` — hx elements accepting custom props (``kind``,
      ``is_sort``, ``is_selected``, ``level`` …).
    * ``toolbar`` / ``scroll_container`` — styled wrapper elements.

    :meth:`resize_handle` and :meth:`expand_and_collapse_button` build the
    interactive affordances a cell can carry.
    """

    def __init__(self) -> None:
        self.tbody = y.tbody
        self.td = _KxTableCellFactory(y.td)
        self.tfoot = y.tfoot
        self.th = _KxTableHeaderCellFactory()
        self.thead = y.thead
        self.tr = _KxTableRowFactory()

        self.scroll_container = _KxSimpleElementFactory("hx-table__scroll-container")
        self.toolbar = _KxSimpleElementFactory("hx-table__toolbar")

    def __call__(
        self,
        *,
        column_widths: str | None = None,
        fullscreen: bool = False,
        is_tree: bool = False,
        scrollable: bool = False,
        controls: y.Node | None = None,
        table_kwargs: Mapping[str, y.Attribute] | None = None,
        **kwargs: y.Attribute,
    ) -> _KxTable:
        """Build a :class:`_KxTable`. See :meth:`_KxTable.__init__` for the args."""
        return _KxTable(
            column_widths=column_widths,
            fullscreen=fullscreen,
            is_tree=is_tree,
            scrollable=scrollable,
            controls=controls,
            children=None,
            table_kwargs=table_kwargs,
            **kwargs,
        )

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        """``table[children]`` — build a default table and fill its body."""
        return self()[children]

    def expand_and_collapse_button(
        self,
        is_expanded: bool,
        *attrs: Mapping[str, y.Attribute],
        **kwargs: y.Attribute,
    ) -> y.Node:
        """A ghost expand/collapse toggle for a tree row's first cell.

        Renders a ``▼`` (expanded) or ``▶`` (collapsed) glyph. It's a
        ``.hx-button`` so the tree expand-column padding reset applies; wire the
        toggle behaviour (e.g. htmx attributes) through ``**kwargs``.

        Args:
            is_expanded: Whether the row is currently expanded (selects the glyph).
            *attrs: Positional attribute mappings forwarded to the button.
            **kwargs: Extra attributes (e.g. htmx handlers).
        """
        # ``button`` has ``Literal``-typed style params, so mypy rejects
        # unpacking a ``dict[str, Attribute]`` of caller attributes into it.
        # Positional ``*attrs`` mappings forward type-safely (htpy keeps their
        # keys literal); the keyword handlers go through ``Any`` so htpy still
        # applies the underscore→dash conversion (e.g. ``hx_post`` → ``hx-post``).
        handlers: dict[str, Any] = dict(kwargs)
        return button(
            (
                Markup("&blacktriangledown;")
                if is_expanded
                else Markup("&blacktriangleright;")
            ),
            *attrs,
            type="submit",
            variant="ghost",
            **handlers,
        )

    def resize_handle(
        self,
        col_idx: int = 0,
        title: str | None = None,
        *attrs: Mapping[str, y.Attribute],
        **kwargs: y.Attribute,
    ) -> y.Node:
        """A draggable column-resize handle for a header cell.

        Emitted as ``<span class="hx-table__col-resizer" data-col-idx=...>``;
        ``pyhx.table.js`` reads ``data-col-idx`` on drag to resize the matching
        ``--hx-table--cols`` track.

        Args:
            col_idx: Zero-based index of the column this handle resizes.
            title: Tooltip / accessible title.
            *attrs: Positional attribute mappings forwarded to the span.
            **kwargs: Extra HTML attributes.
        """
        return y.span(
            class_="hx-table__col-resizer",
            data_col_idx=col_idx,
            title=title,
            *attrs,  # noqa: B026 — htpy applies attr sources in call order; keep it
            **kwargs,
        )

    def stack_chart_cell(
        self,
        items: list[StackChartItem],
        span: int | None = None,
        overlay: y.Node | None = None,
        **kwargs: y.Attribute,
    ) -> y.Node:
        """A ``layout`` cell rendering a vertical stacked-bar chart.

        Each :class:`StackChartItem` becomes a segment whose height is its
        ``percent`` (0-1) of the cell and whose colour is its :class:`Color`.
        The cell carries no padding; the stack fills the full width and height,
        and the segments stack from the bottom up in list order. Each segment's
        ``title`` surfaces as a hover tooltip.

        Args:
            items: Segments to stack, bottom-up in list order.
            span: Columns to span (see :meth:`td`).
            overlay: Optional node rendered over the chart — the cell is its
                containing block, so an absolutely-positioned annotation (e.g. a
                reference line) can span the full cell (ignoring the chart's own
                insets) and sit at a fixed height.
            **kwargs: Extra attributes for the cell.
        """
        return self.td(kind="layout", span=span, **kwargs)[
            y.div(class_="hx-table__stack-chart")[
                [
                    y.div(
                        **cx(
                            "hx-table__stack-chart-item",
                            title=item.title,
                            style=(
                                f"--hx-stack-chart-item--color: {item.color.value}; "
                                f"--hx-stack-chart-item--height: {round(item.percent.percent)}%"
                            ),
                        )
                    )
                    for item in items
                ]
            ],
            overlay,
        ]


#: The table primitive. Import as ``from pyhx.components import table`` (or via
#: ``c.table``) and use ``table(...)`` / ``table[...]`` plus its child tags.
table = _KxTableFactory()
