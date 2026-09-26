from typing import Any, Literal, Protocol

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames


class InputFactory(Protocol):
    """Callable shape that :func:`form_field` accepts as its ``input``.

    Any function whose signature accepts ``**kwargs`` and returns an htpy
    node satisfies this. ``y.input`` matches naturally; for multi-arg
    components like ``dropdown_radio`` or ``segment_control`` use
    :func:`functools.partial` to pre-bind the required positional args
    (typically ``options``) before passing the result here.
    """

    def __call__(self, **kwargs) -> y.Node: ...


def textarea_input(**kwargs: Any) -> y.Node:
    """:class:`InputFactory` for a multi-line text control.

    Args:
        **kwargs: Attributes for the ``<textarea>``; ``value`` becomes its content
    """
    value = kwargs.pop("value", "")
    return y.textarea(**kwargs)[value]  # type: ignore[call-overload]


@component
def form_field(
    name: str,
    label: str,
    input: InputFactory,
    *,
    required: bool = False,
    disabled: bool = False,
    help_text: str | None = None,
    error_text: str | None = None,
    success_text: str | None = None,
    class_: str | None = None,
    wrapper: Literal["label", "div"] = "label",
    **kwargs,
) -> y.Node:
    """A labelled form control with help / error / success affordances.

    Wraps a single input-like control in a ``<label>``, places the label
    text on top, the control next, and an optional ``<small>`` help line
    underneath — with ARIA wiring (``aria-describedby``, ``aria-invalid``)
    derived from the state args.

    Parameters
    ----------
    name : str
        Form field name. Set on the rendered control via ``**kwargs``.
    label : str
        Visible label text shown above the control.
    input : InputFactory
        Callable that renders the control. Called as ``input(name=…,
        **kwargs)`` — see :class:`InputFactory`.
    required : bool, default False
        Whether the field is required. Renders a red asterisk next to the
        label text; the underlying input's ``required`` attribute is *not*
        set automatically (pass ``required=True`` via ``**kwargs`` if you
        want browser-level enforcement too).
    disabled : bool, default False
        Forwards ``disabled=True`` to the input factory — every pyhx form
        primitive (``y.input``, ``dropdown_*``, ``segment_control``,
        ``radio_fieldset``, ``checkbox_fieldset``) knows how to honour it.
        The label itself is dimmed via the ``:has(:disabled)`` rule in
        ``form_field.css``.
    help_text : str | None, default None
        Neutral help text shown under the control. Overridden by
        ``error_text`` / ``success_text`` when one of those is set.
    error_text : str | None, default None
        Error message. Sets ``aria-invalid="true"`` on the control so Pico
        renders the error border, and re-colours the help text.
    success_text : str | None, default None
        Success message. Sets ``aria-invalid="false"`` for the green
        border and re-colours the help text.
    class_ : str | None, default None
        Extra class names to add to the wrapping element alongside
        ``hx-form-field``. Useful for grid placement
        (``hx-grid-span-{n}``) when the field sits inside a ``hx-grid``.
    wrapper : "label" | "div", default "label"
        Outer element. ``"label"`` (default) wraps the control in a
        ``<label>`` — correct for a single control, where clicking the label
        focuses it. ``"div"`` wraps in a ``<div>`` and renders the label text
        in a *non-associated* ``<label>`` (linked to the control via
        ``aria-labelledby``). Use ``"div"`` for **composite controls that
        contain multiple buttons/inputs** (e.g. ``drawer_select`` /
        ``drawer_radio``): a ``<label>`` associates with its first labelable
        descendant, so wrapping such a control makes every in-label click also
        fire that first button — clicking anything would trigger the first
        remove button.
    **kwargs
        Forwarded to the input factory as HTML attributes (``type``,
        ``value``, ``placeholder``, ``aria_*``, …).
    """
    attrs: dict[str, Any] = kwargs.copy()
    attrs["name"] = name
    attrs["disabled"] = disabled

    help_text_id = f"{name}__help_text"
    label_id = f"{name}__label"

    if error_text:
        attrs["aria_invalid"] = "true"
        attrs["aria_describedby"] = help_text_id
        help_text = error_text
    elif success_text:
        attrs["aria_invalid"] = "false"
        attrs["aria_describedby"] = help_text_id
        help_text = success_text
    elif help_text:
        attrs["aria_describedby"] = help_text_id

    required_marker = (
        y.span(class_="hx-form-field__required")[" *"] if required else None
    )

    if wrapper == "div":
        # Composite control: the label must NOT wrap it (a <label> forwards
        # clicks to its first labelable descendant — a button — so every
        # click would fire it). Render the label text in a non-associated
        # <label> and link it via aria-labelledby instead.
        attrs["aria_labelledby"] = label_id
        return y.div(**classnames("hx-form-field", class_=class_ or ""))[
            y.label(id=label_id, class_="hx-form-field__label")[label, required_marker],
            input(**attrs),
            y.small(id=help_text_id)[help_text] if help_text else None,
        ]

    return y.label(**classnames("hx-form-field", class_=class_ or ""))[
        label,
        required_marker,
        input(**attrs),
        y.small(id=help_text_id)[help_text] if help_text else None,
    ]
