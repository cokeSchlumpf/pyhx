"""Drawer-based single-option picker.

``drawer_radio`` is the single-selection sibling of ``drawer_select``. The
on-page control shows the selected option's label (or a placeholder) plus a
ghost clear button and a trigger; a button opens a drawer where the user filters
the available options and **clicks one to commit it** — the click both swaps the
on-page control and closes the drawer in a single htmx response. There is no
staged list and no confirm step. Component state round-trips as JSON in a hidden
input (see :class:`DrawerRadioConfig`).
"""

from collections.abc import Sequence
from typing import Annotated
from uuid import uuid4

import htpy as y
from fastapi import Form, Query, Request
from pydantic import BaseModel, Field

import pyhx.components as c
from pyhx.core import component
from pyhx.core.primitives import htmx

from ..view_model import Option

CONFIG_JSON_FIELD = "drawer_radio_config_json"
DRAWER_AVAILABLE_ITEMS_CLASSNAME = "hx-drawer-radio__available-items"
DRAWER_CONTENT_CLASSNAME = "hx-drawer-radio__drawer-content"


class DrawerRadioLabels(BaseModel):
    """User-facing text for every part of a ``drawer_radio``.

    A single instance is configured on the public ``drawer_radio(...)`` call and
    stored on the config object, so the labels survive every htmx round-trip
    (open, filter, select, clear) without being threaded through each endpoint.
    """

    # --- Main control (on-page) ---
    value_label: str = "Value"
    select_item_button: str = "Select item"
    clear_item: str = "Clear selection"
    no_item_selected: str = "No selected item."

    # --- Drawer ---
    drawer_title: str = "Select item"
    query_label: str = "Filter items"
    available_items_column: str = "Available items"
    cancel_button: str = "Cancel"
    no_items_available: str = "No available items."


class DrawerRadioConfig(BaseModel):
    """State of a ``drawer_radio``, serialized into a hidden input.

    One model serves both the on-page control and the open drawer (there is no
    staged selection to round-trip separately). ``name`` is the form field the
    selected value submits under; ``value`` is the single selected option value;
    ``select_id`` is the on-page control's element id, carried so the drawer can
    target it on commit; ``query`` is the current filter text.
    """

    options: tuple[Option, ...]
    value: str | None = None
    name: str
    select_id: str = ""
    query: str = ""
    labels: DrawerRadioLabels = Field(default_factory=DrawerRadioLabels)

    def get_selected_option(self) -> Option | None:
        """The currently selected option, or ``None`` when nothing is selected."""
        return next((o for o in self.options if o.value == self.value), None)

    def get_available_options(self) -> tuple[Option, ...]:
        """Options whose label matches the current ``query`` filter.

        The current selection is not excluded — re-picking it is a harmless
        no-op and keeps the list stable as the user browses.
        """
        return tuple(o for o in self.options if self.query.lower() in o.label.lower())


@component
def drawer_radio_endpoints() -> y.Node:
    """Mount point for the drawer-radio htmx fragment routes.

    Renders nothing visible; including this component in an app registers the
    fragment endpoints defined below so the drawer's interactions resolve.
    """
    return y.fragment[""]


