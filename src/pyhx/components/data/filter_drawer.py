"""The sort/filter drawer paired with :class:`DataTable`.

Rendered as a Pico drawer (slide-in ``<aside>``) populated by an htmx
fragment. The drawer is its own component — every action the user takes
(adding a filter, picking an operator, applying, clearing) posts back to
the same fragment URL, which validates the form into a
:class:`FilterDrawerValue` and re-renders the drawer. "Apply" and "Clear"
additionally re-render the parent data table via the
``update_query_fragment`` callback supplied at construction time.
"""

import json
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Literal, overload
from urllib.parse import urlencode

import htpy as y
from commons.dict_operators import unflatten
from commons.string_operators import to_kebabcase
from fastapi import Request

from pyhx.core import WebAppRoutes
from pyhx.core.fragment import FragmentResponse, FragmentResult
from pyhx.core.primitives import (
    HtmxAttrs,
    SyncOrAsyncValue,
    classnames,
    htmx,
    resolve_value,
    styles,
)

from ..layouts.drawer import (
    DRAWER_CONTENT_ID,
    drawer_content,
    open_drawer_htmx_attributes,
)
from ..primitives import (
    button,
    checkbox_fieldset,
    drawer_radio,
    drawer_select,
    dropdown_checkbox,
    dropdown_radio,
    radio_fieldset,
    segment_control,
)
from ..view_model import Option, resolve_options
from .annotations.controls import (
    CheckboxFieldsetControl,
    DrawerRadioControl,
    DrawerSelectControl,
    RadioFieldsetControl,
    SegmentControl,
)
from .column import Column
from .column_resolution import resolve_columns
from .filter_drawer_value import FilterDrawerValue
from .sources.filter import (
    BoolIsEmpty,
    BoolIsFalse,
    BoolIsNotEmpty,
    BoolIsTrue,
    Condition,
    DateAfter,
    DateBefore,
    DateBetween,
    DateEquals,
    DateIsEmpty,
    DateIsNotEmpty,
    FilterValue,
    ListContainsAll,
    ListContainsNone,
    ListIntersects,
    ListIsEmpty,
    ListIsNotEmpty,
    NumericBetween,
    NumericEquals,
    NumericGreaterThan,
    NumericGreaterThanOrEqual,
    NumericIsEmpty,
    NumericIsNotEmpty,
    NumericLessThan,
    NumericLessThanOrEqual,
    StringContains,
    StringEndsWith,
    StringEquals,
    StringIsEmpty,
    StringIsNotEmpty,
    StringStartsWith,
    TextChoiceEquals,
    TextChoiceIn,
    TextChoiceIsEmpty,
    TextChoiceIsNotEmpty,
    TextChoiceNotIn,
)
from .sources.filter_options import get_options_for_type
from .sources.filter_type import (
    ChoiceFilter,
    ChoiceFilterOption,
    FilterType,
    ListChoiceFilter,
)
from .sources.query import FilterMode, Query
from .sources.sort import SortOrder


def _render_choice_value_control(
    control: Any,
    name: str,
    options: tuple[Option, ...],
    *,
    multiple: bool,
    value: str | Sequence[str] | None,
) -> y.Node:
    """Render the value widget for a choice / list filter condition.

    Dispatches on the developer-chosen ``control`` marker (or falls back to a
    dropdown when ``None``), exactly mirroring the forms control pattern in
    :meth:`DataForm._render_text_choice` / ``_render_multiselect_choice``. No
    ``form_field`` wrapper — the drawer lays out its own labels.
    """
    if multiple:
        if value is None:
            selected: list[str] = []
        elif isinstance(value, str):
            selected = [value]
        else:
            selected = list(value)
        if isinstance(control, CheckboxFieldsetControl):
            return checkbox_fieldset(
                "", name, options, value=selected, orientation=control.orientation
            )
        if isinstance(control, DrawerSelectControl):
            return drawer_select(
                name, options, value=list(selected), labels=control.labels
            )
        # DropdownControl or no control → multi-select dropdown.
        return dropdown_checkbox(name, options, value=list(selected))

    single = value if isinstance(value, str) else None
    if isinstance(control, SegmentControl):
        return segment_control(name, options, value=single)
    if isinstance(control, RadioFieldsetControl):
        return radio_fieldset(
            "", name, options, value=single, orientation=control.orientation
        )
    if isinstance(control, DrawerRadioControl):
        return drawer_radio(name, options, value=single, labels=control.labels)
    # DropdownControl or no control → single-select dropdown.
    return dropdown_radio(name, options, value=single)


