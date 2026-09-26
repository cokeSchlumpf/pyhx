"""Two-mode selector: pick *all/none* or reveal a picker for a specific set.

``conditional_select`` renders a segmented toggle between a default mode (which
selects nothing specific — the form submits an empty list under ``name``) and a
"specific" mode that reveals an inline multi-select for choosing an explicit
set. The revealed picker is configurable (:data:`SelectControl`): a
``drawer_select`` (default, best for long pools), a ``dropdown_checkbox``, or a
``checkbox_fieldset``.

All interaction is driven by htmx; the component's state round-trips as JSON in a
hidden input (see :class:`ConditionalSelectProps`), so toggling modes never needs
a database round-trip and the chosen set survives switching back and forth.
"""

from collections.abc import Sequence
from typing import Annotated, Literal, cast
from uuid import uuid4

import htpy as y
from fastapi import Query, Request
from pydantic import BaseModel, Field

from pyhx.core import component
from pyhx.core.primitives import classnames, htmx

from ..view_model import Option
from .drawer_select import DrawerSelectLabels, drawer_select
from .dropdown import dropdown_checkbox
from .segment_control import segment_control
from .select_fieldset import checkbox_fieldset

CONFIG_JSON_FIELD = "conditional_select_config"

ConditionalSelectMode = Literal["all", "specific"]
"""Which branch is active: ``"all"`` (nothing specific) or ``"specific"``."""

SelectControl = Literal["drawer", "dropdown", "checkbox"]
"""Which multi-select to reveal in ``"specific"`` mode."""


class ConditionalSelectLabels(BaseModel):
    """User-facing text for a ``conditional_select``.

    A single instance is configured on the public call and stored on the props,
    so the labels survive every htmx round-trip and are available to the render
    functions without being threaded through the endpoint.
    """

    # --- Mode toggle ---
    all_option: str = "All"
    specific_option: str = "Selected"

    # --- Forwarded to the revealed control ---
    drawer: DrawerSelectLabels = Field(default_factory=DrawerSelectLabels)
    """Labels for the ``drawer_select`` (``control="drawer"``)."""
    placeholder: str = "Select ..."
    """Summary placeholder for the ``dropdown_checkbox`` (``control="dropdown"``)."""
    fieldset_legend: str = ""
    """``<legend>`` text for the ``checkbox_fieldset`` (``control="checkbox"``)."""


