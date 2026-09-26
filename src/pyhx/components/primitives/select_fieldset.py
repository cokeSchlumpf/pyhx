"""Radio / checkbox group rendered as a Pico ``<fieldset>`` + ``<legend>``.

Use these when you need an *accessible group* of radio or checkbox controls
under a single visible label — the ``<legend>`` is what screen readers
announce to associate every option with its group. For a single
form-control wrapped in a per-input ``<label>``, see :func:`form_field`.
"""

from collections.abc import Sequence
from typing import Literal

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames

from ..variants import Orientation
from ..view_model import Option


def _select_fieldset(
    label: str,
    name: str,
    options: Sequence[Option],
    *,
    input_type: Literal["radio", "checkbox"],
    value: str | Sequence[str] | None = None,
    orientation: Orientation = "vertical",
    disabled: bool = False,
    **kwargs,
) -> y.Node:
    """Shared implementation behind :func:`radio_fieldset` /
    :func:`checkbox_fieldset` — not intended for direct use.

    Layout switches on ``orientation``:

    * ``"vertical"`` wraps each input in its own ``<label>`` so they stack.
    * ``"horizontal"`` emits sibling ``<input>``/``<label for=…>`` pairs so
      Pico's flex-row form styling can lay them out side by side.

    Parameters
    ----------
    label : str
        Visible group label (rendered as ``<legend>``).
    name : str
        Form field name shared by every input in the group.
    options : Sequence[Option]
        The selectable choices.
    input_type : Literal["radio", "checkbox"]
        Which control to render. ``"radio"`` enforces single-select via the
        browser's name-grouping; ``"checkbox"`` allows multi-select.
    value : str | Sequence[str] | None, default None
        Initially-selected value(s). A ``str`` matches a single ``Option``;
        a sequence marks every matching option (the natural shape for
        checkboxes). ``None`` leaves everything unchecked.
    orientation : Orientation, default "vertical"
        Stacking direction — see above.
    **kwargs
        Forwarded to the ``<fieldset>`` element (e.g. ``class_=``,
        ``data-*``, ``aria_*``).
    """

    def is_checked(option_value: str) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return value == option_value
        return option_value in value

    items: list[y.Node] = []
    for option in options:
        option_id = f"{name}__{option.value}"
        if orientation == "vertical":
            items.append(
                y.label[
                    y.input(
                        type=input_type,
                        name=name,
                        value=option.value,
                        checked=is_checked(option.value),
                    ),
                    option.label,
                ]
            )
        else:
            items.extend(
                [
                    y.input(
                        type=input_type,
                        id=option_id,
                        name=name,
                        value=option.value,
                        checked=is_checked(option.value),
                    ),
                    y.label(for_=option_id)[option.label],
                ]
            )

    fieldset = y.fieldset(
        disabled=disabled, **classnames("hx-select-fieldset", **kwargs)
    )[
        y.legend[label],
        *items,
    ]
    if disabled:
        # A disabled <fieldset> cascades disabled to every descendant form
        # control — including a hidden input placed inside it — so the value
        # siblings must live *outside* the fieldset to still submit.
        return y.fragment[fieldset, *_disabled_value_inputs(input_type, name, value)]
    return fieldset


def _disabled_value_inputs(
    input_type: Literal["radio", "checkbox"],
    name: str,
    value: str | Sequence[str] | None,
) -> list[y.Node]:
    """Hidden inputs echoing the selected value(s) of a disabled fieldset.

    A browser never submits a disabled form control's value, and a disabled
    ``<fieldset>`` disables every control inside it. For a required/closed-choice
    field, "missing" isn't a valid value either, so that would fail validation on
    every submit, not just leave the field alone. These hidden siblings are never
    disabled themselves, so they always submit the actual current value regardless
    of the visible controls' state.
    """
    if input_type == "radio":
        return [y.input(type="hidden", name=name, value=value)] if value else []
    return [y.input(type="hidden", name=name, value=v) for v in value or ()]


@component
def radio_fieldset(
    label: str,
    name: str,
    options: Sequence[Option],
    *,
    value: str | None = None,
    orientation: Orientation = "vertical",
    disabled: bool = False,
    **kwargs,
) -> y.Node:
    """Single-select group of radio buttons grouped by a ``<legend>``.

    Parameters
    ----------
    label : str
        Visible group label, rendered as ``<legend>``.
    name : str
        Form field name shared by every radio in the group.
    options : Sequence[Option]
        The selectable choices.
    value : str | None, default None
        Currently-selected option's value, or ``None`` for an unselected
        group.
    orientation : Orientation, default "vertical"
        ``"vertical"`` stacks the options; ``"horizontal"`` lays them out
        side by side.
    disabled : bool, default False
        When True, emits ``<fieldset disabled>`` — HTML cascades the
        disabled state to every contained form control automatically. A
        disabled control is excluded from what the browser submits, so a
        hidden input per currently-selected value is added alongside the
        fieldset (outside it, since the cascade would disable a hidden
        child too) — otherwise the field would arrive server-side as
        missing rather than unchanged. The CSS in ``select_fieldset.css``
        adds the muted look.
    **kwargs
        Forwarded to the ``<fieldset>`` element.
    """
    return _select_fieldset(
        label,
        name,
        options,
        input_type="radio",
        value=value,
        orientation=orientation,
        disabled=disabled,
        **kwargs,
    )


@component
def checkbox_fieldset(
    label: str,
    name: str,
    options: Sequence[Option],
    *,
    value: Sequence[str] | None = None,
    orientation: Orientation = "vertical",
    disabled: bool = False,
    **kwargs,
) -> y.Node:
    """Multi-select group of checkboxes grouped by a ``<legend>``.

    Parameters
    ----------
    label : str
        Visible group label, rendered as ``<legend>``.
    name : str
        Form field name shared by every checkbox in the group. The browser
        submits one ``name=value`` pair per checked box.
    options : Sequence[Option]
        The selectable choices.
    value : Sequence[str] | None, default None
        Currently-selected values. Every option whose ``value`` is in the
        sequence is rendered checked.
    orientation : Orientation, default "vertical"
        ``"vertical"`` stacks the options; ``"horizontal"`` lays them out
        side by side.
    disabled : bool, default False
        When True, emits ``<fieldset disabled>`` — HTML cascades the
        disabled state to every contained form control automatically. A
        disabled control is excluded from what the browser submits, so a
        hidden input per currently-selected value is added alongside the
        fieldset (outside it, since the cascade would disable a hidden
        child too) — otherwise the field would arrive server-side as
        missing rather than unchanged. The CSS in ``select_fieldset.css``
        adds the muted look.
    **kwargs
        Forwarded to the ``<fieldset>`` element.
    """
    return _select_fieldset(
        label,
        name,
        options,
        input_type="checkbox",
        value=value,
        orientation=orientation,
        disabled=disabled,
        **kwargs,
    )
