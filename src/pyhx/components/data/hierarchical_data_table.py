from collections.abc import Awaitable, Callable
from typing import Annotated, Any

import htpy as y
from commons.string_operators import to_kebabcase, to_snake_case
from fastapi import Form
from pydantic import Field

from pyhx.core import WebAppRoutes
from pyhx.core.fragment import FragmentResponse
from pyhx.core.primitives import SyncOrAsyncValue, htmx, resolve_value

from ..primitives import button, table
from ._table_helpers import (
    COLLAPSE_ALL_ACTION,
    EXPAND_ALL_ACTION,
    TOGGLE_FULLSCREEN_ACTION,
    TOGGLE_SELECT_ACTION,
    EmptyStateProvider,
    SelectMode,
    TableState,
    apply_select_toggle,
    cell_click_attrs,
    column_widths_to_css_cols,
    is_htmx_request,
    is_leafs_only_select,
    is_multi_select,
    normalize_selection,
    read_state_from_request,
    render_empty_row,
    render_header_cell,
    render_state_input,
    render_toolbar,
    resolve_empty_state,
)
from .column import Column
from .column_resolution import resolve_columns
from .filter_drawer import FilterDrawer
from .sources.query import Query
from .sources.source import (
    HierarchicalPage,
    Node,
    ReadOnlyHierarchicalDataSource,
)


class HierarchicalDataTableState(TableState):
    is_expanded: list[str] = Field(default_factory=list)
    is_initialized: bool = False
    """First-render sentinel for ``initially_expanded``.

    ``False`` means the table has never been rendered for this state yet,
    so :class:`HierarchicalDataTable` is free to seed ``is_expanded`` from
    its ``initially_expanded`` constructor flag. Flipped to ``True`` once
    seeded, which keeps a subsequent collapse-all sticky (otherwise an
    empty ``is_expanded`` would look indistinguishable from first paint).
    """


