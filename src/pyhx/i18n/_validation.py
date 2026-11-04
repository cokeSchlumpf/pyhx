"""Pydantic's validation errors in the language of the request."""

from collections.abc import Callable, Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic_core import ErrorDetails

from ._format import format_date, format_datetime, format_number
from ._translate import _, _n


def _value(value: Any) -> str:
    """A limit of an error (``ctx``), formatted for the language of the request."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int | float | Decimal):
        return format_number(value)
    if isinstance(value, datetime):
        return format_datetime(value)
    if isinstance(value, date):
        return format_date(value)
    return str(value)


def _count(ctx: Mapping[str, Any], key: str) -> int:
    value = ctx.get(key, 0)
    return value if isinstance(value, int) else 0


def _invalid_value(_ctx: Mapping[str, Any]) -> str:
    return _("Enter a valid value.")


def _invalid_date(_ctx: Mapping[str, Any]) -> str:
    return _("Enter a valid date.")


def _invalid_datetime(_ctx: Mapping[str, Any]) -> str:
    return _("Enter a valid date and time.")


def _invalid_number(_ctx: Mapping[str, Any]) -> str:
    return _("Enter a number.")


def _invalid_whole_number(_ctx: Mapping[str, Any]) -> str:
    return _("Enter a whole number.")


def _invalid_url(_ctx: Mapping[str, Any]) -> str:
    return _("Enter a valid URL.")


def _choose_offered(_ctx: Mapping[str, Any]) -> str:
    return _("Choose one of the offered values.")


_MESSAGES: dict[str, Callable[[Mapping[str, Any]], str]] = {
    "missing": lambda ctx: _("This field is required."),
    "string_too_short": lambda ctx: (
        _("This field is required.")
        if _count(ctx, "min_length") == 1
        else _n(
            "Enter at least {n} character.",
            "Enter at least {n} characters.",
            _count(ctx, "min_length"),
            n=_value(_count(ctx, "min_length")),
        )
    ),
    "string_too_long": lambda ctx: _n(
        "Enter at most {n} character.",
        "Enter at most {n} characters.",
        _count(ctx, "max_length"),
        n=_value(_count(ctx, "max_length")),
    ),
    "string_pattern_mismatch": lambda ctx: _(
        "The value doesn't have the expected format."
    ),
    "too_short": lambda ctx: _n(
        "Choose at least {n} entry.",
        "Choose at least {n} entries.",
        _count(ctx, "min_length"),
        n=_value(_count(ctx, "min_length")),
    ),
    "too_long": lambda ctx: _n(
        "Choose at most {n} entry.",
        "Choose at most {n} entries.",
        _count(ctx, "max_length"),
        n=_value(_count(ctx, "max_length")),
    ),
    "int_parsing": _invalid_whole_number,
    "int_from_float": _invalid_whole_number,
    "int_type": _invalid_whole_number,
    "float_parsing": _invalid_number,
    "float_type": _invalid_number,
    "decimal_parsing": _invalid_number,
    "decimal_type": _invalid_number,
    "finite_number": _invalid_number,
    "greater_than": lambda ctx: _(
        "Enter a value greater than {limit}.", limit=_value(ctx.get("gt"))
    ),
    "greater_than_equal": lambda ctx: _(
        "Enter a value of at least {limit}.", limit=_value(ctx.get("ge"))
    ),
    "less_than": lambda ctx: _(
        "Enter a value less than {limit}.", limit=_value(ctx.get("lt"))
    ),
    "less_than_equal": lambda ctx: _(
        "Enter a value of at most {limit}.", limit=_value(ctx.get("le"))
    ),
    "multiple_of": lambda ctx: _(
        "Enter a multiple of {multiple}.", multiple=_value(ctx.get("multiple_of"))
    ),
    "decimal_max_digits": lambda ctx: _n(
        "Enter at most {n} digit.",
        "Enter at most {n} digits.",
        _count(ctx, "max_digits"),
        n=_value(_count(ctx, "max_digits")),
    ),
    "decimal_max_places": lambda ctx: _n(
        "Enter at most {n} decimal place.",
        "Enter at most {n} decimal places.",
        _count(ctx, "decimal_places"),
        n=_value(_count(ctx, "decimal_places")),
    ),
    "bool_parsing": lambda ctx: _("Choose yes or no."),
    "bool_type": lambda ctx: _("Choose yes or no."),
    "date_parsing": _invalid_date,
    "date_type": _invalid_date,
    "date_from_datetime_parsing": _invalid_date,
    "date_from_datetime_inexact": _invalid_date,
    "datetime_parsing": _invalid_datetime,
    "datetime_type": _invalid_datetime,
    "datetime_from_date_parsing": _invalid_datetime,
    "time_parsing": lambda ctx: _("Enter a valid time."),
    "time_type": lambda ctx: _("Enter a valid time."),
    "enum": _choose_offered,
    "literal_error": _choose_offered,
    "url_parsing": _invalid_url,
    "url_type": _invalid_url,
    "url_scheme": _invalid_url,
    "string_type": _invalid_value,
    "uuid_parsing": _invalid_value,
    "uuid_type": _invalid_value,
}


def validation_message(error: ErrorDetails) -> str:
    """The message of a Pydantic validation error in the language of the request.

    Errors that Pydantic produces itself (``missing``, ``string_too_short``,
    ``int_parsing``, …) are translated by their ``type``, with the limits of
    ``ctx`` formatted for the language. An error raised by a validator as
    ``ValueError`` or ``AssertionError`` gives its own message, without
    Pydantic's prefix ("Value error, "); any other error (an app's
    ``PydanticCustomError``, :func:`pyhx.core.primitives.field_error`) gives
    its message as it comes, so apps pass it translated.

    Parameters
    ----------
    error
        One entry of ``ValidationError.errors()``.

    Examples
    --------
    >>> from pydantic import BaseModel, Field, ValidationError
    >>> class Case(BaseModel):
    ...     number: str = Field(min_length=3)
    >>> try:
    ...     Case(number="A")
    ... except ValidationError as exc:
    ...     validation_message(exc.errors()[0])
    'Enter at least 3 characters.'
    """
    ctx: Mapping[str, Any] = error.get("ctx") or {}
    kind = error.get("type", "")
    if kind in ("value_error", "assertion_error") and "error" in ctx:
        return str(ctx["error"])
    if kind.endswith("_type") and kind in _MESSAGES and error.get("input") is None:
        # The forms read an empty field as ``None``: the value is missing.
        return _("This field is required.")
    message = _MESSAGES.get(kind)
    if message is None:
        return error.get("msg", "")
    return message(ctx)
