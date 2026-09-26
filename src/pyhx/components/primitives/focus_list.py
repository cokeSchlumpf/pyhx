from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

import htpy as y

from pyhx.core.primitives import classnames

from ..view_model.columns import ColumnKind, ColumnWidth, Fixed, Flex
from .table import table as hx_table

FocusListVariant = Literal["cards", "plain", "table"]


@dataclass(frozen=True)
class FocusListColumn:
    """One column of the table variant.

    Describes how a column looks and is sized — its ``header`` content, its
    semantic ``kind`` (drives cell alignment via the data-table cell modifiers),
    and its ``width`` (``Flex`` / ``Fixed``, reused from the data tables). The
    set of columns is passed once to :meth:`_FocusList.table`, which derives the
    header row and the grid track string from it; body cells inherit their
    column's ``kind`` by position.
    """

    header: y.Node = ""
    kind: ColumnKind | None = None
    width: ColumnWidth = Flex()


@dataclass(frozen=True)
class FocusListCell:
    """One body cell. ``content`` is the cell body; ``colspan`` spans columns
    (an int, or ``"all"`` for the full width — e.g. the focused detail row);
    ``attrs`` are extra attributes for the ``<td>`` (e.g. ``class_``). A cell
    inherits its column's ``kind`` by position; set ``kind`` to override that
    (e.g. ``"layout"`` for a plain block cell that hosts its own layout)."""

    content: y.Node
    colspan: int | Literal["all"] | None = None
    kind: ColumnKind | None = None
    attrs: dict = field(default_factory=dict)


@dataclass(frozen=True)
class FocusListRow:
    """One body row: a stable ``id`` (also its ``view-transition-name``), its
    ``cells``, whether it is the ``active`` (focused) row, and extra ``attrs``
    forwarded onto the row's ``<tr>``.

    ``attrs`` is how a row opts into the clickable / selectable affordance:
    pass ``aria_selected="false"`` (cursor + hover tint) — or ``"true"`` (the
    selected tint) — alongside your own htmx (``hx_*``), exactly as the data
    tables do. The styling is CSS-only; the click behaviour is the caller's htmx.
    """

    id: str
    cells: Sequence[FocusListCell]
    active: bool = False
    attrs: dict = field(default_factory=dict)


