"""Server-rendered data table with sort, filter, selection, and an htmx filter drawer."""

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal
from urllib.parse import urlencode

import htpy as y
from commons.string_operators import to_kebabcase, to_snake_case
from fastapi import Form, Request

from pyhx.core import RequestContext, WebAppRoutes
from pyhx.core.fragment import FragmentResponse
from pyhx.core.primitives import SyncOrAsyncValue, htmx, resolve_value

from ..primitives import segment_control, table
from ..view_model import Option
from ._table_helpers import (
    TOGGLE_FULLSCREEN_ACTION,
    TOGGLE_SELECT_ACTION,
    EmptyStateProvider,
    TableState,
    apply_select_toggle,
    cell_click_attrs,
    column_widths_to_css_cols,
    is_htmx_request,
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
from .quick_filter import (
    QuickFilters,
    TableSearch,
    active_quick_filter,
    apply_quick_filter,
)
from .sources.filter import Condition, TextChoiceEquals, TextChoiceIn
from .sources.filter_type import ChoiceFilter
from .sources.query import Query
from .sources.simple_data_source import SimpleDataSource
from .sources.source import ReadOnlyDataSource

QUICK_FILTER_ACTION = "quick_filter"
"""``action`` posted when the user chooses a quick filter pill."""

SEARCH_ACTION = "search"
"""``action`` posted by the search field while the user types."""

FlatSelectMode = Literal["none", "single", "multi"]
"""Selection modes available on the flat :class:`DataTable`.

A subset of the shared :data:`~pyhx.components.data._table_helpers.SelectMode`
— the leaf-restricted modes only make sense when the table has a tree
structure, so they're excluded at the type level here.
"""


class DataTable[T]:
    """Renderable data table bound to a :class:`ReadOnlyDataSource`.

    Generic over the row type ``T``. Each instance registers two htmx
    fragments at construction time (the table re-render and the column
    header click handler) plus an inner :class:`FilterDrawer` that
    contributes a third (the drawer's own render). Pages re-render
    server-side; the current :class:`TableState` (query + fullscreen +
    column widths + selection) round-trips through a single hidden form
    input next to the table.
    """

    def __init__(
        self,
        *,
        routes: WebAppRoutes,
        name: str,
        source: ReadOnlyDataSource[T] | list[T],
        type: type[T] | None = None,
        columns: SyncOrAsyncValue[tuple[Column[T], ...] | None] = None,
        columns_order: SyncOrAsyncValue[list[str] | None] = None,
        select_mode: FlatSelectMode = "none",
        on_select: Callable[[list[T]], Awaitable[y.Node | FragmentResponse | None]]
        | None = None,
        empty_state: EmptyStateProvider | None = None,
        enable_sort_and_filter: bool = True,
        scrollable: bool = False,
        update_query_fragment: Callable[[Query], Awaitable[y.Node]] | None = None,
        url_param_keys: list[str] | None = None,
        quick_filters: QuickFilters | None = None,
        search: TableSearch | None = None,
    ) -> None:
        """Bind a table to ``source`` and register its htmx fragments.

        Parameters
        ----------
        routes : WebAppRoutes
            The owning app's routing registry. The table adds three
            fragments under ``/_components/data-tables/<name>/…``.
        name : str
            Human-readable identifier. Kebab-cased and used as the prefix
            for every fragment URL and DOM id, so it must be unique
            within the app.
        columns : tuple[Column[T], ...]
            Explicit column descriptors — typically action columns. When
            ``type`` is also given, an explicit column whose ``key``
            matches a model field replaces the auto-derived one.
        source : ReadOnlyDataSource[T] | list[T]
            Where rows come from. A plain ``list`` is auto-wrapped in
            :class:`SimpleDataSource` (handy for fixtures and tests);
            anything else is used as-is.
        type : type[T] | None, default None
            Pydantic model whose annotated fields are auto-derived into
            columns (see :func:`read_column_annotations`). When ``None``,
            only ``columns`` is used.
        columns_order : list[str] | None, default None
            Authoritative whitelist and order, keyed by ``Column.key``.
            When set, any column whose key is absent is dropped entirely
            from the table — render, filter drawer, and sort. When
            ``None``, derived columns come first (in model field order)
            and explicit columns are appended (in call order).
        select_mode : FlatSelectMode, default "none"
            Row selection model. ``"single"`` allows at most one row;
            ``"multi"`` allows any subset. ``"none"`` disables selection
            entirely (no ``aria-selected`` and no click handler on rows).
        on_select : callable, optional
            Fires after every selection change driven by a row click.
            Receives the new selection as a ``list[T]`` — ids are
            resolved through :meth:`ReadOnlyDataSource.get_by_id` before the
            callback runs, so handlers get full items rather than bare
            ids. Returning a ``y.Node`` folds it into the response —
            that node **must carry ``hx-swap-oob``** to actually land in
            the DOM. Returning ``None`` means "side-effects only" (e.g.
            server-side store update with no UI consequence).
        empty_state : :data:`EmptyStateProvider` | None, default None
            Content rendered beneath the column header when the source
            returns no rows. Accepts either a static ``y.Node`` or a
            sync/async callable receiving the current :class:`Query` —
            useful for distinguishing "no items yet" from "no matches
            for the active filter". When ``None``, the table renders the
            default ``"No items to display"``. The content sits in a
            single full-width row spanning every column.
        enable_sort_and_filter : bool, default True
            When ``False``, the table renders without any sort or filter
            controls: column headers become plain text (no sort link or
            icons) and the toolbar drops its filter-drawer and clear
            buttons. The maximize button and column resizing are
            unaffected. Hides the controls only — an externally supplied
            ``query`` is still honoured.
        scrollable : bool, default False
            When ``True``, the ``<table>`` is wrapped in a
            ``hx-table__scroll-container`` (``overflow: auto``) so a table
            wider than its area scrolls horizontally within a bordered box
            instead of overflowing the page. The toolbar stays pinned to the
            wrapper (it doesn't scroll with the body) and the wrapper keeps
            its ``id``/``hx-swap-oob`` so re-renders still target it. Note the
            container re-anchors the sticky header to its own top, so the
            app-shell "header follows the page" sticky behaviour no longer
            applies while scrolling.
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
            Filter ``Condition`` keys mirrored into same-named URL query
            parameters, e.g. ``["status"]`` keeps ``?status=draft`` in sync
            with the table's ``status`` filter after every change of the
            query, and a page opened with ``?status=draft`` starts filtered.
            Only single values are representable: a ``TextChoiceEquals``, or a
            ``TextChoiceIn`` with one value (read back as ``TextChoiceIn`` for
            a multi-select choice column, as ``TextChoiceEquals`` otherwise);
            any other condition on a tracked key removes the parameter.
        quick_filters : QuickFilters | None, default None
            Presets shown as pills above the header (see
            :class:`~.quick_filter.QuickFilters`). Choosing one replaces the
            conditions on the preset columns; the active pill is derived from
            the query, so a drawer change on a preset column that matches no
            preset leaves none active. The active preset is kept in the URL
            (``?view=<key>``) and read back on a page load.
        search : TableSearch | None, default None
            Label, placeholder and URL parameter of the search field. The
            field is shown when at least one column is ``searchable`` and the
            source :attr:`~.sources.source.ReadOnlyDataSource.supports_search`;
            ``None`` uses the defaults of :class:`~.quick_filter.TableSearch`.
            The term is kept in the URL (``?q=<term>``).
        """
        if isinstance(source, list):
            source = SimpleDataSource(source)

        self.name = to_kebabcase(name)
        self.source = source
        self.select_mode: FlatSelectMode = select_mode
        self.on_select = on_select
        self.empty_state = empty_state
        self.enable_sort_and_filter = enable_sort_and_filter
        self.scrollable = scrollable
        self.update_query_fragment = update_query_fragment
        self.url_param_keys = url_param_keys or []
        self.quick_filters = quick_filters
        self.search = search or TableSearch()

        self.type = type
        self.columns = columns
        self.columns_order = columns_order

        self.wrapper_div_id = to_snake_case(f"{self.name}--wrapper")
        self.state_div_id = to_snake_case(f"{self.name}--hx-table--state")
        self.state_input_name = to_snake_case(f"{self.name}--hx-table--state")
        self.quick_filter_input_name = to_snake_case(f"{self.name}--quick-filter")
        self.search_input_name = to_snake_case(f"{self.name}--search")

        self.filter_drawer = FilterDrawer[T](
            routes,
            f"{self.name}--filter-drawer",
            self.state_input_name,
            self.render,
            type=type,
            columns=columns,
            columns_order=columns_order,
            hx_include=["[data-hx-include='always']"],
            # The table writes ``url_param_keys`` to the URL itself, on every
            # change of the query (see ``_url_params``), not only on Apply.
        )

        async def clear_sort_and_filter() -> y.Node:
            state = await self._read_state()
            state.query.clear()
            return await self._render_from_state(state)

        async def render_table(
            request: Request,
            action: Annotated[str, Form()] = "",
            item_id: Annotated[str, Form()] = "",
            column_widths: Annotated[str | None, Form()] = None,
        ) -> y.Node | FragmentResponse:
            state = await self._read_state()
            oob_nodes: list[y.Node] = []

            if column_widths:
                state.column_widths = column_widths
            if action == QUICK_FILTER_ACTION and self.quick_filters is not None:
                form = await request.form()
                key = str(form.get(self.quick_filter_input_name, ""))
                if (preset := self.quick_filters.find(key)) is not None:
                    state.query = apply_quick_filter(
                        state.query, preset, self.quick_filters
                    )
            elif action == SEARCH_ACTION:
                form = await request.form()
                term = str(form.get(self.search_input_name, "")).strip()
                state.query.search = term or None
                # Keep the field the user is typing in (value, focus, caret)
                # instead of swapping in the server's copy of it.
                return await self._render_from_state(state, preserve_search=True)
            elif action == TOGGLE_FULLSCREEN_ACTION:
                state.fullscreen = not state.fullscreen
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
        is_selected: list[str] | None = None,
    ) -> y.Node:
        """Public entry point — load state, overlay overrides, render.

        Reads any persisted :class:`TableState` from the current request
        (via the hidden state input), then overlays whichever of the
        keyword arguments are not ``None``. This is the seam used by the
        filter drawer's ``update_query_fragment`` callback: it passes
        only ``query`` and the rest of the state (selection, fullscreen,
        column widths) carries over from the request automatically.

        Parameters
        ----------
        query : Query | None, default None
            New sort + filter spec. ``None`` keeps the state's query
            (or a fresh ``Query()`` on first paint).
        fullscreen : bool | None, default None
            Override the fullscreen flag. ``None`` keeps the state's.
        column_widths : str | None, default None
            Override the CSS grid track string. ``None`` keeps the
            state's; the worker falls back to the column-derived layout
            if that's also unset.
        is_selected : list[str] | None, default None
            Override the selection list, keyed by
            ``source.get_id(item)``. ``None`` keeps the state's.

        Returns
        -------
        y.Node
            The wrapper ``<div>`` containing the hidden state input and
            the rendered ``<table>``.
        """
        state = await self._read_state()
        if query is not None:
            state.query = query
        if fullscreen is not None:
            state.fullscreen = fullscreen
        if column_widths is not None:
            state.column_widths = column_widths
        if is_selected is not None:
            state.is_selected = is_selected
        return await self._render_from_state(state)

    async def _read_state(self) -> TableState:
        """Read the persisted state from the current request, or a fresh one.

        Thin wrapper around :func:`read_state_from_request` that supplies
        a freshly-initialised ``TableState`` when nothing's available —
        page first-paint, ad-hoc render outside a request, etc.
        """
        state = await read_state_from_request(self.state_input_name, TableState)
        if state is not None:
            return state
        return TableState(query=await self._initial_query())

    async def query(self) -> Query:
        """The query the table renders for the current request.

        From the table state of a fragment request, or, on a page's first
        paint, from the URL (see ``url_param_keys``, ``quick_filters`` and
        ``search``). Use it for controls outside the table that reflect
        whether it is filtered.
        """
        return (await self._read_state()).query

    async def _initial_query(self) -> Query:
        """The query of a first paint: the URL's preset, conditions and search.

        Only the parameters this table is configured for are read; an
        unknown preset key is ignored.
        """
        query = Query()
        columns = await self._resolve_columns()
        search_enabled = self._search_enabled(columns)
        has_url_params = bool(
            self.url_param_keys
            or (search_enabled and self.search.url_param)
            or (self.quick_filters is not None and self.quick_filters.url_param)
        )
        if not has_url_params:
            return query
        try:
            request = RequestContext.get().request
        except LookupError:
            request = None
        if request is None:
            return query
        params = request.query_params

        if (
            self.quick_filters is not None
            and self.quick_filters.url_param is not None
            and (key := params.get(self.quick_filters.url_param)) is not None
            and (preset := self.quick_filters.find(key)) is not None
        ):
            query = apply_quick_filter(query, preset, self.quick_filters)

        if self.url_param_keys:
            columns_by_key = {c.key: c for c in columns}
            for key in self.url_param_keys:
                value = params.get(key)
                if not value:
                    continue
                column = columns_by_key.get(key)
                multiple = (
                    column is not None
                    and isinstance(column.filter_type, ChoiceFilter)
                    and column.filter_type.multiple
                )
                condition = Condition(
                    key=key,
                    values=[
                        TextChoiceIn(values=[value])
                        if multiple
                        else TextChoiceEquals(value=value)
                    ],
                )
                query.filter = [c for c in query.filter if c.key != key]
                query.filter.append(condition)

        if (
            search_enabled
            and self.search.url_param is not None
            and (term := params.get(self.search.url_param, "").strip())
        ):
            query.search = term
        return query

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

    def _search_enabled(self, columns: tuple[Column[T], ...]) -> bool:
        """Whether the search field is shown: a searchable column and a source that searches."""
        return self.source.supports_search and any(c.searchable for c in columns)

    async def _render_from_state(
        self, state: TableState, *, preserve_search: bool = False
    ) -> y.Node:
        """Render the table for ``state`` — the single source of truth.

        Used directly by the fragment handlers. Fills in
        ``state.column_widths`` from the column specs when missing and
        normalises ``state.is_selected`` against ``self.select_mode``
        before any markup is emitted. ``search_keys`` always come from the
        searchable columns, never from the round-tripped state.
        ``preserve_search`` marks the search field ``hx-preserve`` (for the
        response to a search request).
        """
        columns = await self._resolve_columns()
        visible_columns = tuple(c for c in columns if c.visible)

        search_enabled = self._search_enabled(columns)
        if search_enabled:
            state.query.search_keys = [c.key for c in columns if c.searchable]
        else:
            state.query.search_keys = []
            state.query.search = None

        if state.column_widths is None:
            state.column_widths = column_widths_to_css_cols(visible_columns)
        state.is_selected = normalize_selection(self.select_mode, state.is_selected)

        rows = await self.source.fetch(state.query)

        table_kwargs: dict[str, Any] = {
            "data_update_url": self.render_table_fragment.url(),
            "hx_include": "[data-hx-include='always']",
        }
        if self.select_mode != "none":
            table_kwargs["role"] = "grid"
        if is_multi_select(self.select_mode):
            table_kwargs["aria_multiselectable"] = "true"

        table_node = table(
            id=self.wrapper_div_id,
            column_widths=state.column_widths,
            fullscreen=state.fullscreen,
            scrollable=self.scrollable,
            controls=y.fragment[
                render_state_input(self.state_div_id, self.state_input_name, state),
                await self._render_filter_bar(
                    state.query,
                    search_enabled=search_enabled,
                    preserve_search=preserve_search,
                ),
                render_toolbar(
                    render_table_url=self.render_table_fragment.url(),
                    clear_sort_and_filter_url=self.clear_sort_and_filter_fragment.url(),
                    filter_drawer=self.filter_drawer,
                    state_div_id=self.state_div_id,
                    query=state.query,
                    enable_sort_and_filter=self.enable_sort_and_filter,
                ),
            ],
            table_kwargs=table_kwargs,
            is_tree=False,
            **htmx(hx_swap_oob="outerHTML", as_dict=True),
            **self._url_params(state.query, search_enabled=search_enabled),
        )[
            table.thead[
                table.tr[
                    [
                        render_header_cell(
                            column,
                            col_idx,
                            state.query,
                            table_header_click_url=self.table_header_click_fragment.url(),
                            wrapper_div_id=self.wrapper_div_id,
                            state_div_id=self.state_div_id,
                            enable_sort_and_filter=self.enable_sort_and_filter,
                        )
                        for col_idx, column in enumerate(visible_columns)
                    ],
                    table.th[""],
                ],
            ],
            table.tbody[
                (
                    render_empty_row(
                        await resolve_empty_state(self.empty_state, state.query)
                    )
                    if not rows.items
                    else [
                        await self._render_row(row, visible_columns, state.is_selected)
                        for row in rows.items
                    ]
                )
            ],
        ]

        if self.update_query_fragment is None or not is_htmx_request():
            return table_node

        return y.fragment[table_node, await self.update_query_fragment(state.query)]

    def _url_params(self, query: Query, *, search_enabled: bool) -> dict[str, str]:
        """The wrapper attributes ``pyhx.table.js`` mirrors into the address bar.

        ``data-hx-url-param-keys`` lists every parameter the table owns (a
        listed key without value is removed from the URL),
        ``data-hx-url-params`` holds the current values as a query string.
        Empty when the table owns no parameter.
        """
        keys: list[str] = []
        pairs: list[tuple[str, str]] = []

        if self.quick_filters is not None and self.quick_filters.url_param:
            keys.append(self.quick_filters.url_param)
            active = active_quick_filter(query, self.quick_filters)
            if active is not None and active.filter:
                pairs.append((self.quick_filters.url_param, active.key))

        for key in self.url_param_keys:
            keys.append(key)
            condition = next((c for c in query.filter if c.key == key), None)
            if condition is None or len(condition.values) != 1:
                continue
            value = condition.values[0]
            if isinstance(value, TextChoiceEquals):
                pairs.append((key, value.value))
            elif isinstance(value, TextChoiceIn) and len(value.values) == 1:
                pairs.append((key, value.values[0]))

        if search_enabled and self.search.url_param:
            keys.append(self.search.url_param)
            if query.search:
                pairs.append((self.search.url_param, query.search))

        if not keys:
            return {}
        return {
            "data-hx-url-param-keys": ",".join(keys),
            "data-hx-url-params": urlencode(pairs),
        }

    async def _render_filter_bar(
        self, query: Query, *, search_enabled: bool, preserve_search: bool
    ) -> y.Node:
        """The bar above the header: quick filter pills left, search right.

        ``None`` when the table has neither. The pills are the radio group
        of :func:`segment_control` (one checked, or none for "custom"); a
        change posts ``action=quick_filter`` with the checked radio. The
        search field posts ``action=search`` after a short pause.
        """
        if self.quick_filters is None and not search_enabled:
            return None

        pills: y.Node = None
        if self.quick_filters is not None:
            active = active_quick_filter(query, self.quick_filters)
            options = []
            for preset in self.quick_filters.presets:
                label = str(preset.label)
                if self.quick_filters.counts:
                    count = await self.source.count(
                        apply_quick_filter(query, preset, self.quick_filters)
                    )
                    if count is not None:
                        label = f"{label} {count}"
                options.append(Option(label=label, value=preset.key))
            pill_attrs: dict[str, Any] = htmx(
                hx_post=self.render_table_fragment.url(),
                hx_trigger="change",
                hx_swap="none",
                hx_include="[data-hx-include='always'], find input:checked",
                hx_vals={"action": QUICK_FILTER_ACTION},
                as_dict=True,
            )
            pills = segment_control(
                self.quick_filter_input_name,
                options,
                value=active.key if active is not None else None,
                size="sm",
                input_id_prefix=self.quick_filter_input_name,
                aria_label=str(self.quick_filters.label),
                class_="hx-table__quick-filters",
                **pill_attrs,
            )

        search_field: y.Node = None
        if search_enabled:
            search_field = y.label(class_="hx-table__search")[
                y.span[self.search.label],
                y.input(
                    type="search",
                    id=self.search_input_name,
                    name=self.search_input_name,
                    value=query.search or "",
                    placeholder=str(self.search.placeholder)
                    if self.search.placeholder is not None
                    else None,
                    autocomplete="off",
                    hx_preserve=preserve_search or None,
                    **htmx(
                        hx_post=self.render_table_fragment.url(),
                        hx_trigger="input changed delay:300ms, search",
                        hx_swap="none",
                        hx_sync="this:replace",
                        hx_include="[data-hx-include='always']",
                        hx_vals={"action": SEARCH_ACTION},
                        as_dict=True,
                    ),
                ),
            ]

        return y.div(class_="hx-table__filter-bar")[pills, search_field]

    async def _render_row(
        self,
        row: T,
        visible_columns: tuple[Column[T], ...],
        is_selected: list[str],
    ) -> y.Node:
        row_kwargs: dict[str, Any] = {}
        selected: bool | None = None
        if self.select_mode != "none":
            item_id = await self.source.get_id(row)
            selected = item_id in is_selected
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

        return table.tr(is_selected=selected, **row_kwargs)[
            [
                table.td(kind=column.kind, **cell_click_attrs(column))[
                    column.render(row)
                ]
                for column in visible_columns
            ],
            table.td[""],
        ]
