"""Build Pydantic ``ValidationError`` from pure-Python (non-model) code.

The UI's error handling already iterates ``ValidationError.errors()`` to
key per-field messages onto controls. Domain code that doesn't use
Pydantic models can raise the *same exception type* via
:func:`validation_error`, so both paths flow through the same renderer.

Messages are **templates**: ``"must be at least {min} chars"`` with
named ``{placeholder}`` slots. Parameters are passed separately and
end up on the error's ``ctx`` dict, where:

* the rendered ``msg`` shows the substituted string today, and
* the raw ``type`` (treat as a translation key) + ``ctx`` give an i18n
  layer everything it needs to render against a translated template
  tomorrow — without touching the call sites.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, LiteralString, cast

from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError


@dataclass(frozen=True)
class FieldError:
    """One per-field entry for :func:`validation_error`.

    Attributes
    ----------
    loc : tuple[str | int, ...]
        Path to the field. Single name → ``("name",)``; nested →
        ``("address", "zip")``; list index → ``("items", 0, "qty")``.
    msg : str
        Message template — ``{placeholder}`` slots are filled from
        ``params`` for display; the unsubstituted template + ``params``
        survive on the error's ``ctx`` so i18n can re-render later.
    type : str
        Stable error code. Treat as the translation key in i18n.
        Defaults to ``"value_error"`` to match the type Pydantic
        produces when a validator raises ``ValueError``.
    params : Mapping[str, Any]
        Values for the ``{placeholder}``s in ``msg``. Surface as
        ``ctx`` on the resulting Pydantic error.
    """

    loc: tuple[str | int, ...]
    msg: str
    type: str = "value_error"
    params: Mapping[str, Any] = field(default_factory=dict)


def field_error(
    loc: str | tuple[str | int, ...],
    msg: str,
    *,
    type: str = "value_error",
    **params: Any,
) -> FieldError:
    """Sugar for building a :class:`FieldError`.

    ``loc`` accepts a bare string (wrapped to a one-element tuple) or
    an explicit nested path. Keyword arguments after ``type`` are
    captured as ``params`` — both substituted into ``msg`` and exposed
    as ``ctx`` on the resulting error for later i18n.

    Examples
    --------
    >>> field_error("code", "must be uppercase")
    >>> field_error("name", "must be at least {min} chars",
    ...             type="string_too_short", min=3)
    >>> field_error(("address", "zip"), "invalid {country} zip",
    ...             type="zip_invalid", country="CH")
    """
    return FieldError(
        loc=(loc,) if isinstance(loc, str) else loc,
        msg=msg,
        type=type,
        params=params,
    )


def validation_error(
    errors: Mapping[str, str] | FieldError | Sequence[FieldError],
    title: str = "ValidationError",
) -> ValidationError:
    """Build a Pydantic ``ValidationError`` from a friendly input.

    Accepts three input shapes:

    1. ``{field: message}`` — the simple flat case, no params, default
       ``type``. Each entry becomes one :class:`FieldError`.
    2. A single :class:`FieldError` — when you only have one to raise
       and want params / a custom ``type``.
    3. A sequence of :class:`FieldError` — multiple errors surfaced at
       once. The UI shows them all simultaneously.

    The returned ``ValidationError`` is the genuine Pydantic class, so
    handlers that catch ``pydantic.ValidationError`` see no difference
    between model-raised and domain-raised validation errors.

    Examples
    --------
    >>> raise validation_error({"code": "must be uppercase"})
    >>> raise validation_error(
    ...     field_error("name", "must be at least {min} chars", min=3),
    ... )
    >>> raise validation_error([
    ...     field_error("code", "must be uppercase"),
    ...     field_error("name", "must be at least {min} chars",
    ...                 type="too_short", min=3),
    ... ])
    """
    if isinstance(errors, FieldError):
        items: list[FieldError] = [errors]
    elif isinstance(errors, Mapping):
        items = [FieldError(loc=(k,), msg=v) for k, v in errors.items()]
    else:
        items = list(errors)

    return ValidationError.from_exception_data(
        title,
        [
            InitErrorDetails(
                # PydanticCustomError annotates these as LiteralString to
                # discourage user input as templates; ours come from
                # developer-authored call sites, so the cast is safe.
                type=PydanticCustomError(
                    cast(LiteralString, e.type),
                    cast(LiteralString, e.msg),
                    dict(e.params),
                ),
                loc=e.loc,
                input=None,
            )
            for e in items
        ],
    )
