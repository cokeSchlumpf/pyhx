from collections.abc import Sequence

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames

from ..variants import Size
from ..view_model import Option


@component
def segment_control(
    name: str,
    options: Sequence[Option],
    *,
    value: str | None = None,
    size: Size = "md",
    disabled: bool = False,
    **kwargs,
) -> y.Node:
    """A segmented control: a row of buttons acting as a radio group.

    Renders as a real ``<input type="radio">`` group wrapped in labels, so it
    submits like a normal form field, supports keyboard navigation out of the
    box, and needs no JavaScript. The visible "selected" state is driven by
    CSS ``:has(:checked)``.

    Parameters
    ----------
    name
        The ``name`` attribute shared by every radio input — what the form
        submits the selected value under.
    options
        The choices, in display order. ``Option.label`` is the visible text;
        ``Option.value`` is the submitted value.
    value
        The currently-selected option's value, if any.
    size
        ``"sm" | "md" | "lg"``. Drives padding and font-size.
    disabled
        When True, ``disabled`` is set on every radio (so selection can't
        change) and ``aria-disabled="true"`` on the wrapper. A disabled radio is excluded from
        what the browser submits, so a hidden input carrying ``value`` is
        added alongside — otherwise the field would arrive server-side as
        missing rather than unchanged, which fails validation outright for
        a required/closed-choice field instead of just leaving it alone.

    Examples
    --------
    >>> segment_control(
    ...     "view",
    ...     [Option("List", "list"), Option("Grid", "grid")],
    ...     value="list",
    ... )
    """
    options = tuple(options)
    classes = ["hx-segment-control", f"hx-segment-control--{size}"]

    wrapper_attrs: dict = {"role": "radiogroup"}
    if disabled:
        wrapper_attrs["aria_disabled"] = "true"

    return y.div(**wrapper_attrs, **classnames(classes, **kwargs))[
        [
            y.label(class_="hx-segment-control__option")[
                y.input(
                    type="radio",
                    name=name,
                    value=option.value,
                    checked=option.value == value,
                    disabled=disabled,
                ),
                y.span[option.label],
            ]
            for option in options
        ],
        y.input(type="hidden", name=name, value=value) if disabled and value else None,
    ]
