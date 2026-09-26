from collections.abc import Awaitable, Callable
from inspect import Parameter, signature
from typing import Annotated, Any, Generic, cast

import htpy as y
from commons.string_operators import (
    pluralize,
    to_kebabcase,
    to_snake_case,
    to_title_case,
)
from fastapi import Form
from fastapi import Query as QueryParam
from pydantic import BaseModel

# PEP 696 TypeVar defaults land in `typing` only in 3.13; import from
# typing_extensions so the library stays importable on 3.12.
from typing_extensions import TypeVar

from pyhx.core.fragment import FragmentResponse
from pyhx.core.primitives import (
    Path,
    SyncOrAsyncFn,
    SyncOrAsyncValue,
    htmx,
    resolve_async_fn,
    resolve_value,
    styles,
)
from pyhx.core.webapp_routes import WebAppRoutes

from ..layouts import (
    POPUP_DRAWER_CONTENT_ID,
    container,
    drawer_content,
    notification,
    open_drawer_htmx_attributes,
    page_section,
)
from ..primitives import button
from ._model_type import ModelType
from .column import Column
from .data_form_drawer import DataFormDrawer
from .data_table import DataTable
from .hierarchical_data_table import HierarchicalDataTable
from .sources import (
    DataSource,
    HierarchicalDataSource,
    MappedReadOnlyDataSource,
    MappedReadOnlyHierarchicalDataSource,
    Query,
    ReadOnlyDataSource,
    ReadOnlyHierarchicalDataSource,
)

T = TypeVar("T", bound=BaseModel)
M = TypeVar("M", bound=BaseModel)
TM = TypeVar("TM", bound=BaseModel, default=T)  # table model
EM = TypeVar("EM", bound=BaseModel, default=T)  # edit form model
CM = TypeVar("CM", bound=BaseModel, default=T)  # create form model


type ExtraOobFn = Callable[[], Awaitable[y.Node]]
"""Renders one more out-of-band fragment, appended to every successful
create/update/delete response, so a change there can refresh a sibling section
on the same page. The returned node must carry its own ``hx-swap-oob``."""


type CanEdit[I] = SyncOrAsyncValue[bool | SyncOrAsyncFn[I, FragmentResponse]]
"""Whether items are editable, and optionally what an edit click renders.

Resolves to ``False`` (not editable), ``True`` (editable, built-in edit
drawer), or a callable taking the clicked item that renders the edit
click itself. See :class:`DataSection`'s ``can_edit`` parameter.
"""


def _takes_an_item(fn: object) -> bool:
    """True when ``fn`` is a callable that wants an item passed to it.

    ``can_edit`` accepts both a 0-arg producer of a bool and a 1-arg
    renderer taking the clicked item, and :func:`resolve_value` calls any
    callable with no arguments — so the two have to be told apart *before*
    it gets a chance to. Arity is the only signal available: a callable
    with at least one required positional parameter is the renderer.

    The corollary is a constraint on callers: a renderer whose parameter
    carries a default has no *required* positional and reads as a producer.
    Documented on :class:`DataSection`'s ``can_edit`` parameter.
    """
    if not callable(fn):
        return False

    try:
        params = signature(fn).parameters.values()
    except (TypeError, ValueError):  # builtins and other unintrospectables
        return False

    return any(
        parameter.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
        and parameter.default is Parameter.empty
        for parameter in params
    )


async def identity[T](x: T) -> T:
    return x