class ConditionalSelectProps(BaseModel):
    """State serialized into the control's hidden input.

    ``name`` is the form field the selected values submit under; ``mode_name`` is
    the field the toggle submits under. ``value`` holds the currently selected
    option values; ``options`` the full pool. The whole object round-trips as
    JSON so the mode-switch endpoint can rebuild the control without external
    state.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    mode_name: str
    mode: ConditionalSelectMode
    control: SelectControl
    value: list[str] = Field(default_factory=list)
    options: list[Option] = Field(default_factory=list)
    labels: ConditionalSelectLabels = Field(default_factory=ConditionalSelectLabels)
    disabled: bool = False

    @staticmethod
    async def from_request(
        request: Request, element_id: str
    ) -> "ConditionalSelectProps":
        """Rebuild the props from the serialized hidden field in the request.

        ``element_id`` selects this control's config among any others in the same
        form (the field name is scoped to it — see :func:`_render`).
        """
        form = await request.form()
        return ConditionalSelectProps.model_validate_json(
            str(form.get(f"{CONFIG_JSON_FIELD}__{element_id}", "{}"))
        )


@component
def conditional_select(
    name: str,
    options: Sequence[Option],
    *,
    value: Sequence[str] | None = None,
    mode: ConditionalSelectMode = "all",
    mode_name: str | None = None,
    control: SelectControl = "drawer",
    labels: ConditionalSelectLabels | None = None,
    disabled: bool = False,
    **kwargs,
) -> y.Node:
    """A toggle between selecting *all/none* and an explicit set.

    Renders a segmented control switching between two modes. In ``"all"`` mode
    nothing is rendered below the toggle and the form submits **no** values under
    ``name`` — the caller interprets the empty list (typically as "apply to all",
    but the semantics are the caller's: "none" works just as well). In
    ``"specific"`` mode a multi-select (chosen via ``control``) is revealed and
    the picked option values submit under ``name``.

    Parameters
    ----------
    name
        Form field name the selected option values submit under.
    options
        Full set of selectable options.
    value
        Option values selected initially (only meaningful in ``"specific"`` mode).
    mode
        Initial mode. Defaults to ``"all"``.
    mode_name
        Form field name the toggle submits under. Defaults to ``f"{name}__mode"``.
    control
        Which picker to reveal in ``"specific"`` mode: ``"drawer"`` (default),
        ``"dropdown"``, or ``"checkbox"``.
    labels
        User-facing text overrides. See :class:`ConditionalSelectLabels`.
    disabled
        Disable the toggle and the revealed control.
    **kwargs
        Forwarded onto the root element — e.g. ``aria_labelledby`` injected by
        ``form_field(wrapper="div")``.

    Examples
    --------
    >>> conditional_select("tags", options, value=["a"], mode="specific")
    >>> conditional_select(
    ...     "regions", options, control="dropdown",
    ...     labels=ConditionalSelectLabels(all_option="Global", specific_option="Pick"),
    ... )
    """
    props = ConditionalSelectProps(
        name=name,
        mode_name=mode_name or f"{name}__mode",
        mode=mode,
        control=control,
        value=list(value or []),
        options=list(options),
        labels=labels or ConditionalSelectLabels(),
        disabled=disabled,
    )
    return _render(props, **kwargs)


@conditional_select.fragments.post("/switch-mode")
async def _switch_mode(request: Request, element_id: Annotated[str, Query]) -> y.Node:
    """Re-render the control when the mode toggle changes.

    Triggered only by the toggle (not by the revealed picker's own inputs), so
    interacting with a ``dropdown``/``checkbox`` picker never collapses it.
    """
    props = await ConditionalSelectProps.from_request(request, element_id)
    form = await request.form()
    # Capture the live picker selection *before* switching, but only when the
    # picker was actually on screen (previous mode was "specific"). This keeps the
    # chosen set across an all -> specific -> all -> specific round trip: in "all"
    # mode there are no value inputs, so reading the form unconditionally would
    # wipe the round-tripped selection.
    if props.mode == "specific":
        props.value = [str(v) for v in form.getlist(props.name)]
    props.mode = cast(ConditionalSelectMode, str(form.get(props.mode_name, "all")))
    return _render(props)


def _render(props: ConditionalSelectProps, **kwargs) -> y.Node:
    return y.div(id=props.id, **classnames("hx-conditional-select", **kwargs))[
        y.input(
            type="hidden",
            name=f"{CONFIG_JSON_FIELD}__{props.id}",
            value=props.model_dump_json(),
        ),
        y.div(
            **classnames("hx-conditional-select__toggle"),
            **htmx(
                hx_post=f"{_switch_mode.url()}?element_id={props.id}",
                hx_trigger="change",
                # Target the root container via ``closest`` rather than ``#{id}``:
                # the id is a raw uuid4 that often starts with a digit, which is an
                # invalid CSS id selector (``querySelector`` throws and the swap
                # silently fails). ``closest`` sidesteps id-escaping entirely.
                hx_target="closest .hx-conditional-select",
                hx_swap="outerHTML",
                hx_include="closest .hx-conditional-select",
                as_dict=True,
            ),
        )[
            segment_control(
                props.mode_name,
                options=[
                    Option.of(props.labels.all_option, "all"),
                    Option.of(props.labels.specific_option, "specific"),
                ],
                value=str(props.mode),
                disabled=props.disabled,
            )
        ],
        _revealed_control(props) if props.mode == "specific" else None,
    ]


def _revealed_control(props: ConditionalSelectProps) -> y.Node:
    if props.control == "drawer":
        return drawer_select(
            name=props.name,
            options=props.options,
            value=props.value,
            labels=props.labels.drawer,
            disabled=props.disabled,
        )
    if props.control == "dropdown":
        return dropdown_checkbox(
            props.name,
            props.options,
            value=props.value,
            placeholder=props.labels.placeholder,
            disabled=props.disabled,
        )
    return checkbox_fieldset(
        props.labels.fieldset_legend,
        props.name,
        props.options,
        value=props.value,
        disabled=props.disabled,
    )
