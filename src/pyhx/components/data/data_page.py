from typing import Any, Generic

import htpy as y
from commons.string_operators import pluralize, to_snake_case, to_title_case
from fastapi import Request

from pyhx.core.page import PageResponse, PageResult
from pyhx.core.primitives import Path, SyncOrAsyncFn, SyncOrAsyncValue, resolve_value
from pyhx.core.request_context import RequestContext
from pyhx.core.webapp_routes import WebAppRoutes

from ..layouts import page_header
from ._model_type import ModelType
from .column import Column
from .data_section import CM, EM, TM, CanEdit, DataSection, ExtraOobFn, T
from .sources import (
    DataSource,
    HierarchicalDataSource,
    ReadOnlyDataSource,
    ReadOnlyHierarchicalDataSource,
)


class DataPage(Generic[T, TM, EM, CM]):
    def __init__(
        self,
        *,
        routes: WebAppRoutes,
        path: str,
        source: DataSource[T] | HierarchicalDataSource[T],
        type: type[T],
        name: str | None = None,
        page_title: SyncOrAsyncValue[str | None] = None,
        breadcrumbs: SyncOrAsyncValue[list[y.Node] | None] = None,
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
        on_page_render: SyncOrAsyncValue[Any] = None,
        table_columns: SyncOrAsyncValue[tuple[Column[TM], ...] | None] = None,
        table_columns_order: SyncOrAsyncValue[list[str] | None] = None,
        table_initially_expanded: bool = False,
        table_enable_sort_and_filter: bool = True,
        fragments_path: Path | None = None,
        hidden_params: dict[str, str] | None = None,
    ) -> None:
        """Register a full CRUD page for items of ``type``.

        A ``DataPage`` registers a page at ``path`` that renders a header
        (title, breadcrumbs, actions) above a :class:`DataSection` — the
        table plus its create/edit drawer. The section's HTMX fragment
        endpoints are registered separately under a *static*
        ``fragments_path`` so the page ``path`` itself may be
        parameterized.

        Type parameters: ``T`` is the domain model, ``TM`` the table-row
        model, ``EM`` the edit-form model and ``CM`` the create-form
        model. ``TM`` / ``EM`` / ``CM`` each default to ``T``.

        Parameters
        ----------
        routes : WebAppRoutes
            The app or router the page and its fragment endpoints are
            registered against.
        path : str
            The page's URL path. May be parameterized (e.g.
            ``"/projects/{id}/tasks"``); in that case supply
            ``hidden_params`` (or rely on the path-param default) so the
            static fragment endpoints still receive the parameters.
        source : DataSource[T] | HierarchicalDataSource[T]
            The read/write data source for domain items of ``type``.
            A hierarchical source yields a tree-shaped table.
        type : type[T]
            The domain model type handled by the page.
        name : str, optional
            Identifier used to derive route names, element ids and the
            derived ``fragments_path``. Defaults to the snake_case plural
            of the type name (e.g. ``Task`` -> ``tasks``).
        page_title : SyncOrAsyncValue[str | None], optional
            The page's ``<h1>`` and browser title, or a sync/async
            producer of it (resolved on each render, so it may depend on
            path params). Defaults to the title-case plural of the type
            name. Note: the static registration title used for nav/menus
            is the plain string when one is given here, otherwise the
            pluralized type name.
        breadcrumbs : SyncOrAsyncValue[list[y.Node] | None], optional
            Breadcrumb nodes rendered in the page header, or a sync/async
            producer of them (resolved on each render). ``None`` (the
            default) renders no breadcrumbs.
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
            applying ``table_model_type``.
        can_edit : :data:`CanEdit`, optional
            Whether items may be edited, and optionally what an edit click
            renders. ``False`` disables editing, ``True`` (the default) uses
            the built-in edit drawer, and a callable taking the clicked item
            renders the edit click itself — e.g.
            ``lambda item: FragmentResponse.redirect(f"/items/{item.id}")``.
            Forwarded verbatim to :class:`DataSection`, whose ``can_edit``
            documents the resolution rules and the required-positional-
            parameter constraint on the callable.
        can_create : SyncOrAsyncValue[bool], optional
            Whether new items may be created. Gates the create button.
            Defaults to ``True``.
        can_remove : SyncOrAsyncValue[bool], optional
            Whether items may be deleted. Gates the delete action.
            Defaults to ``True``.
        on_page_render : SyncOrAsyncValue[Any], optional
            A value (or sync/async producer) resolved on every page
            render, before the body is built — a hook for side effects or
            access checks. Its result is discarded. Defaults to ``None``.
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
        fragments_path : Path, optional
            Static base path under which the section's HTMX fragment
            endpoints are registered. When omitted it is ``Path(path)``
            for a static ``path``, or a derived
            ``/_fragments/data_pages/<name>`` when ``path`` is
            parameterized (so the fragments always have a variable-free
            path).
        hidden_params : dict[str, str], optional
            Name/value pairs rendered as hidden inputs that htmx includes
            in every request on the page (via ``data-hx-include``), so a
            parameterized page carries its parameters into the static
            fragment endpoints. When ``None`` (default), the current
            request's path parameters are used.
        """
        self._on_page_render = on_page_render
        self._hidden_params: dict[str, str] | None = hidden_params

        # The page `path` may be parameterized (e.g. "/projects/{id}/tasks"), but
        # DataSection derives static HTMX fragment endpoints from its `path`, so it
        # needs a path without parameters. When no explicit `fragments_path` is given
        # we derive a static one under "/_fragments/data_pages/{name}", resolving the
        # name the same way DataSection does so both agree.
        resolved_name = name or to_snake_case(
            pluralize(to_title_case(type_name or type.__name__))
        )

        try:
            fragments_path = fragments_path or Path(path)
        except ValueError:
            fragments_path = fragments_path or (
                Path("/_fragments/data_pages") / Path(f"/{resolved_name}")
            )

        self.section = DataSection(
            routes=routes,
            path=str(fragments_path),
            source=source,
            type=type,
            name=resolved_name,
            create_button_label=create_button_label,
            edit_dialog_title=edit_dialog_title,
            create_dialog_title=create_dialog_title,
            edit_submit_label=edit_submit_label,
            create_submit_label=create_submit_label,
            delete_item_label=delete_item_label,
            delete_confirmation_value=delete_confirmation_value,
            cancel_edit_label=cancel_edit_label,
            cancel_create_label=cancel_create_label,
            type_name=type_name,
            table_model_type=table_model_type,
            edit_form_model_type=edit_form_model_type,
            create_form_model_type=create_form_model_type,
            table_source=table_source,
            can_edit=can_edit,
            can_create=can_create,
            can_remove=can_remove,
            extra_oob=extra_oob,
            table_columns=table_columns,
            table_columns_order=table_columns_order,
            table_initially_expanded=table_initially_expanded,
            table_enable_sort_and_filter=table_enable_sort_and_filter,
            # A DataPage renders a full-page table, which always gets its own
            # scroll container (paired with the app-shell full-height layout).
            table_scrollable=True,
        )

        self._page_title = page_title
        self._breadcrumbs = breadcrumbs

        # `routes.page` needs a static title at registration time (used for
        # nav/menus). Use the string when one is given, otherwise fall back to
        # the pluralized type name; a dynamic title is resolved per render (see
        # `_render_page`) and overrides this via `PageResponse.page_title`.
        registration_title = (
            page_title
            if isinstance(page_title, str)
            else self.section.type_name_title_case_plural
        )
        self.page = routes.page(path, title=registration_title)(self._render_page)

    async def render_content(self) -> y.Node:
        # `section.render_table()` already wraps the table in a `container`;
        # return it directly rather than nesting a second identical container.
        return await self.section.render_table()

    async def render_page_header(self, page_title: str | None = None) -> y.Node:
        breadcrumbs = await resolve_value(self._breadcrumbs)
        return page_header(
            breadcrumbs=(
                page_header.breadcrumbs(*breadcrumbs) if breadcrumbs else None
            ),
            title=y.h1[page_title or await self._resolve_page_title()],
            actions=await self.section.render_actions(),
        )

    async def _resolve_page_title(self) -> str:
        resolved_title = await resolve_value(self._page_title)
        return resolved_title or self.section.type_name_title_case_plural

    async def _render_page(self) -> PageResult:
        await resolve_value(self._on_page_render)

        page_title = await self._resolve_page_title()
        body = y.fragment[
            await self.render_page_header(page_title),
            self._render_hidden_fields(),
            await self.render_content(),
        ]
        return PageResponse(node=body, page_title=page_title)

    def _render_hidden_fields(self) -> y.Node | None:
        """Hidden inputs carried into every HTMX request on the page.

        The page ``path`` may be parameterized (e.g. ``/projects/{id}/tasks``),
        but DataSection's fragment endpoints are static and never see those
        params. Wrapping the inputs in a ``data-hx-include="always"`` div makes
        htmx include them in every fragment request, so the params survive.

        - ``None`` (default): derive one hidden input per current path param.
        - ``dict``: one hidden input per key/value.

        Renders nothing when there is nothing to include.
        """
        if self._hidden_params is not None:
            params: dict[str, str] = self._hidden_params
        else:  # None: derive from the current request's path params
            (request,) = RequestContext.get_from_context(Request)
            params = {k: str(v) for k, v in request.path_params.items()}

        children: list[y.Node] = [
            y.input(type="hidden", name=name, value=value)
            for name, value in params.items()
        ]
        if not children:
            return None

        return y.div(data_hx_include="always")[children]