class HierarchicalDataTable[T]:
    def __init__(
        self,
        *,
        routes: WebAppRoutes,
        name: str,
        source: ReadOnlyHierarchicalDataSource[T],
        type: type[T] | None = None,
        columns: SyncOrAsyncValue[tuple[Column[T], ...] | None] = None,
        columns_order: SyncOrAsyncValue[list[str] | None] = None,
        select_mode: SelectMode = "none",
        on_select: Callable[[list[T]], Awaitable[y.Node | FragmentResponse | None]]
        | None = None,
        empty_state: EmptyStateProvider | None = None,
        initially_expanded: bool = False,
        enable_sort_and_filter: bool = True,
        scrollable: bool = False,
        update_query_fragment: Callable[[Query], Awaitable[y.Node]] | None = None,
        url_param_keys: list[str] | None = None,
    ) -> None:
        """Build a hierarchical (tree-grid) table component.

        All arguments are keyword-only; the signature mirrors
        :class:`DataTable` for symmetry.

        Parameters
        ----------
        routes : WebAppRoutes
            Where the component registers its fragment endpoints
            (header click, row toggle, clear sort/filter).
        name : str
            Per-instance identifier — must be unique on the page. Used to
            namespace the registered routes and the DOM ids.
        source : ReadOnlyHierarchicalDataSource[T]
            Backend the table reads from. ``source.fetch(query, parent=…)``
            is called once per visible level.
        type : type[T] | None, default None
            Pydantic model whose annotated fields are auto-derived into
            columns (see :func:`read_column_annotations`). When ``None``,
            only ``columns`` is used.
        columns : tuple[Column[T], ...] | None, default None
            Explicit column descriptors — typically action columns. When
            ``type`` is also given, an explicit column whose ``key``
            matches a model field replaces the auto-derived one. The
            first table column is the built-in expand affordance;
            ``columns`` describe the rest.
        columns_order : list[str] | None, default None
            Authoritative whitelist and order, keyed by ``Column.key``.
            When set, any column whose key is absent is dropped entirely
            from the table — render, filter drawer, and sort. When
            ``None``, derived columns come first (in model field order)
            and explicit columns are appended (in call order).
        select_mode : SelectMode, default "none"
            Row selection model. ``"single"`` / ``"multi"`` allow any row;
            ``"single-leafs"`` / ``"multi-leafs"`` restrict selection to
            leaf rows (those whose ``Node[T].has_children()`` is False).
        on_select : callable, optional
            Fires after every selection change driven by a row click.
            Receives the new selection as a ``list[T]`` — ids are resolved
            through :meth:`ReadOnlyHierarchicalDataSource.get_by_id` before the
            callback runs, so handlers get full items rather than bare
            ids. Returning a ``y.Node`` folds it into the response — that
            node **must carry ``hx-swap-oob``** to actually land in the
            DOM. Returning a :class:`FragmentResponse` replaces the whole
            response, which is how a row click can redirect the browser
            (see :meth:`FragmentResponse.redirect`). Returning ``None``
            means "side-effects only" (e.g. server-side store update with
            no UI consequence).
        empty_state : :data:`EmptyStateProvider` | None, default None
            Content rendered beneath the column header when the source's
            top-level fetch returns no rows. Accepts either a static
            ``y.Node`` or a sync/async callable receiving the current
            :class:`Query` — useful for distinguishing "no items yet"
            from "no matches for the active filter". When ``None``, the
            table renders the default ``"No items to display"``. Only
            checked at the root: empty sub-trees stay empty, they don't
            render a placeholder row.
        initially_expanded : bool, default False
            When ``True``, the first render seeds ``is_expanded`` with
            every expandable node id discovered by walking the source —
            i.e. the table opens fully expanded. A subsequent collapse
            sticks: the seeding only fires once per state, gated by
            ``HierarchicalDataTableState.is_initialized``.
        enable_sort_and_filter : bool, default True
            When ``False``, the table renders without any sort or filter
            controls: column headers become plain text (no sort link or
            icons) and the toolbar drops its filter-drawer and clear
            buttons. The maximize and expand/collapse buttons and column
            resizing are unaffected. Hides the controls only — an
            externally supplied ``query`` is still honoured.
        scrollable : bool, default False
            Wrap the ``<table>`` in a ``hx-table__scroll-container`` so a
            table wider or taller than its area scrolls within a bordered box
            instead of overflowing. Mirrors :class:`DataTable`'s ``scrollable``.
        update_query_fragment : callable, optional
            Fires with the current :class:`Query` every time
            :meth:`_render_from_state` renders, i.e. on every request
            that can change sort/filter (drawer apply/clear, the
            toolbar's own clear icon, a column-header sort click), not
            just one of them. The returned node is folded into the
            response alongside the table, so it should carry its own
            stable ``id`` and ``hx-swap-oob`` if it's meant to update an
            element living outside the table (e.g. a page-header button
            that mirrors whether a filter/sort is active).
        url_param_keys : list[str] | None, default None
            Forwarded to the table's internal :class:`FilterDrawer`(see its own ``url_param_keys`` for what it does). ``None``
            (the default) leaves the drawer's Apply/Clear behaviour exactly as it was before this option existed.
        """
        self.name = to_kebabcase(name)
        self.type = type
        self.columns = columns
        self.columns_order = columns_order
        self.source = source
        self.select_mode: SelectMode = select_mode
        self.on_select = on_select
        self.empty_state = empty_state
        self.initially_expanded = initially_expanded
        self.enable_sort_and_filter = enable_sort_and_filter
        self.scrollable = scrollable
        self.update_query_fragment = update_query_fragment

        self.wrapper_div_id = to_snake_case(f"{self.name}--wrapper")
        self.state_div_id = to_snake_case(f"{self.name}--hx-htable--state")
        self.state_input_name = to_snake_case(f"{self.name}--hx-htable--state")

        self.filter_drawer = FilterDrawer[T](
            routes,
            f"{self.name}--filter-drawer",
            self.state_input_name,
            self.render,
            type=type,
            columns=columns,
            columns_order=columns_order,
            url_param_keys=url_param_keys,
        )

        async def clear_sort_and_filter() -> y.Node:
            state = await self._read_state()
            state.query.clear()
            return await self._render_from_state(state)

        async def render_table(
            action: Annotated[str, Form()] = "",
            item_id: Annotated[str, Form()] = "",
            column_widths: Annotated[str | None, Form()] = None,
        ) -> y.Node | FragmentResponse:
            state = await self._read_state()
            oob_nodes: list[y.Node] = []

            if column_widths:
                state.column_widths = column_widths

            if action == TOGGLE_FULLSCREEN_ACTION:
                state.fullscreen = not state.fullscreen
            elif action == "toggle" and item_id:
                if item_id in state.is_expanded:
                    state.is_expanded.remove(item_id)
                else:
                    state.is_expanded.append(item_id)
            elif action == EXPAND_ALL_ACTION:
                state.is_expanded = await self._gather_expandable_ids(state.query)
            elif action == COLLAPSE_ALL_ACTION:
                state.is_expanded = []
            elif action == TOGGLE_SELECT_ACTION and item_id:
                state.is_selected = apply_select_toggle(
                    self.select_mode, state.is_selected, item_id
                )
                if self.on_select:
                    selected_items = [
                        await self.source.get_by_id(id) for id in state.is_selected
                    ]
                    result = await self.on_select(selected_items)
                    if isinstance(result, FragmentResponse):
                        return result
                    elif result is not None:
                        oob_nodes.append(result)

            return y.fragment[
                await self._render_from_state(state),
                *oob_nodes,
            ]

        async def table_header_click(
            column_key: Annotated[str, Form()],
        ) -> y.Node:
            state = await self._read_state()
            state.query.toggle_sort(column_key)
            return await self._render_from_state(state)

        self.clear_sort_and_filter_fragment = routes.fragment.add(
            f"/_components/data-tables/{self.name}/clear-sort-and-filter",
            "POST",
            clear_sort_and_filter,
        )

        self.render_table_fragment = routes.fragment.add(
            f"/_components/data-tables/{self.name}/render-table", "POST", render_table
        )

        self.table_header_click_fragment = routes.fragment.add(
            f"/_components/data-tables/{self.name}/table-header-click",
            "POST",
            table_header_click,
        )

    async def render(
        self,
        query: Query | None = None,
        fullscreen: bool | None = None,
        column_widths: str | None = None,
        is_expanded: list[str] | None = None,
        is_selected: list[str] | None = None,
    ) -> y.Node:
        """Public entry point — load state, overlay overrides, render.

        Reads any persisted :class:`HierarchicalDataTableState` from the
        current request (via the hidden state input), then overlays
        whichever of the keyword arguments are not ``None``. This is the
        seam used by the filter drawer's ``update_query_fragment``
        callback: it passes only ``query`` and the rest of the state
        (expansion, selection, fullscreen, column widths) carries over
        from the request automatically.
        """
        state = await self._read_state()
        if query is not None:
            state.query = query
        if fullscreen is not None:
            state.fullscreen = fullscreen
        if column_widths is not None:
            state.column_widths = column_widths
        if is_expanded is not None:
            state.is_expanded = is_expanded
        if is_selected is not None:
            state.is_selected = is_selected
        return await self._render_from_state(state)

    def _render_expand_collapse_buttons(self) -> list[y.Node]:
        """Build the toolbar's expand-all and collapse-all buttons.

        Both post against the table's main re-render fragment with a
        dedicated ``action`` value — same pattern as the maximize button.
        """
        render_table_url = self.render_table_fragment.url()
        return [
            button(
                icon="chevrons-down",
                variant="ghost",
                title="Expand All",
                **htmx(
                    hx_post=render_table_url,
                    hx_swap="none",
                    hx_include="[data-hx-include='always']",
                    hx_vals={"action": EXPAND_ALL_ACTION},
                ),
            ),
            button(
                icon="chevrons-up",
                variant="ghost",
                title="Collapse All",
                **htmx(
                    hx_post=render_table_url,
                    hx_swap="none",
                    hx_include="[data-hx-include='always']",
                    hx_vals={"action": COLLAPSE_ALL_ACTION},
                ),
            ),
        ]

    async def _gather_expandable_ids(self, query: Query) -> list[str]:
        """Walk the source under ``query`` and return every expandable node id.

        Used by the expand-all action and ``initially_expanded`` seeding.
        Recursion follows ``Node.has_children()``, so leaves don't trigger
        an extra fetch. The walk honours the active query — filtered-out
        subtrees aren't expanded.
        """
        expandable: list[str] = []

        async def walk(parent: str | None) -> None:
            page = await self.source.fetch(query, parent=parent)
            for node in page.items:
                if not node.has_children():
                    continue
                item_id = await self.source.get_id(node.item)
                expandable.append(item_id)
                await walk(item_id)

        await walk(None)
        return expandable

    def _is_selectable(self, node: Node[T]) -> bool:
        """Whether this row should carry ``aria-selected`` + the toggle handler.

        Layers two rules on top of the shared mode predicates:

        - The tree-specific leaf rule: in ``"single-leafs"`` /
          ``"multi-leafs"``, only rows without children are selectable.
        - The per-node veto: ``Node.selectable=False`` excludes an
          individual row regardless of mode — useful for marking
          structural/category rows or items the user lacks permission
          to pick.
        """
        if self.select_mode == "none":
            return False
        if not node.selectable:
            return False
        if is_leafs_only_select(self.select_mode):
            return not node.has_children()
        return True

    async def _read_state(self) -> HierarchicalDataTableState:
        """Read the persisted state from the current request, or a fresh one.

        Thin wrapper around :func:`read_state_from_request` that supplies
        a freshly-initialised ``HierarchicalDataTableState`` when nothing's
        available — page first-paint, ad-hoc render outside a request, etc.
        """
        state = await read_state_from_request(
            self.state_input_name, HierarchicalDataTableState
        )
        return state if state is not None else HierarchicalDataTableState(query=Query())

    async def _resolve_columns(self) -> tuple[Column[T], ...]:
        """Resolve the table's column set for the current render.

        Awaits the (possibly async) ``columns`` and ``columns_order``
        providers and folds them together with ``type`` into the final,
        ordered tuple of :class:`Column` descriptors. Called once per
        :meth:`_render_from_state` so the column set stays fresh per
        request rather than being frozen at construction time.
        """
        resolved_columns = await resolve_value(self.columns)
        resolved_columns_order = await resolve_value(self.columns_order)

        return resolve_columns(
            explicit=resolved_columns,
            type=self.type,
            columns_order=resolved_columns_order,
        )

    async def _render_from_state(self, state: HierarchicalDataTableState) -> y.Node:
        """Render the table for ``state`` — the single source of truth.

        Used directly by the fragment handlers. Fills in
        ``state.column_widths`` from the column specs when missing and
        normalises ``state.is_selected`` against ``self.select_mode``
        before any markup is emitted.
        """
        columns = await self._resolve_columns()
        visible_columns = tuple(c for c in columns if c.visible)

        if state.column_widths is None:
            state.column_widths = column_widths_to_css_cols(visible_columns)
        state.is_selected = normalize_selection(self.select_mode, state.is_selected)

        if not state.is_initialized:
            if self.initially_expanded:
                state.is_expanded = await self._gather_expandable_ids(state.query)
            state.is_initialized = True

        top_page = await self.source.fetch(state.query, parent=None)

        table_kwargs: dict[str, Any] = {
            "data_update_url": self.render_table_fragment.url(),
            "hx_include": "[data-hx-include='always']",
        }
        if is_multi_select(self.select_mode):
            table_kwargs["aria_multiselectable"] = "true"

        table_node = table(
            id=self.wrapper_div_id,
            column_widths=state.column_widths,  # NO leading — is_tree prepends it
            fullscreen=state.fullscreen,
            is_tree=True,
            scrollable=self.scrollable,
            controls=y.fragment[
                render_state_input(self.state_div_id, self.state_input_name, state),
                render_toolbar(
                    render_table_url=self.render_table_fragment.url(),
                    clear_sort_and_filter_url=self.clear_sort_and_filter_fragment.url(),
                    filter_drawer=self.filter_drawer,
                    state_div_id=self.state_div_id,
                    query=state.query,
                    leading_buttons=self._render_expand_collapse_buttons(),
                    enable_sort_and_filter=self.enable_sort_and_filter,
                ),
            ],
            table_kwargs=table_kwargs,
            **htmx(hx_swap_oob="outerHTML", as_dict=True),
        )[
            table.thead[
                table.tr[
                    table.th[""],  # leading expand-column header
                    [
                        render_header_cell(
                            column,
                            col_idx,
                            state.query,
                            table_header_click_url=self.table_header_click_fragment.url(),
                            wrapper_div_id=self.wrapper_div_id,
                            state_div_id=self.state_div_id,
                            col_idx_offset=1,
                            enable_sort_and_filter=self.enable_sort_and_filter,
                        )
                        for col_idx, column in enumerate(visible_columns)
                    ],
                    table.th[""],  # trailing placeholder (resize UX)
                ],
            ],
            table.tbody[
                (
                    render_empty_row(
                        await resolve_empty_state(self.empty_state, state.query)
                    )
                    if not top_page.items
                    else await self._render_rows(
                        state.query,
                        state.is_expanded,
                        state.is_selected,
                        visible_columns,
                        page=top_page,
                    )
                )
            ],
        ]

        if self.update_query_fragment is None or not is_htmx_request():
            return table_node

        return y.fragment[table_node, await self.update_query_fragment(state.query)]

    async def _render_rows(
        self,
        query: Query,
        is_expanded: list[str],
        is_selected: list[str],
        visible_columns: tuple[Column[T], ...],
        *,
        page: HierarchicalPage[T],
        level: int = 1,
    ) -> list[y.Node]:
        """Render the rows of ``page`` (pre-fetched), recursing for expanded children.

        The caller fetches the page so that ``_render_from_state`` can
        check emptiness once at the root and render the empty-state row
        instead. Child levels are fetched lazily here, only when a
        parent is expanded.
        """

        async def render_row(idx: int, node: Node[T]) -> list[y.Node]:
            item_id = await self.source.get_id(node.item)
            item_expanded = item_id in is_expanded
            item_selected = item_id in is_selected
            row_kwargs: dict[str, Any] = {
                "role": "row",
                "aria_posinset": str(idx + 1),
                "aria_setsize": str(page.total),
            }
            child_rows: list[y.Node] = []
            expanded: bool | None = None
            selected: bool | None = None

            if node.has_children():
                expanded = item_expanded
                if item_expanded:
                    child_page = await self.source.fetch(query, parent=item_id)
                    child_rows = await self._render_rows(
                        query,
                        is_expanded,
                        is_selected,
                        visible_columns,
                        page=child_page,
                        level=level + 1,
                    )

            if self._is_selectable(node):
                selected = item_selected
                row_kwargs.update(
                    htmx(
                        hx_post=self.render_table_fragment.url(),
                        hx_target=f"#{self.wrapper_div_id}",
                        hx_swap="outerHTML",
                        hx_include="[data-hx-include='always']",
                        hx_vals={"action": TOGGLE_SELECT_ACTION, "item_id": item_id},
                        as_dict=True,
                    )
                )

            row = table.tr(
                level=level,
                is_expanded=expanded,
                is_selected=selected,
                **row_kwargs,
            )[
                table.td[
                    (
                        table.expand_and_collapse_button(
                            item_expanded,
                            **htmx(
                                hx_post=self.render_table_fragment.url(),
                                hx_target=f"#{self.wrapper_div_id}",
                                hx_swap="outerHTML",
                                hx_include="[data-hx-include='always']",
                                hx_vals={"action": "toggle", "item_id": item_id},
                                as_dict=True,
                            ),
                        )
                        if node.has_children()
                        else ""
                    )
                ],
                *[
                    table.td(kind=column.kind, **cell_click_attrs(column))[
                        column.render(node.item)
                    ]
                    for column in visible_columns
                ],
                table.td[""],
            ]
            return [row, *child_rows]

        rendered: list[y.Node] = []
        for idx, node in enumerate(page.items):
            rendered.extend(await render_row(idx, node))
        return rendered
