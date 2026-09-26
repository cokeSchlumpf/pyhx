"""Selectable options — shared view-model value types.

A choice presented to the user (``Option``) and the providers that supply a
set of them. Self-contained value types used across form controls (dropdown,
drawer-select, segment-control, …) and the data filters, so they live in the
neutral ``view_model`` package.
"""

from collections.abc import Awaitable, Callable, Sequence
from inspect import iscoroutinefunction
from typing import Any, get_args

from commons.string_operators import to_title_case
from pydantic import BaseModel, Field


class Option(BaseModel):
    label: str
    value: str

    @staticmethod
    def of(label: str, value: str | None = None) -> "Option":
        if value is None:
            value = label

        return Option(label=label, value=value)

    @staticmethod
    def from_literal(literal: Any) -> list["Option"]:
        values = get_args(literal)
        return [Option.of(to_title_case(o), o) for o in values]


class Options(BaseModel):
    options: list[Option] = Field(default_factory=list)


type OptionsProvider = (
    Sequence[Option]
    | Callable[[], Sequence[Option]]
    | Callable[[], Awaitable[Sequence[Option]]]
)
"""Options source: an eager sequence or a sync/async no-arg producer.

Used by form-field controls and choice-filter markers that want to defer
option computation until render time. :func:`resolve_options` awaits the
provider (or returns the sequence as-is) and normalizes the result to a
``tuple[Option, ...]``.
"""


async def resolve_options(provider: OptionsProvider) -> tuple[Option, ...]:
    """Materialize an :data:`OptionsProvider` into a concrete tuple.

    Sequences are passed through verbatim (coerced to ``tuple``). Sync
    callables are invoked and their result tupled; async callables are
    awaited first. Resolution happens once per render — the caller is
    expected to cache the result for the duration of a single response.
    """
    if callable(provider):
        if iscoroutinefunction(provider):
            return tuple(await provider())
        result = provider()
        if isinstance(result, Awaitable):
            return tuple(await result)
        return tuple(result)
    return tuple(provider)
