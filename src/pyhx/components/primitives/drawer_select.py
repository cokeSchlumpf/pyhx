"""Drawer-based option picker.

``drawer_select`` renders an on-page control listing the currently selected
options. A "Select items" button opens a drawer where the user filters the
available options, stages additions/removals, and confirms. All interaction is
driven by htmx fragments; component state round-trips as JSON in hidden inputs
(see :class:`DrawerSelectConfig` / :class:`DrawerSelectDrawerConfig`).
"""

from collections.abc import Sequence
from typing import Annotated
from uuid import uuid4

import htpy as y
from commons.string_operators import to_kebabcase
from fastapi import Form, Query, Request
from pydantic import BaseModel, Field

import pyhx.components as c
from pyhx.core import component
from pyhx.core.primitives import htmx, styles

from ..view_model import Option

CONFIG_JSON_FIELD = "drawer_select_config_json"
DRAWER_CONFIG_JSON_FIELD = "drawer_select_drawer_content_config_json"
DRAWER_AVAILABLE_ITEMS_CLASSNAME = "hx-drawer-select__available-items"
DRAWER_CONTENT_CLASSNAME = "hx-drawer-select__drawer-content"
DRAWER_TO_BE_ADDED_ITEMS_CLASSNAME = "hx-drawer-select__to-be-added"


class DrawerSelectLabels(BaseModel):
    """User-facing text for every part of a ``drawer_select``.

    A single instance is configured on the public ``drawer_select(...)`` call
    and stored on the config objects, so the labels survive every htmx
    round-trip (drawer open, search, add/remove, submit) and are available to
    all render functions without being threaded through each endpoint.
    """

    # --- Main control (on-page) ---
    value_column: str = "Value"
    select_items_button: str = "Select items"

    # --- Drawer ---
    drawer_title: str = "Select items"
    query_label: str = "Filter items"
    available_items_column: str = "Available items"
    selected_items_column: str = "Selected items"
    cancel_button: str = "Cancel"
    select_button: str = "Select"

    # --- Shared ---
    remove_item: str = "Remove"
    no_items_available: str = "No available items."
    no_items_selected: str = "No items selected."


class DrawerSelectConfig(BaseModel):
    """State of the on-page control, serialized into its hidden input.

    ``name`` is the form field name the selected values submit under; ``value``
    holds the currently selected option values.
    """

    options: tuple[Option, ...]
    value: list[str]
    name: str
    labels: DrawerSelectLabels = Field(default_factory=DrawerSelectLabels)

    def get_available_options(self) -> tuple[Option, ...]:
        """Options not in the current selection."""
        return tuple([o for o in self.options if o.value not in self.value])

    def get_selected_options(self) -> tuple[Option, ...]:
        """Currently selected options, in canonical option order."""
        return tuple([o for o in self.options if o.value in self.value])


class DrawerSelectDrawerConfig(BaseModel):
    """State of the open drawer, serialized into the drawer's hidden input.

    ``query`` is the current filter text; ``value`` holds the staged selection
    being edited in the drawer. ``nested_state`` carries the originating
    :class:`DrawerSelectConfig` (as JSON) so the control can be rebuilt on
    submit without a second request.
    """

    options: tuple[Option, ...]
    value: list[str]
    query: str
    nested_state: str = ""
    labels: DrawerSelectLabels = Field(default_factory=DrawerSelectLabels)

    def get_available_options(self) -> tuple[Option, ...]:
        """Unselected options whose label matches the current ``query`` filter."""
        return tuple(
            [
                o
                for o in self.options
                if self.query.lower() in o.label.lower() and o.value not in self.value
            ]
        )

    def get_selected_options(self) -> tuple[Option, ...]:
        """Currently selected options, in canonical option order."""
        return tuple([o for o in self.options if o.value in self.value])