class _DrawerContent:
    """Renders the drawer body and the out-of-band fragments that keep it in
    sync as the user filters.

    Exposed as ``drawer_radio.drawer_content``; the fragment endpoints call its
    methods to re-render the available list while the drawer is open.
    """

    def __call__(self, config: DrawerRadioConfig) -> y.Node:
        """Render the drawer body: a filter box and the available-items list.

        Clicking a row commits that option (see :func:`select_item`); there is
        no staged list and no Select button — only Cancel.
        """
        return c.drawer_content(
            y.div(class_=DRAWER_CONTENT_CLASSNAME)[
                y.div(
                    class_="hx-drawer-radio__search",
                    hx_post=query_items.url(),
                    hx_trigger="input delay:200ms",
                    hx_target=f".{DRAWER_AVAILABLE_ITEMS_CLASSNAME}",
                    hx_swap="none",
                    hx_include="this",
                    as_dict=True,
                )[
                    self.config_input(config),
                    c.form_field("query", config.labels.query_label, y.input()),
                ],
                self.available_items(config),
                y.div(class_="hx-drawer-radio__actions")[
                    c.button(
                        config.labels.cancel_button,
                        **htmx(hx_get=close_drawer.url(), hx_swap="none"),
                    ),
                ],
            ],
            id=c.POPUP_DRAWER_CONTENT_ID,
            title=config.labels.drawer_title,
        )

    def available_items(self, config: DrawerRadioConfig, oob: bool = False) -> y.Node:
        """Render the filterable list of selectable options.

        Each row commits itself on click, posting to :func:`select_item`.
        ``oob=True`` marks the fragment for an htmx out-of-band swap.
        """
        commit_url = f"{select_item.url()}?select_id={config.select_id}"
        options = config.get_available_options()
        return y.div(
            id=DRAWER_AVAILABLE_ITEMS_CLASSNAME,
            class_=DRAWER_AVAILABLE_ITEMS_CLASSNAME,
            **(htmx(hx_swap_oob="outerHTML", as_dict=True) if oob else {}),
        )[
            y.table[
                y.thead[y.tr[y.th[config.labels.available_items_column]]],
                y.tbody[
                    *[
                        y.tr(
                            **htmx(
                                hx_post=commit_url,
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
                            y.td(class_="hx-drawer-radio__empty")[
                                config.labels.no_items_available
                            ]
                        ]
                        if not options
                        else None
                    ),
                ],
            ]
        ]

    def config_input(self, config: DrawerRadioConfig, oob: bool = False) -> y.Node:
        """Render the hidden input holding the drawer's serialized state.

        ``oob=True`` marks it for an out-of-band swap so the round-tripped state
        stays in sync after each interaction.
        """
        return y.input(
            type="hidden",
            id=CONFIG_JSON_FIELD,
            name=CONFIG_JSON_FIELD,
            value=config.model_dump_json(),
            **(htmx(hx_swap_oob="outerHTML", as_dict=True) if oob else {}),
        )

    def query_filter_oob(self, config: DrawerRadioConfig) -> y.Node:
        """Out-of-band fragments re-syncing the available list after a filter
        change."""
        return y.fragment[
            self.available_items(config, oob=True),
            self.config_input(config, oob=True),
        ]

    async def get_config_from_request(self, request: Request) -> DrawerRadioConfig:
        """Rebuild the config from its serialized hidden field in the request's
        form data."""
        form = await request.form()
        return DrawerRadioConfig.model_validate_json(str(form[CONFIG_JSON_FIELD]))


class _DrawerRadio:
    """The drawer-radio component, exposed as the ``drawer_radio`` singleton.

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
        value: str | None = None,
        labels: DrawerRadioLabels | None = None,
        disabled: bool = False,
        **_kwargs,
    ) -> y.Node:
        """Render a single-selection drawer control.

        Parameters
        ----------
        name:
            Form field name the selected option value submits under.
        options:
            Full set of selectable options.
        value:
            Option value selected initially, or ``None`` for no selection.
        labels:
            Overrides for the component's user-facing text. Defaults to
            :class:`DrawerRadioLabels`.
        disabled:
            Render the trigger (and clear) buttons as disabled.
        """
        element_id = f"{name}--container--{uuid4()!s}"
        config = DrawerRadioConfig(
            name=name,
            options=tuple(options),
            value=value,
            select_id=element_id,
            labels=labels or DrawerRadioLabels(),
        )
        return self.control(config, element_id, disabled=disabled)

    def control(
        self,
        config: DrawerRadioConfig,
        element_id: str,
        oob: bool = False,
        disabled: bool = False,
    ) -> y.Node:
        """Render the on-page control: hidden state, the selected value (or a
        placeholder) with a clear button, and the drawer trigger.

        ``element_id`` scopes the control for htmx targeting; ``oob=True`` marks
        it for an out-of-band swap (used when an item is committed from the
        drawer); ``disabled`` renders the buttons as disabled.
        """
        selected = config.get_selected_option()
        labels = config.labels
        return y.div(
            id=element_id,
            class_="hx-drawer-radio__control",
            # On an OOB commit/clear swap, mark the control so the DataForm
            # bridge (pyhx.data-form.js) dispatches a `change` from the field
            # input — OOB swaps don't fire one, so the form wouldn't revalidate.
            **({"data-pyhx-revalidate": config.name} if oob else {}),
            **(htmx(hx_swap_oob="outerHTML", as_dict=True) if oob else {}),
        )[
            y.input(
                type="hidden", name=CONFIG_JSON_FIELD, value=config.model_dump_json()
            ),
            (
                y.input(type="hidden", name=config.name, value=config.value)
                if config.value is not None
                else None
            ),
            y.div(class_="hx-drawer-radio__field")[
                y.input(
                    type="text",
                    class_="hx-drawer-radio__value",
                    value=selected.label if selected is not None else "",
                    placeholder=labels.no_item_selected,
                    aria_label=labels.value_label,
                    # Display-only: no name, so it never submits (the hidden
                    # input above carries the value). `readonly` keeps it
                    # legible and form-field-like (and, unlike `disabled`,
                    # still fires the focus event below); `disabled` greys it
                    # out with the control.
                    readonly=True,
                    disabled=disabled,
                    # Open the drawer when the value field is clicked or
                    # focused, mirroring the trigger button. `focus` covers
                    # both a mouse click and keyboard tab-in with one event
                    # (so it never double-fires). Omitted when disabled, which
                    # would suppress the event anyway.
                    **(
                        c.open_drawer_htmx_attributes(
                            url=open_drawer.url(),
                            id=c.POPUP_DRAWER_CONTENT_ID,
                            method="POST",
                            as_dict=True,
                            kwargs={
                                "hx_include": f"#{element_id}",
                                "hx_trigger": "focus",
                            },
                        )
                        if not disabled
                        else {}
                    ),
                ),
                (
                    c.button(
                        icon="x",
                        variant="ghost",
                        size="sm",
                        class_="hx-drawer-radio__clear",
                        aria_label=labels.clear_item,
                        disabled=disabled,
                        **htmx(
                            hx_post=f"{clear_value.url()}?select_id={element_id}",
                            hx_trigger="click",
                            hx_swap="none",
                            hx_include=f"#{element_id}",
                        ),
                    )
                    if selected is not None
                    else None
                ),
            ],
            c.button(
                labels.select_item_button,
                variant="solid",
                size="md",
                appearance="neutral",
                disabled=disabled,
                **c.open_drawer_htmx_attributes(
                    url=open_drawer.url(),
                    id=c.POPUP_DRAWER_CONTENT_ID,
                    method="POST",
                    kwargs={
                        "hx_include": f"#{element_id}",
                        "hx_trigger": "click",
                    },
                ),
            ),
        ]

    async def get_config_from_request(self, request: Request) -> DrawerRadioConfig:
        """Rebuild the control config from its serialized hidden field in the
        request's form data."""
        form = await request.form()
        return DrawerRadioConfig.model_validate_json(str(form[CONFIG_JSON_FIELD]))


@drawer_radio_endpoints.fragments.post("/drawer-radio/drawer")
async def open_drawer(request: Request):
    """Open the picker drawer for the triggering control.

    Seeds the drawer from the control's current state (carried in the hidden
    config input, including its ``select_id``), so the filter list and commit
    target are ready immediately.
    """
    config = await drawer_radio.get_config_from_request(request)
    config.query = ""
    return drawer_radio.drawer_content(config)


@drawer_radio_endpoints.fragments.post("/drawer-radio/drawer/query")
async def query_items(request: Request, query: Annotated[str | None, Form()] = None):
    """Re-filter the available list as the user types, OOB-swapping the list and
    the serialized state."""
    config = await drawer_radio.drawer_content.get_config_from_request(request)
    config.query = query or ""
    return drawer_radio.drawer_content.query_filter_oob(config)


@drawer_radio_endpoints.fragments.post("/drawer-radio/drawer/select")
async def select_item(
    request: Request,
    value: Annotated[str, Form()],
    select_id: Annotated[str, Query()],
) -> y.Node:
    """Commit the clicked option into the control and close the drawer.

    Single-select: sets the value, OOB-swaps the on-page control, and returns an
    empty drawer body to close the drawer — all in one response.
    """
    config = await drawer_radio.drawer_content.get_config_from_request(request)
    config.value = value
    config.query = ""
    return y.fragment[
        drawer_radio.control(config, select_id, oob=True),
        c.drawer_content(id=c.POPUP_DRAWER_CONTENT_ID),
    ]


@drawer_radio_endpoints.fragments.post("/drawer-radio/clear")
async def clear_value(request: Request, select_id: Annotated[str, Query()]) -> y.Node:
    """Clear the selection back to the placeholder, without opening the drawer."""
    config = await drawer_radio.get_config_from_request(request)
    config.value = None
    return drawer_radio.control(config, select_id, oob=True)


@drawer_radio_endpoints.fragments.get("/drawer-radio/close-drawer")
async def close_drawer():
    """Close the drawer without changing the selection."""
    return c.drawer_content(id=c.POPUP_DRAWER_CONTENT_ID)


drawer_radio = _DrawerRadio()