class DataSection(Generic[T, TM, EM, CM]):
    def __init__(
        self,
        *,
        routes: WebAppRoutes,
        path: str,
        source: DataSource[T] | HierarchicalDataSource[T],
        type: type[T],
        name: str | None = None,
        create_button_label: str | None = None,
        edit_dialog_title: str | None = None,
        create_dialog_title: str | None = None,
        edit_submit_label: str | None = None,
        create_submit_label: str | None = None,
        delete_item_label: str | None = None,
        delete_confirmation_value: SyncOrAsyncFn[T, str] | None = None,
        cancel_edit_label: str | None = None,
        cancel_create_label: str | None = None,
        type_name: str | None = None,
        table_model_type: ModelType[T, TM] | None = None,
        edit_form_model_type: ModelType[T, EM] | None = None,
        create_form_model_type: ModelType[T, CM] | None = None,
        table_source: ReadOnlyDataSource[TM]
        | ReadOnlyHierarchicalDataSource[TM]
        | None = None,
        can_edit: CanEdit[T] = True,
        can_create: SyncOrAsyncValue[bool] = True,
        can_remove: SyncOrAsyncValue[bool] = True,
        extra_oob: ExtraOobFn | None = None,
        table_columns: SyncOrAsyncValue[tuple[Column[TM], ...] | None] = None,
        table_columns_order: SyncOrAsyncValue[list[str] | None] = None,
        table_initially_expanded: bool = False,
        table_enable_sort_and_filter: bool = True,
        table_scrollable: bool = False,
    ) -> None:
        """Assemble a CRUD section (table + create/edit forms + drawer).

        A ``DataSection`` wires a data ``source`` to a table and to
        create/edit forms, registering its own HTMX fragment endpoints
        under ``path``. It renders as a table plus the actions (e.g. a
        create button) that drive an edit/create drawer.

        Type parameters: ``T`` is the domain model, ``TM`` the table-row
        model, ``EM`` the edit-form model and ``CM`` the create-form
        model. ``TM`` / ``EM`` / ``CM`` each default to ``T``.

        Parameters
        ----------
        routes : WebAppRoutes
            The app or router the section registers its fragment
            endpoints against.
        path : str
            Static base path for the section's HTMX fragment endpoints
            (e.g. create and close-drawer). Must contain no path
            variables — it is combined with sub-paths via :class:`Path`,
            which rejects parameterized paths.
        source : DataSource[T] | HierarchicalDataSource[T]
            The read/write data source for domain items of ``type``.
            A hierarchical source yields a tree-shaped table.
        type : type[T]
            The domain model type handled by the section.
        name : str, optional
            Identifier used to derive route names and element ids (e.g.
            the table and form names). Defaults to the snake_case plural
            of the type name (e.g. ``Task`` -> ``tasks``).
        create_button_label : str, optional
            Label of the button that opens the create drawer. Defaults to
            ``"Create <TypeName>"``.
        edit_dialog_title : str, optional
            Title of the edit drawer. Defaults to ``"Edit <TypeName>"``.
        create_dialog_title : str, optional
            Title of the create drawer. Defaults to ``"Create <TypeName>"``.
        edit_submit_label : str, optional
            Submit-button label of the edit form. Defaults to
            ``"Save <TypeName>"``.
        create_submit_label : str, optional
            Submit-button label of the create form. Defaults to
            ``"Create <TypeName>"``.
        delete_item_label : str, optional
            Label of the delete action in the edit drawer. Defaults to
            ``"Delete <TypeName>"``.
        cancel_edit_label : str, optional
            Cancel-button label of the edit form. Defaults to ``"Cancel"``.
        cancel_create_label : str, optional
            Cancel-button label of the create form. Defaults to ``"Cancel"``.
        type_name : str, optional
            Human-readable name of the type used to build the default
            titles and labels above. Defaults to ``type.__name__``.
        table_model_type : ModelType[T, TM], optional
            Bi-directional mapping between the domain type ``T`` and the
            model ``TM`` shown in the table. Defaults to the identity
            mapping (the table shows ``T`` directly).
        edit_form_model_type : ModelType[T, EM], optional
            Bi-directional mapping between ``T`` and the edit-form model
            ``EM``. Defaults to the identity mapping.
        create_form_model_type : ModelType[T, CM], optional
            Bi-directional mapping between ``T`` and the create-form model
            ``CM``. Defaults to the identity mapping.
        table_source : ReadOnlyDataSource[TM] | ReadOnlyHierarchicalDataSource[TM], optional
            An explicit read-only source of already-mapped table rows.
            When omitted, the table source is derived from ``source`` by
            applying ``table_model_type`` (matching ``source``'s flat or
            hierarchical shape).
        can_edit : :data:`CanEdit`, optional
            Whether items may be edited, and optionally what an edit
            click renders. Defaults to ``True``.

            Resolves (via :func:`resolve_value`) to one of:

            - ``False`` — not editable. The edit drawer never opens and
              the edit form's own submit endpoint refuses to update.
            - ``True`` — editable, using the built-in edit drawer.
            - a callable taking the clicked item — editable, but the
              callable renders the response instead of the built-in
              drawer. Returning :meth:`FragmentResponse.redirect` sends
              the browser to another page; returning any other
              ``FragmentResponse`` replaces the response wholesale.

            The callable is only invoked to render an edit click. The
            server-side guard on the edit form's submit endpoint treats
            "a callable was supplied" as "editable" without calling it,
            so a renderer that queries or logs doesn't run on submit.

            The renderer **must take a required positional parameter** —
            that arity is the only thing separating it from a plain 0-arg
            producer of a bool. Given a default (``def render(item=None)``)
            it is taken for a producer, called with no item, and the
            ``FragmentResponse`` it returns is read as a truthy bool: the
            built-in drawer renders and the custom response is dropped.
        can_create : SyncOrAsyncValue[bool], optional
            Whether new items may be created. Gates the create button.
            Defaults to ``True``.
        can_remove : SyncOrAsyncValue[bool], optional
            Whether items may be deleted. Gates the delete action.
            Defaults to ``True``.
        extra_oob : ExtraOobFn, optional
            Extra out-of-band fragment appended to every successful
            create/update/delete response, for refreshing a sibling section.
        table_columns : SyncOrAsyncValue[tuple[Column[TM], ...] | None], optional
            The columns to render. ``None`` (default) lets the table
            derive columns from the ``TM`` model's fields.
        table_columns_order : SyncOrAsyncValue[list[str] | None], optional
            Explicit left-to-right order of column keys. ``None``
            (default) keeps the model's field order.
        table_initially_expanded : bool, optional
            Hierarchical tables only: expand every node on first render.
            Defaults to ``False``.
        table_enable_sort_and_filter : bool, optional
            Show the sort/filter toolbar and enable per-column sorting and
            filtering. Defaults to ``True``.
        table_scrollable : bool, optional
            Wrap the table in its own scroll container (see
            :class:`DataTable`'s ``scrollable``), so a table wider or taller
            than its area scrolls internally. Forwarded to whichever table
            type is built. Defaults to ``False``.
        """
        self.source = source

        #
        # Names and labels
        #
        self.type_name_title_case = to_title_case(type_name or type.__name__)
        self.type_name_title_case_plural = pluralize(self.type_name_title_case)
        self.type_name_title_case_short = self.type_name_title_case.split(" ")[-1]

        self.name = name or to_snake_case(self.type_name_title_case_plural)

        self.create_button_label = (
            create_button_label or f"Create {self.type_name_title_case_short}"
        )
        self.create_dialog_title = (
            create_dialog_title or f"Create {self.type_name_title_case}"
        )
        self.edit_dialog_title = (
            edit_dialog_title or f"Edit {self.type_name_title_case}"
        )

        self.create_submit_label = (
            create_submit_label or f"Create {self.type_name_title_case_short}"
        )
        self.edit_submit_label = (
            edit_submit_label or f"Save {self.type_name_title_case_short}"
        )
        self.delete_item_label = (
            delete_item_label or f"Delete {self.type_name_title_case_short}"
        )
        # When set, the delete-confirmation popup requires retyping this value
        # before the Delete button enables (Azure-style). ``None`` (default)
        # is a plain Confirm/Cancel prompt.
        self._delete_confirmation_value = (
            resolve_async_fn(delete_confirmation_value)
            if delete_confirmation_value is not None
            else None
        )
        self.cancel_edit_label = cancel_edit_label or "Cancel"
        self.cancel_create_label = cancel_create_label or "Cancel"

        self.can_edit: CanEdit[T] = can_edit
        self.can_create = can_create
        self.can_remove = can_remove
        self._extra_oob = extra_oob
        self.enable_sort_and_filter = table_enable_sort_and_filter
        self.filter_sort_button_id = to_kebabcase(f"{self.name}-filter-sort-button")
        self._delete_confirm_button_id = to_kebabcase(
            f"{self.name}-delete-confirm-button"
        )

        #
        # Data models for internal components
        #
        identity_model = ModelType[T, T](type, identity, identity)
        self.table_model_type = cast(
            ModelType[T, TM], table_model_type or identity_model
        )
        self.edit_form_model_type = cast(
            ModelType[T, EM], edit_form_model_type or identity_model
        )
        self.create_form_model_type = cast(
            ModelType[T, CM], create_form_model_type or identity_model
        )

        #
        # Table's data source
        #
        self.table_source: ReadOnlyDataSource[TM] | ReadOnlyHierarchicalDataSource[TM]

        if table_source is None and isinstance(self.source, DataSource):
            self.table_source = MappedReadOnlyDataSource[T, TM](
                self.source,
                self.table_model_type.map_to,
                self.table_model_type.map_from,
            )
        elif table_source is None and isinstance(self.source, HierarchicalDataSource):
            self.table_source = MappedReadOnlyHierarchicalDataSource[T, TM](
                self.source,
                self.table_model_type.map_to,
                self.table_model_type.map_from,
            )
        else:
            assert table_source is not None
            self.table_source = table_source

        #
        # Edit Form
        #
        self.edit_form = DataFormDrawer(
            routes=routes,
            name=f"{self.name}_edit_form",
            type=self.edit_form_model_type.type,
            handle_submit=self._on_edit_form_submit,
            submit_label=self.edit_submit_label,
            dialog_title=self.edit_dialog_title,
            cancel_label=self.cancel_edit_label,
        )

        self.create_form = DataFormDrawer(
            routes=routes,
            name=f"{self.name}_save_form",
            type=self.create_form_model_type.type,
            handle_submit=self._on_create_form_submit,
            submit_label=self.create_submit_label,
            dialog_title=self.create_dialog_title,
            cancel_label=self.cancel_create_label,
        )

        #
        # Table
        #
        self.table: DataTable | HierarchicalDataTable

        if isinstance(self.table_source, ReadOnlyDataSource):
            self.table = DataTable(
                routes=routes,
                name=f"{self.name}_table",
                source=self.table_source,
                type=self.table_model_type.type,
                select_mode="single",
                on_select=self._on_select,
                columns=table_columns,
                columns_order=table_columns_order,
                enable_sort_and_filter=self.enable_sort_and_filter,
                scrollable=table_scrollable,
                update_query_fragment=(
                    self._render_filter_sort_button
                    if self.enable_sort_and_filter
                    else None
                ),
            )
        elif isinstance(self.table_source, ReadOnlyHierarchicalDataSource):
            self.table = HierarchicalDataTable(
                routes=routes,
                name=f"{self.name}_table",
                source=self.table_source,
                type=self.table_model_type.type,
                select_mode="single-leafs",
                on_select=self._on_select,
                columns=table_columns,
                columns_order=table_columns_order,
                initially_expanded=table_initially_expanded,
                enable_sort_and_filter=self.enable_sort_and_filter,
                scrollable=table_scrollable,
                update_query_fragment=(
                    self._render_filter_sort_button
                    if self.enable_sort_and_filter
                    else None
                ),
            )
        else:
            raise TypeError(f"Unexpected type of table_source {self.table_source}")

        #
        # Routes
        #
        create_path = str(Path(path) / Path("/create"))
        delete_path = str(Path(path) / Path("/delete"))
        delete_close_path = str(Path(path) / Path("/delete/close"))
        delete_confirm_path = str(Path(path) / Path("/delete/confirm"))

        self.open_create_form = routes.fragment.get(create_path)(
            self._on_create_item_click
        )

        self.open_delete_confirm = routes.fragment.get(delete_path)(
            self._on_delete_open
        )

        self.close_delete_confirm = routes.fragment.get(delete_close_path)(
            self._on_delete_close
        )

        self.confirm_delete = routes.fragment.post(delete_confirm_path)(
            self._on_delete_confirm
        )

    async def _render_filter_sort_button(self, query: Query) -> y.Node:
        """The page-header "Filter & Sort" trigger, highlighted while ``query`` is active.

        Passed to the table as its ``update_query_fragment`` hook, so this re-renders every time the table's query changes triggered by actions like drawer apply/clear, the toolbar's own clear icon, a column-header sort click.
        ``hx-swap-oob`` is always set, even on this method's first call from :meth:`render_actions`: it's inert on a plain page load and only takes effect once this node shows up inside a fragment response.
        """
        return button(
            "Filter & Sort",
            appearance="primary" if query.is_active_filter_or_sort() else "neutral",
            id=self.filter_sort_button_id,
            **self.table.filter_drawer.open_drawer_htmx_attributes(
                kwargs={
                    "hx_include": "[data-hx-include='always']",
                    "hx_swap_oob": "outerHTML",
                }
            ),
        )

    async def render_actions(self) -> y.Node:
        """The page-header action buttons.

        Renders the "Filter & Sort" drawer trigger (only when
        ``enable_sort_and_filter`` is ``True``) followed by the create
        button (only when ``can_create``).

        The trigger's initial highlight always starts from an empty
        ``Query``. A page reloaded with an active filter/sort will show the trigger un-highlighted until the next interaction.
        """

        return y.fragment[
            await self._render_filter_sort_button(Query())
            if self.enable_sort_and_filter
            else None,
            button(
                self.create_button_label,
                appearance="primary",
                **htmx(hx_get=self.open_create_form.url(), hx_swap="none"),
            )
            if self.can_create
            else None,
        ]

    async def render_section(self, section_title: str | None) -> y.Node:
        section_title = section_title or self.type_name_title_case_plural

        return page_section(
            title=section_title,
            actions=await self.render_actions(),
        )[await self.render_table()]

    async def render_table(self) -> y.Node:
        return container(await self.table.render(), width="wide")

    async def _extra_oob_node(self) -> y.Node | None:
        """Resolve ``extra_oob``, or ``None`` when the consumer passed none."""
        return await self._extra_oob() if self._extra_oob is not None else None

    async def _on_create_form_submit(self, item: CM) -> y.Node:
        await self.source.create(await self.create_form_model_type.map_from(item))
        return y.fragment[
            drawer_content(),
            self.table.render(is_selected=[]),
            await self._extra_oob_node(),
        ]

    async def _on_create_item_click(self) -> y.Node:
        return await self.create_form.render_drawer()

    async def _on_edit_form_submit(self, item: EM) -> y.Node:
        # A renderer resolves to a truthy callable, so a custom edit UI
        # still permits the update without the renderer being invoked.
        if not await self._resolve_can_edit():
            return None

        await self.source.update(await self.edit_form_model_type.map_from(item))
        return y.fragment[
            drawer_content(),
            self.table.render(is_selected=[]),
            await self._extra_oob_node(),
        ]

    async def _on_delete_open(self, id: Annotated[str, QueryParam()]) -> y.Node:
        """Open the delete-confirmation popup, stacked over the still-open edit drawer."""
        item = await self.source.get_by_id(id)
        return await self._render_delete_confirm(item)

    async def _on_delete_close(self) -> y.Node:
        """Close the confirmation popup without deleting, leaving the edit drawer open."""
        return drawer_content(id=POPUP_DRAWER_CONTENT_ID)

    async def _on_delete_confirm(self, id: Annotated[str, Form()]) -> y.Node:
        can_remove = await resolve_value(self.can_remove)
        if not can_remove:
            return None

        try:
            await self.source.delete_by_id(id)
        except ValueError as error:
            return y.fragment[
                drawer_content(id=POPUP_DRAWER_CONTENT_ID),
                drawer_content(),
                self.table.render(is_selected=[]),
                notification(
                    str(error),
                    appearance="danger",
                    title=f"Cannot delete {self.type_name_title_case_short}",
                ),
            ]

        return y.fragment[
            drawer_content(id=POPUP_DRAWER_CONTENT_ID),
            drawer_content(),
            self.table.render(is_selected=[]),
            await self._extra_oob_node(),
        ]

    async def _render_delete_confirm(self, item: T) -> y.Node:
        return drawer_content(
            y.div(**styles("flex", "px-md", "items-stretch", "flex-col", "gap-md"))[
                y.div(**styles("flex", "gap-sm", "items-start"))[
                    y.i(data_feather="alert-triangle", **styles("text-danger")),
                    y.div(**styles("flex", "flex-col", "gap-none"))[
                        y.strong(**styles("text-lg"))[
                            f"Delete this {self.type_name_title_case_short.lower()}?"
                        ],
                        y.p(**styles("mb-none", "text-muted"))[
                            "This action cannot be undone."
                        ],
                    ],
                ],
                await self._render_typed_confirmation_input(item)
                if self._delete_confirmation_value is not None
                else None,
                y.hr(**styles("my-none")),
                y.div(**styles("flex", "justify-end", "gap-sm"))[
                    button(
                        self.cancel_edit_label,
                        **htmx(hx_get=self.close_delete_confirm.url(), hx_swap="none"),
                    ),
                    await self._render_delete_confirm_button(item),
                ],
            ],
            id=POPUP_DRAWER_CONTENT_ID,
            title=self.delete_item_label,
        )

    async def _render_typed_confirmation_input(self, item: T) -> y.Node:
        """The retype-to-confirm input.

        Matching against ``data_expected_value`` is done client-side
        (``pyhx.delete-confirm.js``).
        """
        assert self._delete_confirmation_value is not None
        expected = await self._delete_confirmation_value(item)

        return y.div(**styles("flex", "flex-col", "gap-sm"))[
            y.p(**styles("mb-none"))[y.strong[f'Type "{expected}" to confirm.']],
            y.input(
                name="typed_value",
                autocomplete="off",
                data_expected_value=expected,
                data_confirm_button=self._delete_confirm_button_id,
            ),
        ]

    async def _render_delete_confirm_button(self, item: T) -> y.Node:
        item_id = await self.source.get_id(item)
        return button(
            self.delete_item_label,
            appearance="danger",
            id=self._delete_confirm_button_id,
            disabled=self._delete_confirmation_value is not None,
            **htmx(
                hx_post=self.confirm_delete.url(),
                hx_vals={"id": item_id},
                hx_include="[data-hx-include='always']",
                hx_swap="none",
            ),
        )

    async def _resolve_can_edit(
        self,
    ) -> bool | Callable[[T], Awaitable[FragmentResponse]]:
        """Normalise ``can_edit`` into either a bool or an always-async renderer.

        Returns the renderer *uncalled* so permission checks can read it as
        a plain truthy value (see :meth:`_on_edit_form_submit`) while the
        edit-click path invokes it with the item.
        """
        can_edit = self.can_edit

        if _takes_an_item(can_edit):
            renderer = can_edit
        else:
            resolved = await resolve_value(cast(SyncOrAsyncValue[Any], can_edit))
            if not callable(resolved):
                return bool(resolved)
            renderer = resolved

        return resolve_async_fn(cast(SyncOrAsyncFn[T, FragmentResponse], renderer))

    async def _on_select(self, items: list[TM]) -> y.Node | FragmentResponse:
        table_item = await self.table_model_type.map_from(items[0])
        edit_model_item = await self.edit_form_model_type.map_to(table_item)
        can_remove = await resolve_value(self.can_remove)
        can_edit = await self._resolve_can_edit()

        if not can_edit:
            return None

        if callable(can_edit):
            return await can_edit(table_item)

        delete_button: y.Node | None = None
        if can_remove:
            item_id = await self.source.get_id(table_item)
            delete_button = button(
                self.delete_item_label,
                appearance="danger",
                **open_drawer_htmx_attributes(
                    url=self.open_delete_confirm.url(query={"id": item_id}),
                    id=POPUP_DRAWER_CONTENT_ID,
                ),
            )

        return self.edit_form.render_drawer(
            edit_model_item, delete_button=delete_button
        )