def _values_in_option_order(values: list[str], options: Sequence[Option]) -> list[str]:
    """Order and de-duplicate selected ``values`` to match ``options``.

    Selection state is stored as a flat list of option values. Normalising it
    to the canonical option order keeps the serialized state deterministic
    (``set`` iteration order is not) and the submitted form values predictable,
    regardless of the order in which the user clicked items.
    """
    selected = set(values)
    return [option.value for option in options if option.value in selected]


@component
def drawer_select_endpoints() -> y.Node:
    """Mount point for the drawer-select htmx fragment routes.

    Renders nothing visible; including this component in an app registers the
    fragment endpoints defined below so the drawer's interactions resolve.
    """
    return y.fragment[""]


class _DrawerContent:
    """Renders the drawer body and the out-of-band fragments that keep it in
    sync as the user filters and stages a selection.

    Exposed as ``drawer_select.drawer_content``; the fragment endpoints call its
    methods to re-render parts of the open drawer.
    """

    def __call__(
        self,
        on_submit: str,
        options: Sequence[Option],
        value: list[str] | None = None,
        query: str = "",
        nested_state: str = "",
        labels: DrawerSelectLabels | None = None,
    ) -> y.Node:
        """Render the drawer body for the open picker.

        Parameters
        ----------
        on_submit:
            URL the Select button posts the staged selection to.
        options:
            Options offered in the available list (typically the
            not-yet-selected pool).
        value:
            Option values already staged for selection.
        query:
            Initial filter text for the search box.
        nested_state:
            Originating :class:`DrawerSelectConfig` as JSON, echoed back so the
            control can be rebuilt on submit.
        labels:
            Overrides for user-facing text. Defaults to
            :class:`DrawerSelectLabels`.
        """
        config = DrawerSelectDrawerConfig(
            options=tuple(options),
            value=value or [],
            query=query,
            nested_state=nested_state,
            labels=labels or DrawerSelectLabels(),
        )

        return c.drawer_content(
            y.div(class_=DRAWER_CONTENT_CLASSNAME)[
                y.div(
                    class_="hx-drawer-select__search",
                    hx_post=query_items.url(),
                    hx_trigger=("input delay:200ms"),
                    hx_target=f".{DRAWER_AVAILABLE_ITEMS_CLASSNAME}",
                    hx_swap="none",
                    hx_include="this",
                    as_dict=True,
                )[
                    self.config_input(config),
                    c.form_field("query", config.labels.query_label, y.input()),
                ],
                self.available_items(config.get_available_options(), config.labels),
                self.to_be_added_items(config.get_selected_options(), config.labels),
                y.div(class_="hx-drawer-select__actions")[
                    c.button(
                        config.labels.cancel_button,
                        **htmx(hx_get=close_drawer.url(), hx_swap="none"),
                    ),
                    c.button(
                        config.labels.select_button,
                        appearance="primary",
                        **htmx(
                            hx_post=on_submit,
                            hx_swap="none",
                            hx_include=f".{DRAWER_CONTENT_CLASSNAME}",
                        ),
                    ),
                ],
            ],
            id=c.POPUP_DRAWER_CONTENT_ID,
            title=config.labels.drawer_title,
        )

    def available_items(
        self,
        options: Sequence[Option],
        labels: DrawerSelectLabels,
        oob: bool = False,
    ) -> y.Node:
        """Render the filterable list of selectable options.

        Each row posts itself onto the staged selection on click. ``oob=True``
        marks the fragment for an htmx out-of-band swap during re-renders.
        """
        return y.div(
            id=DRAWER_AVAILABLE_ITEMS_CLASSNAME,
            class_=DRAWER_AVAILABLE_ITEMS_CLASSNAME,
            **(htmx(hx_swap_oob="outerHTML", as_dict=True) if oob else {}),
        )[
            y.table[
                y.thead[y.tr[y.th[labels.available_items_column]]],
                y.tbody[
                    *[
                        y.tr(
                            **htmx(
                                hx_post=select_item_to_be_added.url(),
                                hx_trigger="click",
                                hx_swap="none",
                                hx_include=f".{DRAWER_CONTENT_CLASSNAME}",
                                hx_vals={"value": option.value},
                                as_dict=True,
                            )
                        )[y.td()[option.label]]
                        for option in options
                    ],
                    (
                        y.tr[
                            y.td(class_="hx-drawer-select__empty")[
                                labels.no_items_available
                            ]
                        ]
                        if not options
                        else None
                    ),
                ],
            ]
        ]

    def config_input(
        self, config: DrawerSelectDrawerConfig, oob: bool = False
    ) -> y.Node:
        """Render the hidden input holding the drawer's serialized state.

        ``oob=True`` marks it for an out-of-band swap so the round-tripped
        state stays in sync after each interaction.
        """
        return y.input(
            type="hidden",
            id=DRAWER_CONFIG_JSON_FIELD,
            name=DRAWER_CONFIG_JSON_FIELD,
            value=config.model_dump_json(),
            **(htmx(hx_swap_oob="outerHTML", as_dict=True) if oob else {}),
        )

    async def get_drawer_config_from_request(
        self, request: Request
    ) -> DrawerSelectDrawerConfig:
        """Rebuild the drawer config from its serialized hidden field in the
        request's form data."""
        form = await request.form()
        return DrawerSelectDrawerConfig.model_validate_json(
            str(form[DRAWER_CONFIG_JSON_FIELD])
        )

    def to_be_added_items(
        self,
        options: Sequence[Option],
        labels: DrawerSelectLabels,
        oob: bool = False,
    ) -> y.Node:
        """Render the staged-selection list, each row with a remove button.

        ``oob=True`` marks the fragment for an htmx out-of-band swap during
        re-renders.
        """
        return y.div(
            id=DRAWER_TO_BE_ADDED_ITEMS_CLASSNAME,
            class_=DRAWER_TO_BE_ADDED_ITEMS_CLASSNAME,
            **(htmx(hx_swap_oob="outerHTML", as_dict=True) if oob else {}),
        )[
            y.table[
                y.thead[y.tr[y.th[labels.selected_items_column], y.th[""]]],
                y.tbody[
                    *[
                        y.tr[
                            y.td()[o.label],
                            y.td(**styles("text-right"))[
                                c.button(
                                    icon="x",
                                    variant="ghost",
                                    size="sm",
                                    aria_label=f"{labels.remove_item} {o.label}",
                                    **htmx(
                                        hx_post=remove_selected_item.url(),
                                        hx_trigger="click",
                                        hx_swap="none",
                                        hx_include=f".{DRAWER_CONTENT_CLASSNAME}",
                                        hx_vals={"value": o.value},
                                    ),
                                )
                            ],
                        ]
                        for o in options
                    ],
                    (
                        y.tr[
                            y.td(colspan="2", class_="hx-drawer-select__empty")[
                                labels.no_items_selected
                            ]
                        ]
                        if not options
                        else None
                    ),
                ],
            ]
        ]

    def oob_refresh(self, config: DrawerSelectDrawerConfig) -> y.Node:
        """Out-of-band fragments re-syncing the drawer body after the staged
        selection changes (an item added or removed)."""
        return y.fragment[
            self.available_items(
                config.get_available_options(), config.labels, oob=True
            ),
            self.to_be_added_items(
                config.get_selected_options(), config.labels, oob=True
            ),
            self.config_input(config, oob=True),
        ]


