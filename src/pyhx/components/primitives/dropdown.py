from collections.abc import Sequence
from typing import Literal
from uuid import uuid4

import htpy as y
from commons.string_operators import to_kebabcase
from pydantic import BaseModel

from pyhx.core import RequestContext, component
from pyhx.core.primitives import classnames, htmx

from ..view_model import Option, Options

InputType = Literal["radio", "checkbox"]


class DropdownConfig(BaseModel):
    target_id: str
    options: Options
    field_name: str
    placeholder: str
    input_type: InputType


@component
def dropdown(
    name: str,
    options: Sequence[Option],
    *,
    input_type: InputType,
    value: str | Sequence[str] | None = None,
    placeholder: str = "Select ...",
    disabled: bool = False,
    **kwargs,
) -> y.Node:
    """Dropdown built on Pico's ``<details class="dropdown">`` + radio or checkbox inputs.

    Set ``input_type="radio"`` for single-select (``value`` is a single value or None),
    or ``input_type="checkbox"`` for multi-select (``value`` is a sequence of selected
    values, or None). The visible summary label is recomputed on every change via an
    htmx fragment, so the dropdown always shows what the user actually picked.

    ``disabled=True`` propagates ``disabled`` to every inner ``<input>`` (so
    selection can't change) and marks the ``<details>`` wrapper with
    ``aria-disabled="true"``; the CSS rule in ``dropdown.css`` keys off the wrapper
    attribute to suppress summary clicks and dim the control. A disabled radio/
    checkbox is excluded from what the browser submits, so a hidden input
    per currently-selected value is added alongside them.

    Prefer the :func:`dropdown_radio` / :func:`dropdown_checkbox` convenience wrappers
    at call sites — they pin ``input_type`` and narrow the ``value`` type.
    """
    options = tuple(options)
    # Unique per instance (not derived solely from ``name``) so two dropdowns
    # sharing a ``name`` on the same page get distinct summary targets — the
    # label-recompute swap must hit the dropdown that changed, not the first one
    # with that name. The static ``hx-`` prefix keeps the id a valid CSS selector
    # for ``hx-target``: a CSS id can't start with a digit, and neither the uuid
    # suffix nor ``name`` is guaranteed to start with a letter (callers may prefix
    # the field name with a record uuid, e.g. ``<uuid>-client-domicile``).
    summary_id = f"hx-{to_kebabcase(name)}--summary--{uuid4().hex}"
    cfg = DropdownConfig(
        target_id=summary_id,
        options=Options(options=list(options)),
        field_name=name,
        placeholder=placeholder,
        input_type=input_type,
    ).model_dump_json()

    details_attrs: dict = {}
    if disabled:
        details_attrs["aria_disabled"] = "true"
        details_attrs["inert"] = True

    return y.details(
        **{
            **htmx(
                hx_post=update_options_label.url(),
                hx_trigger="change",
                hx_target=f"#{summary_id}",
                hx_swap="outerHTML",
                hx_vals={"hx_dropdown__cfg": cfg},
                # ``this`` includes every option input inside the dropdown. A
                # ``find input[name=…]`` selector only matches the *first*
                # descendant, so the multi-select label recompute would only ever
                # see the first checkbox's state (label stuck unless the first
                # option was the one toggled).
                hx_include="this",
                as_dict=True,
            ),
            **details_attrs,
            **classnames("dropdown", **kwargs),
        },
    )[
        y.summary(id=summary_id)[
            y.span[_get_options_label(options, value, placeholder)]
        ],
        y.ul[
            [
                y.li[
                    y.label[
                        y.input(
                            type=input_type,
                            name=name,
                            value=option.value,
                            checked=_is_checked(option.value, value),
                            disabled=disabled,
                            autocomplete="off",
                        ),
                        option.label,
                    ]
                ]
                for option in options
            ]
        ],
        *(_disabled_value_inputs(name, input_type, value) if disabled else []),
    ]


def dropdown_radio(
    name: str,
    options: Sequence[Option],
    value: str | None = None,
    placeholder: str = "Select ...",
    disabled: bool = False,
    **kwargs,
) -> y.Node:
    """Single-select dropdown. Thin wrapper over :func:`dropdown`."""
    return dropdown(
        name,
        options,
        input_type="radio",
        value=value,
        placeholder=placeholder,
        disabled=disabled,
        **kwargs,
    )


def dropdown_checkbox(
    name: str,
    options: Sequence[Option],
    value: Sequence[str] | None = None,
    placeholder: str = "Select ...",
    disabled: bool = False,
    **kwargs,
) -> y.Node:
    """Multi-select dropdown. Thin wrapper over :func:`dropdown`."""
    return dropdown(
        name,
        options,
        input_type="checkbox",
        value=value,
        placeholder=placeholder,
        disabled=disabled,
        **kwargs,
    )


@dropdown.fragments.post("/label")
async def update_options_label() -> y.Node:
    request = RequestContext.get().request
    assert request is not None

    form = await request.form()
    cfg = DropdownConfig.model_validate_json(str(form["hx_dropdown__cfg"]))

    value: str | list[str] | None
    if cfg.input_type == "radio":
        value = str(form[cfg.field_name]) if cfg.field_name in form else None
    else:
        raw = form.getlist(cfg.field_name)
        value = [str(v) for v in raw] if raw else None

    return y.summary(id=cfg.target_id)[
        y.span[_get_options_label(cfg.options.options, value, cfg.placeholder)]
    ]


def _disabled_value_inputs(
    name: str, input_type: InputType, value: str | Sequence[str] | None
) -> list[y.Node]:
    """Hidden inputs echoing the selected value(s) of a disabled dropdown.

    A browser never submits a disabled form control's value. For a required/closed-choice
    field (e.g. a ``Literal``), "missing" isn't a valid value either, so that
    would fail validation on every submit, not just leave the field alone.
    These hidden siblings are never disabled themselves, so they always
    submit the actual current value regardless of the visible controls' state.
    """
    if input_type == "radio":
        return [y.input(type="hidden", name=name, value=value)] if value else []
    return [y.input(type="hidden", name=name, value=v) for v in value or ()]


def _is_checked(option_value: str, value: str | Sequence[str] | None) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value == option_value
    return option_value in value


def _get_options_label(
    options: Sequence[Option],
    value: str | Sequence[str] | None,
    placeholder: str,
) -> y.Node:
    labels = [o.label for o in options if _is_checked(o.value, value)]
    if not labels:
        return placeholder
    return ", ".join(labels)
