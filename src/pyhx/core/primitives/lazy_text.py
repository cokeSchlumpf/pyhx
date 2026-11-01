"""A text translated each time it is shown (the result of ``pyhx.i18n._l``)."""

from typing import Any

from markupsafe import Markup, escape


class LazyText:
    """A marked text that is translated into the language of the request when used.

    For texts defined at import time (page titles, navigation labels, module
    constants, class defaults), when no request language is known yet.
    ``str()``, f-strings and ``format()`` translate it; as a child of an
    htpy element it renders as escaped text. HTML attributes need a ``str``:
    pass ``str(text)`` or use ``_()`` while rendering.

    Parameters
    ----------
    message
        The English source text.
    **values
        Values of its named placeholders.
    """

    __slots__ = ("message", "values")

    def __init__(self, message: str, /, **values: Any) -> None:
        self.message = message
        self.values = values

    def __str__(self) -> str:
        from pyhx.i18n._translate import _

        return _(self.message, **self.values)

    def __html__(self) -> Markup:
        return escape(str(self))

    def __format__(self, format_spec: str) -> str:
        return format(str(self), format_spec)

    def __add__(self, other: object) -> str:
        return str(self) + str(other)

    def __radd__(self, other: object) -> str:
        return str(other) + str(self)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, LazyText):
            return (self.message, self.values) == (other.message, other.values)
        return str(self) == other

    def __hash__(self) -> int:
        return hash(self.message)

    def __repr__(self) -> str:
        return f"LazyText({self.message!r})"


type Text = str | LazyText
"""A text: a ``str``, or a :class:`LazyText` translated when it is shown."""