class _DrawerSelect:
    """The drawer-select component, exposed as the ``drawer_select`` singleton.

    Calling an instance renders the on-page control; ``drawer_content`` renders
    the drawer body. The module-level fragment endpoints drive the interactions
    between the two.
    """

    def __init__(self) -> None:
        self.drawer_content = _DrawerContent()

    def __call__(
        self,
        name: str,
        options: Sequence[Option],
        *,
        value: Sequence[str] | None = None,
        labels: DrawerSelectLabels | None = None,
        disabled: bool = False,
        **_kwargs,
    ) -> y.Node:
        """Render a drawer select control.

        Parameters
        ----------
        name:
            Form field name the selected option values submit under.
        options:
            Full set of selectable options.
        value:
            Option values selected initially.
        labels:
            Overrides for the component's user-facing text. Defaults to
            :class:`DrawerSelectLabels`.
        disabled:
            Render the "Select items" trigger as disabled.
        """
        config = DrawerSelectConfig(
            name=name,
            options=tuple(options),
            value=list(value or []),
            labels=labels or DrawerSelectLabels(),
        )

        element_id = f"{to_kebabcase(name)}--container--{uuid4()!s}"
        return self.control(config, element_id, disabled=disabled)

    def control(
        self,
        config: DrawerSelectConfig,
        element_id: str,
        oob: bool = False,
        disabled: bool = False,
    ) -> y.Node:
        """Render the on-page control: hidden state, the selected-values table,
        and the drawer trigger.

        ``element_id`` scopes the control for htmx targeting; ``oob=True`` marks
        it for an out-of-band swap (used when the drawer submits a new
        selection); ``disabled`` renders the trigger and remove buttons as
        disabled.
        """
        return y.div(
            id=element_id,
            # On an OOB commit/remove swap, mark the control so the DataForm
            # bridge (pyhx.data-form.js) dispatches a `change` from a field
            # input — OOB swaps don't fire one, so the form wouldn't revalidate.
            **({"data-pyhx-revalidate": config.name} if oob else {}),
            **(htmx(hx_swap_oob="outerHTML", as_dict=True) if oob else {}),
        )[
            y.input(
                type="hidden",
                name=f"{CONFIG_JSON_FIELD}__{element_id}",
                value=config.model_dump_json(),
            ),
            y.table[
                y.thead[y.tr[y.th[config.labels.value_column], y.th[""]]],
                y.tbody[
                    self.values(
                        config.name,
                        config.get_selected_options(),
                        element_id,
                        config.labels,
                        disabled,
                    ),
                    y.tr(style="border-bottom: none")[
                        y.td(
                            colspan="2",
                            **styles("text-center", style="border-bottom: none"),
                        )[
                            c.button(
                                config.labels.select_items_button,
                                variant="solid",
                                size="md",
                                disabled=disabled,
                                **c.open_drawer_htmx_attributes(
                                    url=f"{open_drawer.url()}?select_id={element_id}",
                                    id=c.POPUP_DRAWER_CONTENT_ID,
                                    method="POST",
                                    kwargs={
                                        "hx_include": f"#{element_id}",
                                        "hx_trigger": "click",
                                    },
                                ),
                            )
                        ]
                    ],
                ],
            ],
        ]

    async def get_config_from_request(
        self, request: Request, element_id: str
    ) -> DrawerSelectConfig:
        """Rebuild the control config from its serialized hidden field in the
        request's form data.

        ``element_id`` selects this control's config among any others present in
        the same form (the field name is scoped to it — see :meth:`control`).
        """
        form = await request.form()
        return DrawerSelectConfig.model_validate_json(
            str(form[f"{CONFIG_JSON_FIELD}__{element_id}"])
        )

    def values(
        self,
        name: str,
        options: Sequence[Option],
        element_id: str,
        labels: DrawerSelectLabels,
        disabled: bool = False,
    ) -> y.Node:
        """Render one table row per selected option, each with a remove button.

        ``name`` is the form field the hidden value inputs submit under;
        ``element_id`` scopes htmx targeting; ``disabled`` disables the remove
        buttons. Falls back to an empty-state row when nothing is selected.
        """
        return y.fragment[
            *[
                y.tr[
                    y.td()[
                        option.label,
                        y.input(type="hidden", name=name, value=option.value),
                    ],
                    y.td(**styles("text-right"))[
                        c.button(
                            icon="x",
                            variant="ghost",
                            size="sm",
                            aria_label=f"{labels.remove_item} {option.label}",
                            disabled=disabled,
                            **htmx(
                                hx_post=f"{remove_value.url()}?select_id={element_id}",
                                hx_trigger="click",
                                hx_swap="none",
                                hx_include=f"#{element_id}",
                                hx_vals={"value": option.value},
                            ),
                        )
                    ],
                ]
                for option in options
            ],
            y.tr[
                y.td(colspan="2", class_="hx-drawer-select__empty")[
                    labels.no_items_selected
                ]
            ]
            if not options
            else None,
        ]