class FilterDrawer[T]:
    """A sort/filter side-panel bound to a set of :class:`Column` descriptors.

    Owns a single htmx fragment route which renders the drawer's full
    content. Acts as the configuration UI for a parent :class:`DataTable`:
    when the user clicks "Apply", the drawer hands a clean :class:`Query`
    back through the ``update_query_fragment`` callback so the table can
    re-render with the new sort + filter.
    """

    def __init__(
        self,
        routes: WebAppRoutes,
        name: str,
        state_input_name: str,
        update_query_fragment: Callable[[Query], Awaitable[y.Node]],
        *,
        type: type[T] | None = None,
        columns: SyncOrAsyncValue[tuple[Column[T], ...] | None] = None,
        columns_order: SyncOrAsyncValue[list[str] | None] = None,
        drawer_id: str = DRAWER_CONTENT_ID,
        hx_include: list[str] | None = None,
        url_param_keys: list[str] | None = None,
    ) -> None:
        """Register the drawer's htmx fragment and bind it to ``columns``.

        Parameters
        ----------
        routes : WebAppRoutes
            The owning app's routing registry. One fragment is added at
            ``/_components/filter-drawer/<name>``.
        name : str
            Human-readable identifier. Kebab-cased and used as the
            fragment URL suffix — must be unique within the app.
        state_input_name : str
            The DOM ``name`` of the parent data table's hidden state
            input. The value is JSON with a top-level ``query`` field
            (see :class:`TableState`); the drawer reads it on first
            open to bootstrap from the persisted query.
        update_query_fragment : Callable[[Query], Awaitable[y.Node]]
            Callback invoked on "Apply" and "Clear". Receives a clean
            :class:`Query` (no drawer UI state) and is expected to
            re-render whatever displays the data — typically the parent
            data table.
        type : type[T] | None, default None
            Pydantic model whose annotated fields are auto-derived into
            columns (see :func:`read_column_annotations`). When ``None``,
            only ``columns`` is used.
        columns : tuple[Column[T], ...] | None, default None
            Explicit column descriptors — typically action columns or
            per-call overrides. When ``type`` is also given, an explicit
            column whose ``key`` matches a model field replaces the
            auto-derived one. The drawer drives sort + filter against the
            resolved set.
        columns_order : list[str] | None, default None
            Authoritative whitelist and order, keyed by ``Column.key``.
            When set, any column whose key is absent is dropped. When
            ``None``, derived columns come first (in model field order)
            and explicit columns are appended (in call order).
        drawer_id : str, default DRAWER_CONTENT_ID
            DOM id the drawer's ``<aside>`` swaps into. Defaults to the
            shared id used by the layout-level drawer component.
        hx_include : list[str] | None, default None
            Extra CSS selectors merged into the drawer's ``hx-include``
            so that external state rides along with every Apply / Clear
            request. ``None`` and ``[]`` collapse to the default
            ``"closest form"`` behaviour. Selectors are htmx-style CSS
            (e.g. ``"#search-box"``, ``"[data-tenant]"``); read the
            corresponding values back inside ``update_query_fragment``
            via ``RequestContext.get().request.form()``.
        url_param_keys : list[str] | None, default None
            Filter ``Condition`` keys whose current value should mirror
            into a same-named browser URL query param on Apply/Clear, e.g. ``["status"]`` keeps ``?status=draft`` in sync with the
            drawer's own ``status`` filter, including removing it from the URL on Clear. ``None`` (the default) disables this entirely
            Implemented via two response headers (``HX-Url-Param-Keys``, ``HX-Url-Params``) that a client-side listener (``pyhx.filter-drawer.js``) reads to update the
            address bar with ``history.replaceState``, no full page navigation, no history entry. Only single-valued (:class:`~.sources.filter.TextChoiceEquals`) conditions are
            representable; any other condition on a tracked key is treated the same as "not set" (the URL param is removed).
        """
        self.name = to_kebabcase(name)
        self.state_input_name = state_input_name
        self.drawer_id = drawer_id

        self.type = type
        self.columns = columns
        self.columns_order = columns_order

        self.update_query_fragment = update_query_fragment
        self.url_param_keys = url_param_keys
        self.hx_include = ", ".join(
            ["closest form", "[data-hx-include='always']", *(hx_include or [])]
        )

        self.render_drawer_fragment = routes.fragment.add(
            f"/_components/filter-drawer/{self.name}", "POST", self._handle_request
        )

    async def _handle_request(self, request: Request) -> FragmentResult:
        """The registered fragment-route handler.

        Wraps :meth:`_render_and_apply`. When ``url_param_keys`` is configured and this request just committed a new query (Apply or
        Clear), attaches ``HX-Url-Param-Keys``/``HX-Url-Params`` headers for the client-side listener to sync into the address bar. Every
        other action (mid-edit re-renders, or no ``url_param_keys`` at all) returns the plain node, unchanged from before.
        """
        node, committed_query = await self._render_and_apply(request)
        if self.url_param_keys is None or committed_query is None:
            return node
        return FragmentResponse(
            node=node,
            headers={
                "HX-Url-Param-Keys": ",".join(self.url_param_keys),
                "HX-Url-Params": self._build_url_params_value(committed_query),
            },
        )

    def _build_url_params_value(self, query: Query) -> str:
        """Serialize ``url_param_keys``'s current values as a query string.

        Only single-valued (:class:`TextChoiceEquals`) conditions are representable since its the shape a single-select drawer control produces.
        """
        assert self.url_param_keys is not None
        pairs = []
        for key in self.url_param_keys:
            condition = next((c for c in query.filter if c.key == key), None)
            if condition is None or not condition.values:
                continue
            value = condition.values[0]
            if isinstance(value, TextChoiceEquals):
                pairs.append((key, value.value))
        return urlencode(pairs)

    async def render(self, request: Request) -> y.Node:
        """Render the drawer for the current request (plain node).

        Thin public wrapper around :meth:`_render_and_apply`, discarding
        the committed-query half of its result. This is what :class:`~.data_table.DataTable`/:class:`~.hierarchical_data_table.HierarchicalDataTable`
        pass as their own ``update_query_fragment`` when they build their internal drawer.
        """
        node, _ = await self._render_and_apply(request)
        return node

    async def _render_and_apply(self, request: Request) -> tuple[y.Node, Query | None]:
        """Core drawer logic: validate the form, dispatch on ``action``, render.

        Dispatches on ``action`` (add/remove a filter or sort entry, apply, clear), and re-renders the drawer. The "external" origin
        path bootstraps from the data table's hidden ``query`` JSON the first time the user opens the drawer. "Apply" and "Clear"
        additionally trigger the ``update_query_fragment`` callback to re-render the parent table.

        Parameters
        ----------
        request : Request
            The incoming htmx POST. Form is read from this.

        Returns
        -------
        tuple[y.Node, Query | None]
            The rendered node (either the drawer alone for a mid-edit
            re-render, or a fragment containing both the drawer and the
            re-rendered table after apply/clear), paired with the
            just-committed :class:`Query` for apply/clear, or ``None``
            for every other action.
        """
        form = await request.form()
        _columns, columns_by_key, all_fields_options = await self._resolve_columns()

        # Group repeated names into lists. A multi-select checkbox group submits
        # one ``name=value`` pair per checked box under a shared name; the naive
        # ``dict(form)`` would collapse them to the last value. Keys seen once
        # stay scalar (hidden fields, single inputs); keys seen 2+ times become
        # a ``list[str]`` that ``unflatten`` writes as a list leaf.
        grouped: dict[str, str | list[str]] = {}
        for key, raw in form.multi_items():
            if not isinstance(raw, str):
                continue
            existing = grouped.get(key)
            if existing is None:
                grouped[key] = raw
            elif isinstance(existing, list):
                existing.append(raw)
            else:
                grouped[key] = [existing, raw]

        filter_drawer_value = FilterDrawerValue.model_validate(unflatten(grouped))

        resolved_filter_types = await self._resolve_filter_types(columns_by_key)

        if filter_drawer_value.origin == "external" and self.state_input_name in form:
            state = json.loads(str(form[self.state_input_name]))
            query = Query.model_validate(state.get("query", {}))
            filter_drawer_value = FilterDrawerValue(**query.model_dump())
        elif (
            filter_drawer_value.action == "add_sort_field"
            and filter_drawer_value.add_sort_field is not None
        ):
            filter_drawer_value.sort.append(
                SortOrder(key=filter_drawer_value.add_sort_field, order="asc")
            )
        if (
            filter_drawer_value.action == "add_filter_field"
            and (field := filter_drawer_value.add_filter_field) is not None
            and (filter_type := resolved_filter_types.get(field)) is not None
        ):
            filter_drawer_value.add_filter(field, filter_type)
        elif filter_drawer_value.action == "clear":
            filter_drawer_value.clear()
            query = filter_drawer_value.to_query()
            return (
                y.fragment[
                    drawer_content(),
                    await self.update_query_fragment(query),
                ],
                query,
            )
        elif filter_drawer_value.action == "apply":
            query = filter_drawer_value.to_query()
            return (
                y.fragment[
                    drawer_content(),
                    await self.update_query_fragment(query),
                ],
                query,
            )
        elif (
            filter_drawer_value.action is not None
            and filter_drawer_value.action.startswith("remove_sort_field")
        ):
            key = filter_drawer_value.action.split(" ", 1)[1]
            filter_drawer_value.remove_sort_key(key)
        elif (
            filter_drawer_value.action is not None
            and filter_drawer_value.action.startswith("remove_filter_field")
        ):
            key = filter_drawer_value.action.split(" ", 1)[1]
            filter_drawer_value.remove_filter_key(key)
        elif (
            filter_drawer_value.action is not None
            and filter_drawer_value.action.startswith("remove_filter_condition")
        ):
            _, key, cond_idx = filter_drawer_value.action.split(" ")
            filter_drawer_value.remove_filter_condition(key, int(cond_idx))
        elif (
            filter_drawer_value.action is not None
            and filter_drawer_value.action.startswith("add_filter_condition")
            and (key := filter_drawer_value.action.split(" ", 1)[1]) in columns_by_key
            and (filter_type := resolved_filter_types.get(key)) is not None
        ):
            filter_drawer_value.add_filter_condition(key, filter_type)

        return (
            drawer_content(
                y.form(
                    class_="hx-filter-drawer",
                    **htmx(
                        hx_post=self.render_drawer_fragment.url(),
                        hx_include=self.hx_include,
                        hx_swap="none",
                        as_dict=True,
                    ),
                )[
                    y.input(type="hidden", name="origin", value="drawer"),
                    segment_control(
                        "view",
                        [
                            Option(label="Sort", value="sort"),
                            Option(label="Filter", value="filter"),
                        ],
                        value=filter_drawer_value.view,
                    ),
                    self._render_sort(
                        filter_drawer_value.sort,
                        columns_by_key,
                        all_fields_options,
                    ),
                    self._render_filter(
                        filter_drawer_value.filter_mode,
                        filter_drawer_value.filter,
                        resolved_filter_types,
                        columns_by_key,
                        all_fields_options,
                    ),
                ],
                title="Sort & Filter",
            ),
            None,
        )

    async def _resolve_columns(
        self,
    ) -> tuple[tuple[Column[T], ...], dict[str, Column[T]], tuple[Option, ...]]:
        resolved_columns = await resolve_value(self.columns)
        resolved_columns_order = await resolve_value(self.columns_order)

        columns = resolve_columns(
            explicit=resolved_columns,
            type=self.type,
            columns_order=resolved_columns_order,
        )

        columns_by_key = {column.key: column for column in columns}

        all_fields_options = tuple(
            [Option(label=c.label, value=c.key) for c in columns]
        )

        return (columns, columns_by_key, all_fields_options)

    async def _resolve_filter_types(
        self, columns_by_key: dict[str, Column[T]]
    ) -> dict[str, FilterType]:
        """Materialize every column's filter type for the current render.

        For :class:`ChoiceFilter` instances carrying a lazy
        ``_choices_provider`` (set by the annotation reader when a
        :class:`TextChoiceFilter` was given a callable), this awaits the
        provider and returns a fresh :class:`ChoiceFilter` with the
        resolved choices. Static filter types pass through unchanged.

        The result is built once per :meth:`render` call and threaded
        through the sync ``_render_*`` helpers so they never touch a
        provider directly.
        """
        resolved: dict[str, FilterType] = {}
        for key, column in columns_by_key.items():
            ft = column.filter_type
            if ft is None:
                continue
            if (
                isinstance(ft, (ChoiceFilter, ListChoiceFilter))
                and ft._choices_provider is not None
            ):
                options = await resolve_options(ft._choices_provider)
                choices = [
                    ChoiceFilterOption(label=o.label, value=o.value) for o in options
                ]
                rebuilt: ChoiceFilter | ListChoiceFilter = (
                    ListChoiceFilter(choices=choices)
                    if isinstance(ft, ListChoiceFilter)
                    else ChoiceFilter(choices=choices, multiple=ft.multiple)
                )
                # Carry the developer-chosen control through to the value render.
                rebuilt._control = ft._control
                resolved[key] = rebuilt
            else:
                resolved[key] = ft
        return resolved

    @overload
    def open_drawer_htmx_attributes(
        self,
        id: str = DRAWER_CONTENT_ID,
        *,
        as_dict: Literal[True],
        kwargs: HtmxAttrs | None = None,
    ) -> dict[str, str]: ...

    @overload
    def open_drawer_htmx_attributes(
        self,
        id: str = DRAWER_CONTENT_ID,
        *,
        as_dict: Literal[False] = False,
        kwargs: HtmxAttrs | None = None,
    ) -> HtmxAttrs: ...

    def open_drawer_htmx_attributes(
        self,
        id: str = DRAWER_CONTENT_ID,
        *,
        as_dict: bool = False,
        kwargs: HtmxAttrs | None = None,
    ) -> HtmxAttrs | dict[str, str]:
        """Attributes that open this drawer when spread onto a trigger element.

        Wraps :func:`pyhx.components.layouts.drawer.open_drawer_htmx_attributes`
        with this drawer's render-fragment URL pre-bound. The result can
        be spread onto a button or link to make it open the drawer on
        click.

        Parameters
        ----------
        id : str, default DRAWER_CONTENT_ID
            DOM id of the drawer's ``<aside>`` — controls where the
            response swaps in. Almost always left as the default.
        as_dict : bool, default False
            ``True`` returns a plain ``dict[str, str]`` with hyphenated
            keys (e.g. ``"hx-post"``) — suitable for direct spread into
            an htpy element. ``False`` returns an :class:`HtmxAttrs`
            ``TypedDict`` with snake-case keys, preferred when forwarding
            into another helper that itself accepts htmx kwargs.
        kwargs : HtmxAttrs | None, default None
            Additional htmx attributes to merge in. Overrides any of the
            internal defaults (``hx_swap="none"``, ``hx_target=#id``)
            when keys overlap. Typical use: pass ``hx_include`` to ship
            the table's hidden ``query`` input with the open request.

        Returns
        -------
        HtmxAttrs | dict[str, str]
            Attribute mapping ready to spread onto the trigger element.
        """
        if as_dict:
            return open_drawer_htmx_attributes(
                self.render_drawer_fragment.url(),
                method="POST",
                as_dict=True,
                kwargs=kwargs,
            )

        return open_drawer_htmx_attributes(
            self.render_drawer_fragment.url(),
            method="POST",
            as_dict=False,
            kwargs=kwargs,
        )

    def _render_submit_buttons(self) -> y.Node:
        return y.div(**styles("flex", "flex-col", "gap-sm", "items-stretch"))[
            button(
                "Apply Filter & Sort",
                appearance="primary",
                name="action",
                value="apply",
            ),
            button("Clear Filter & Sort", name="action", value="clear"),
        ]

    def _render_filter(
        self,
        filter_mode: FilterMode,
        filter: list[Condition],
        resolved_filter_types: dict[str, FilterType],
        columns_by_key: dict[str, Column[T]],
        all_fields_options: tuple[Option, ...],
    ) -> y.Node:
        return y.div(
            **classnames("hx-filter-drawer__filter", **styles("ml-lg", "mr-lg"))
        )[
            y.p(**styles("font-bold", "mb-md", "mt-md"))["Filter Mode"],
            dropdown_radio(
                "filter_mode",
                (
                    Option(label="Match All Filters", value="all"),
                    Option(label="Match Any Filter", value="any"),
                ),
                filter_mode,
            ),
            y.hr,
            self._render_filter_conditions(
                filter, resolved_filter_types, columns_by_key
            ),
            dropdown_radio(
                "add_filter_field",
                tuple(
                    [
                        col
                        for col in all_fields_options
                        if col.value not in [s.key for s in filter]
                        and columns_by_key[col.value].filter_type is not None
                    ]
                ),
                placeholder="Add filter ...",
                **htmx(
                    hx_post=self.render_drawer_fragment.url(),
                    hx_include=self.hx_include,
                    hx_swap="none",
                    hx_vals={"action": "add_filter_field"},
                ),
            ),
            y.hr,
            self._render_submit_buttons(),
        ]

    def _render_filter_conditions(
        self,
        filters: list[Condition],
        resolved_filter_types: dict[str, FilterType],
        columns_by_key: dict[str, Column[T]],
    ) -> y.Node:
        return [
            [
                y.input(
                    type="hidden",
                    name=f"filter[{filter_idx}].key",
                    value=f.key,
                ),
                y.div(**styles("flex", "justify-between", "items-center", "mb-sm"))[
                    y.span(**styles("font-bold"))[columns_by_key[f.key].label],
                    button(
                        icon="trash",
                        size="sm",
                        variant="solid",
                        name="action",
                        value=f"remove_filter_field {f.key}",
                    ),
                ],
                [
                    self._render_filter_condition(
                        f.key,
                        con,
                        filter_idx,
                        cond_idx,
                        len(f.values),
                        resolved_filter_types,
                    )
                    for cond_idx, con in enumerate(f.values)
                ],
                y.hr,
            ]
            for filter_idx, f in enumerate(filters)
        ]

    def _render_filter_condition(
        self,
        key: str,
        cond: FilterValue,
        filter_idx: int,
        cond_idx: int,
        cond_count: int,
        resolved_filter_types: dict[str, FilterType],
    ) -> y.Node:
        name_prefix = f"filter[{filter_idx}].values[{cond_idx}]"

        def render_filter_dropdown() -> y.Node:
            filter_type = resolved_filter_types.get(key)
            assert filter_type is not None

            return dropdown_radio(
                f"{name_prefix}.kind",
                get_options_for_type(filter_type),
                value=cond.kind,
                **styles("mb-none"),
                **htmx(
                    hx_post=self.render_drawer_fragment.url(),
                    hx_include=self.hx_include,
                    hx_swap="none",
                    hx_vals={},
                ),
            )

        def render_filter_value_controls() -> y.Node:
            match cond:
                # --- String ---
                case (
                    StringEquals()
                    | StringContains()
                    | StringStartsWith()
                    | StringEndsWith()
                ):
                    return [
                        y.input(
                            type="text",
                            name=f"{name_prefix}.value",
                            value=cond.value,
                            **styles("mb-none"),
                        )
                    ]
                case StringIsEmpty() | StringIsNotEmpty():
                    return []

                # --- Numeric ---
                case (
                    NumericEquals()
                    | NumericGreaterThan()
                    | NumericGreaterThanOrEqual()
                    | NumericLessThan()
                    | NumericLessThanOrEqual()
                ):
                    return [
                        y.input(
                            type="number",
                            name=f"{name_prefix}.value",
                            value=str(cond.value),
                            **styles("mb-none"),
                        )
                    ]
                case NumericBetween():
                    return [
                        y.input(
                            type="number",
                            name=f"{name_prefix}.min",
                            value=str(cond.min),
                            **styles("mb-none"),
                        ),
                        y.input(
                            type="number",
                            name=f"{name_prefix}.max",
                            value=str(cond.max),
                            **styles("mb-none"),
                        ),
                    ]
                case NumericIsEmpty() | NumericIsNotEmpty():
                    return []

                # --- Date ---
                case DateEquals() | DateBefore() | DateAfter():
                    return [
                        y.input(
                            type="date",
                            name=f"{name_prefix}.value",
                            value=cond.value.isoformat(),
                            **styles("mb-none"),
                        )
                    ]
                case DateBetween():
                    return [
                        y.input(
                            type="date",
                            name=f"{name_prefix}.min",
                            value=cond.min.isoformat(),
                            **styles("mb-none"),
                        ),
                        y.input(
                            type="date",
                            name=f"{name_prefix}.max",
                            value=cond.max.isoformat(),
                            **styles("mb-none"),
                        ),
                    ]
                case DateIsEmpty() | DateIsNotEmpty():
                    return []

                # --- Boolean (no value control; the kind alone carries meaning) ---
                case BoolIsTrue() | BoolIsFalse() | BoolIsEmpty() | BoolIsNotEmpty():
                    return []

                # --- Text choice (single + multi) & list set-ops ---
                case (
                    TextChoiceEquals()
                    | TextChoiceIn()
                    | TextChoiceNotIn()
                    | ListIntersects()
                    | ListContainsAll()
                    | ListContainsNone()
                ):
                    filter_type = resolved_filter_types.get(key)
                    choices = (
                        filter_type.choices
                        if isinstance(filter_type, (ChoiceFilter, ListChoiceFilter))
                        else []
                    )
                    options = tuple(
                        Option(label=c.label, value=c.value) for c in choices
                    )
                    control = getattr(filter_type, "_control", None)
                    if isinstance(cond, TextChoiceEquals):
                        return [
                            _render_choice_value_control(
                                control,
                                f"{name_prefix}.value",
                                options,
                                multiple=False,
                                value=cond.value,
                            )
                        ]
                    return [
                        _render_choice_value_control(
                            control,
                            f"{name_prefix}.values",
                            options,
                            multiple=True,
                            value=cond.values,
                        )
                    ]
                case (
                    TextChoiceIsEmpty()
                    | TextChoiceIsNotEmpty()
                    | ListIsEmpty()
                    | ListIsNotEmpty()
                ):
                    return []

            return []

        return [
            y.div(**styles("py-md")) if cond_idx > 0 else None,
            y.div(
                **styles(
                    "grid",
                    "gap-sm",
                    "justify-between",
                    "items-center",
                    style="display: grid; grid-template-columns: 2em 1fr 2em",
                )
            )[
                y.div(**styles("text-center"))["or" if cond_idx > 0 else None],
                y.div(
                    **styles("flex", "flex-col", "gap-md", "items-stretch", "flex-1")
                )[
                    render_filter_dropdown(),
                    render_filter_value_controls(),
                    button(
                        "Add new rule ...",
                        variant="link",
                        name="action",
                        value=f"add_filter_condition {key}",
                    ),
                ],
                y.div(**styles("text-right"))[
                    (
                        button(
                            icon="trash",
                            size="sm",
                            name="action",
                            value=f"remove_filter_condition {key} {cond_idx}",
                        )
                        if cond_count > 1
                        else None
                    )
                ],
            ],
        ]

    def _render_sort(
        self,
        sort: list[SortOrder],
        columns_by_key: dict[str, Column[T]],
        all_fields_options: tuple[Option, ...],
    ) -> y.Node:
        return y.div(
            **classnames("hx-filter-drawer__sort", **styles("ml-lg", "mr-lg"))
        )[
            y.p(**styles("font-bold", "mb-md", "mt-md"))["Sort by:"],
            dropdown_radio(
                "add_sort_field",
                tuple(
                    [
                        col
                        for col in all_fields_options
                        if col.value not in [s.key for s in sort]
                        and columns_by_key[col.value].sortable
                    ]
                ),
                **htmx(
                    hx_post=self.render_drawer_fragment.url(),
                    hx_include=self.hx_include,
                    hx_swap="none",
                    hx_vals={"action": "add_sort_field"},
                ),
            ),
            y.hr,
            self._render_sort_items(sort, columns_by_key),
            y.hr if sort else None,
            self._render_submit_buttons(),
        ]

    def _render_sort_items(
        self,
        sort: list[SortOrder],
        columns_by_key: dict[str, Column[T]],
    ) -> y.Node:
        return [
            [
                y.div(**styles("font-medium", "text-center", "mb-sm"))[
                    columns_by_key[s.key].label
                ],
                y.input(type="hidden", name=f"sort[{i}].key", value=s.key),
                y.div(
                    **styles(
                        "flex", "gap-sm", "justify-between", "align-middle", "mb-md"
                    )
                )[
                    dropdown_radio(
                        f"sort[{i}].order",
                        (
                            Option(label="Ascending", value="asc"),
                            Option(label="Descending", value="desc"),
                        ),
                        s.order,
                        **styles("mb-none"),
                    ),
                    button(
                        icon="trash",
                        size="sm",
                        variant="solid",
                        **styles("p-md"),
                        name="action",
                        value=f"remove_sort_field {s.key}",
                    ),
                ],
            ]
            for i, s in enumerate(sort)
        ]
