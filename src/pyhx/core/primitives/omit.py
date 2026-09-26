"""Singleton sentinel for "parameter was not provided".

Allows functions to distinguish three input states:

- a concrete value was passed (e.g. a string),
- ``None`` was passed explicitly,
- no argument was passed at all — the framework should use its default.

Use the module-level ``omit`` instance, never ``Omit()`` directly. The class
is exposed only so it can appear in type annotations next to ``omit``.

Example
-------
    from pyhx.core.primitives import omit, Omit

    def render(title: str | None | Omit = omit) -> str:
        if title is omit:
            return _framework_default()
        if title is None:
            return ""
        return title

Identity comparison (``is omit``) is idiomatic; equality (``== omit``) also
works because the default ``__eq__`` is identity for this class.
"""

from typing import Final, Literal


class Omit:
    """Type of the ``omit`` sentinel.

    Calling ``Omit()`` always returns the same singleton instance, so
    ``Omit() is omit`` is true. Pickling round-trips correctly via
    ``__reduce__``.
    """

    _instance: "Omit | None" = None

    def __new__(cls) -> "Omit":  # noqa: PYI034 — singleton returns the cached Omit, not Self
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "omit"

    def __bool__(self) -> Literal[False]:
        return False

    def __reduce__(self) -> tuple[type["Omit"], tuple]:
        return (Omit, ())


omit: Final[Omit] = Omit()