@drawer_select_endpoints.fragments.post("/drawer-select/drawer/query")
async def query_items(request: Request, query: Annotated[str | None, Form()] = None):
    """Re-filter the available list as the user types, OOB-swapping the list
    and the serialized state."""
    config = await drawer_select.drawer_content.get_drawer_config_from_request(request)
    config.query = query or ""

    return y.fragment[
        drawer_select.drawer_content.available_items(
            config.get_available_options(), config.labels, oob=True
        ),
        drawer_select.drawer_content.config_input(config, oob=True),
    ]


@drawer_select_endpoints.fragments.post("/drawer-select/drawer/select")
async def select_item_to_be_added(
    request: Request, value: Annotated[str, Form()]
) -> y.Node:
    """Add an option to the staged selection and refresh the drawer body."""
    config = await drawer_select.drawer_content.get_drawer_config_from_request(request)
    config.value = _values_in_option_order([*config.value, value], config.options)

    return drawer_select.drawer_content.oob_refresh(config)


@drawer_select_endpoints.fragments.post("/drawer-select/drawer/remove")
async def remove_selected_item(
    request: Request, value: Annotated[str, Form()]
) -> y.Node:
    """Remove an option from the staged selection and refresh the drawer body."""
    config = await drawer_select.drawer_content.get_drawer_config_from_request(request)
    config.value = [v for v in config.value if v != value]

    return drawer_select.drawer_content.oob_refresh(config)