class _FocusList:
    """Focus list — a list where selecting one item lifts it into focus while
    the rest dim and lock.

    Use the variant-specific public helpers, which pair a list with its matching
    item so the two can't be mismatched:

        focus_list.cards(...)  + focus_list.card_item(...)
        focus_list.plain(...)  + focus_list.plain_item(...)
        focus_list.table(columns, rows)  + focus_list.table_row / .table_cell

    The table variant is declarative: a set of ``table_column``\\ s (header +
    kind + width) is passed once to ``table``, which derives the header row and
    the column grid from it; rows are built from ``table_cell``\\ s. ``backdrop``
    (any variant) is passed to the list helper. The ``_list`` / ``_item`` /
    ``_cell`` methods are the shared internal machinery.
    """

    list_classname: str = "hx-focus-list"
    item_classname: str = "hx-focus-list__item"
    backdrop_classname: str = "hx-focus-list__backdrop"

    #
    # Internal machinery — shared by every variant.
    #

    def _list(
        self,
        variant: FocusListVariant,
        children: y.Node,
        *,
        backdrop: y.Node | None = None,
        header: y.Node | None = None,
        header_vtn: str | None = None,
        cols_css: str | None = None,
        **kwargs,
    ) -> y.Node:
        # The `table` variant renders real <table>/<tbody>/<tr>/<td> markup, but
        # laid out with CSS grid (see focus-list.css) so each row stays an
        # ordinary box — the lift, z-index and view-transition-name all behave
        # as in the other variants. A <div> can't live inside a <table>, so the
        # root is always a div: the backdrop sits beside the table, not in it.
        # The <table> carries `class="hx-table"` so it inherits the table
        # primitive's scoped CSS; `--hx-table--cols` lives on the <table> too.
        if variant == "table":
            # The header's `view-transition-name` is set *inline*, per instance
            # (``header_vtn``), rather than as a constant in CSS: two focus-list
            # tables on one page would otherwise share the same name, and
            # duplicate view-transition-names abort the *whole* transition for
            # every element on the page. The shared `view-transition-class`
            # (focus-list.css) still drives the header group's z-index.
            thead_attrs = (
                {"style": f"view-transition-name: {header_vtn};"} if header_vtn else {}
            )
            body: y.Node = y.table(
                class_="hx-table",
                style=f"--hx-table--cols: {cols_css};",
            )[
                hx_table.thead(**thead_attrs)[header] if header is not None else None,
                hx_table.tbody[children],
            ]
        else:
            body = children

        return y.div(
            **classnames(
                {
                    self.list_classname: True,
                    f"{self.list_classname}--variant-{variant}": True,
                },
                **kwargs,
            )
        )[backdrop, body]

    def _item(
        self,
        variant: FocusListVariant,
        children: y.Node,
        *,
        id: str,
        active: bool = False,
        **kwargs,
    ) -> y.Node:
        if active:
            kwargs["data-is-active"] = "true"

        attrs = classnames(self.item_classname, **kwargs)
        if variant == "table":
            return hx_table.tr(id=id, style=f"view-transition-name: {id}", **attrs)[
                children
            ]
        return y.div(id=id, style=f"view-transition-name: {id}", **attrs)[children]

    def _cell(
        self,
        content: y.Node,
        *,
        kind: ColumnKind | None = None,
        colspan: int | Literal["all"] | None = None,
        attrs: dict | None = None,
    ) -> y.Node:
        kw = dict(attrs) if attrs else {}

        # CSS grid means the native `colspan` is a no-op — translate it to a
        # `grid-column` span. "all" spans every column; an int spans that many.
        if colspan is not None:
            span = "1 / -1" if colspan == "all" else f"span {colspan}"
            style = kw.get("style")
            prefix = f"{style.rstrip().rstrip(';')}; " if style else ""
            kw["style"] = f"{prefix}grid-column: {span};"

        # "actions" cells isolate their own clicks so buttons inside don't each need their own stopPropagation. mirrors cell_click_attrs() in the data tables (components.data._table_helpers)
        if kind == "actions":
            kw["hx-on:click"] = "event.stopPropagation()"

        return hx_table.td(kind=kind, **kw)[content]

    @staticmethod
    def _columns_to_css_cols(columns: Sequence[FocusListColumn]) -> str:
        # Build the `--hx-table--cols` grid-track string from the column
        # widths. Unlike the data tables there is no trailing resizer track:
        # every track is content-independent (`minmax(min, fr)` / fixed) so the
        # header and each row-grid resolve to identical, aligned columns.
        tracks: list[str] = []
        for col in columns:
            w = col.width
            if isinstance(w, Flex):
                tracks.append(f"minmax({w.min_width}, {w.weight}fr)")
            elif isinstance(w, Fixed):
                tracks.append(w.width)
        return " ".join(tracks)

    def _render_row(
        self, row: FocusListRow, columns: Sequence[FocusListColumn]
    ) -> y.Node:
        cells: list[y.Node] = []
        col_idx = 0
        for cell in row.cells:
            # An explicit cell kind always wins. Otherwise a non-spanning cell
            # inherits its column's kind by position; a spanning cell maps to no
            # single column, so it carries no inherited kind.
            kind = cell.kind
            if kind is None and cell.colspan is None and col_idx < len(columns):
                kind = columns[col_idx].kind
            cells.append(
                self._cell(
                    cell.content,
                    kind=kind,
                    colspan=cell.colspan,
                    attrs=cell.attrs,
                )
            )

            if cell.colspan == "all":
                col_idx = len(columns)
            elif isinstance(cell.colspan, int):
                col_idx += cell.colspan
            else:
                col_idx += 1

        return self._item("table", cells, id=row.id, active=row.active, **row.attrs)

    #
    # Public API — one list + item pair per variant.
    #

    def cards(
        self, children: y.Node, *, backdrop: y.Node | None = None, **kwargs
    ) -> y.Node:
        """Spaced, rounded, shadowed cards. Pair with ``card_item``."""
        return self._list("cards", children, backdrop=backdrop, **kwargs)

    def card_item(
        self, children: y.Node, *, id: str, active: bool = False, **kwargs
    ) -> y.Node:
        return self._item("cards", children, id=id, active=active, **kwargs)

    def plain(
        self, children: y.Node, *, backdrop: y.Node | None = None, **kwargs
    ) -> y.Node:
        """Flush rows divided by a 1px rule; only the active row lifts. Pair with ``plain_item``."""
        return self._list("plain", children, backdrop=backdrop, **kwargs)

    def plain_item(
        self, children: y.Node, *, id: str, active: bool = False, **kwargs
    ) -> y.Node:
        return self._item("plain", children, id=id, active=active, **kwargs)

    def table_column(
        self,
        header: y.Node = "",
        *,
        kind: ColumnKind | None = None,
        width: ColumnWidth = Flex(),
    ) -> FocusListColumn:
        """Define a table column: ``header`` content, semantic ``kind`` (drives
        cell alignment), and ``width`` (``Flex`` / ``Fixed``)."""
        return FocusListColumn(header=header, kind=kind, width=width)

    def table(
        self,
        columns: Sequence[FocusListColumn],
        rows: Sequence[FocusListRow],
        *,
        id: str | None = None,
        backdrop: y.Node | None = None,
        header: bool = True,
        **kwargs,
    ) -> y.Node:
        """Real <table> markup laid out on a CSS grid, driven by ``columns``.

        ``columns`` (built with ``table_column``) define the header, the column
        grid (``--hx-table--cols`` is derived from their widths), and the kind
        each body cell inherits by position. ``rows`` are built with
        ``table_row`` / ``table_cell``. Set ``header=False`` to omit the header
        row.

        ``id`` namespaces the header's ``view-transition-name`` so several
        focus-list tables can share one page without their headers colliding
        (a duplicate name aborts the whole transition). Pass a stable, unique
        ``id`` per table — like the stable ``id`` each row already carries — so
        the header morphs smoothly across re-renders. When omitted, a fresh name
        is generated each render: still collision-free, but the header
        cross-fades instead of morphing (invisible for an unchanging header).
        """
        # Derive the column grid from the column widths. This is the single
        # source of truth for both header and rows; it's set as
        # `--hx-table--cols` on the `<table>`.
        cols_css = self._columns_to_css_cols(columns)

        header_vtn = f"hx-focus-list-header--{id if id else uuid4().hex}"
        header_node = (
            hx_table.tr[[hx_table.th(kind=col.kind)[col.header] for col in columns]]
            if header
            else None
        )
        body_rows = [self._render_row(row, columns) for row in rows]

        return self._list(
            "table",
            body_rows,
            backdrop=backdrop,
            header=header_node,
            header_vtn=header_vtn,
            cols_css=cols_css,
            **kwargs,
        )

    def table_row(
        self,
        cells: Sequence[FocusListCell],
        *,
        id: str,
        active: bool = False,
        **attrs,
    ) -> FocusListRow:
        """A body row; ``cells`` are built with ``table_cell``.

        Extra keyword args become attributes on the row's ``<tr>``. To make the
        whole row clickable with the data-table hover / selected affordance, pass
        ``aria_selected="false"`` (or ``"true"`` for the selected look) together
        with your htmx — e.g.::

            focus_list.table_row(
                cells, id=row_id, aria_selected="false",
                **htmx(hx_post=..., hx_target=..., hx_swap="outerHTML", as_dict=True),
            )
        """
        return FocusListRow(id=id, cells=cells, active=active, attrs=attrs)

    def table_cell(
        self,
        content: y.Node,
        *,
        colspan: int | Literal["all"] | None = None,
        kind: ColumnKind | None = None,
        **attrs,
    ) -> FocusListCell:
        """A body cell. ``colspan`` spans columns (an int, or ``"all"`` for the
        full width). The cell inherits its column's ``kind`` (alignment) by
        position; pass ``kind`` to override it — e.g. ``kind="layout"`` for a
        plain block cell (no flex, no padding) that hosts its own layout. Extra
        keyword args become ``<td>`` attributes (e.g. ``class_``)."""
        return FocusListCell(content=content, colspan=colspan, kind=kind, attrs=attrs)

    def backdrop(self, **kwargs) -> y.Node:
        """Transparent overlay shown while an item is focused.

        Covers the list above the dimmed/locked siblings (and below the active
        item, which stays interactive), so clicks on the rest of the list are
        intercepted here instead. Defines no behaviour of its own — pass the
        close interaction via ``kwargs`` (e.g. htmx ``hx_*`` attributes or an
        ``onclick``). Pass it to the list helper's ``backdrop=`` while an item
        is active.
        """
        return y.div(**classnames(self.backdrop_classname, **kwargs))


focus_list = _FocusList()
