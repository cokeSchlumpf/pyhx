import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames


@component
def switch(
    *,
    checked: bool,
    name: str | None = None,
    disabled: bool = False,
    aria_label: str | None = None,
    **kwargs,
) -> y.Node:
    """A boolean on/off switch.

    A real ``<input type="checkbox" role="switch">``, styled entirely by pico.
    Submits like a checkbox when ``name`` is set; toggling fires htmx's default
    ``change`` trigger, so no ``hx_trigger`` override is needed.

    Parameters
    ----------
    checked
        The current on/off state.
    name
        Optional form field name, if this switch should submit like a normal
        checkbox (e.g. as a ``DataForm`` boolean control). Omit for a
        display-only switch driven entirely by htmx attributes.
    disabled
        When True, the switch cannot be toggled.
    aria_label
        Accessible label for screen readers - required unless the switch sits
        next to its own visible text label.

    Examples
    --------
    >>> switch(
    ...     checked=todo.action_required,
    ...     aria_label="Action required",
    ...     **htmx(
    ...         hx_post=set_action_required.url(note_id=todo.id),
    ...         hx_vals={"action_required": not todo.action_required},
    ...         hx_swap="none",
    ...     ),
    ... )
    """
    return y.input(
        type="checkbox",
        role="switch",
        checked=checked,
        name=name,
        disabled=disabled,
        aria_label=aria_label,
        **classnames("hx-switch", **kwargs),
    )