@drawer_select_endpoints.fragments.post("/drawer-select/drawer")
async def open_drawer(request: Request, select_id: Annotated[str, Query()]):
    """Open the picker drawer for the control identified by ``select_id``.

    Seeds the drawer from the control's current state and stashes that state in
    ``nested_state`` so the selection can be committed back on submit.
    """
    config = await drawer_select.get_config_from_request(request, select_id)

    return drawer_select.drawer_content(
        on_submit=f"{on_submit_drawer.url()}?select_id={select_id}",
        options=config.get_available_options(),
        nested_state=config.model_dump_json(),
        labels=config.labels,
    )


@drawer_select_endpoints.fragments.post("/drawer-select/submit-drawer")
async def on_submit_drawer(request: Request, select_id: Annotated[str, Query()]):
    """Commit the drawer's staged selection into the control and close the drawer.

    Merges the staged values onto the originating control config (restored from
    ``nested_state``) and OOB-swaps the refreshed control back into the page.
    """
    drawer_config = await drawer_select.drawer_content.get_drawer_config_from_request(
        request
    )
    config = DrawerSelectConfig.model_validate_json(drawer_config.nested_state)
    config.value = _values_in_option_order(
        [*config.value, *drawer_config.value], config.options
    )

    return y.fragment[
        drawer_select.control(config, select_id, oob=True),
        c.drawer_content(id=c.POPUP_DRAWER_CONTENT_ID),
    ]


@drawer_select_endpoints.fragments.post("/drawer-select/remove")
async def remove_value(
    request: Request,
    value: Annotated[str, Form()],
    select_id: Annotated[str, Query()],
) -> y.Node:
    """Remove a value directly from the on-page control, without opening the
    drawer."""
    config = await drawer_select.get_config_from_request(request, select_id)
    config.value = [v for v in config.value if v != value]

    return drawer_select.control(config, select_id, oob=True)


@drawer_select_endpoints.fragments.get("/drawer-select/close-drawer")
async def close_drawer():
    """Close the drawer without changing the selection."""
    return c.drawer_content(id=c.POPUP_DRAWER_CONTENT_ID)


drawer_select = _DrawerSelect()
