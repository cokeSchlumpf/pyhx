"""The ``bubble`` primitive: a full-width rounded container with a tinted surface.

The module exposes a single public entry point — the :data:`bubble` factory. Call
or subscript it to build a bubble (``bubble(...)`` / ``bubble[...]``) and fill it
with child components (``bubble(appearance="success")[content]``).

A bubble is a block-level container that spans the full width of its parent, with
rounded corners (``--hx-radius-lg``) and a tinted surface. Its colour comes from an
``appearance`` variant (the same semantic palette as :data:`pill`). For one-off
colours, ``color`` overrides the background and ``text_color`` overrides the text —
both bypass the appearance palette without needing a new variant.
"""

from typing import Literal

import htpy as y

from ...core.primitives import classnames as cx
from ...core.primitives import merge_styles
from ..variants import Appearance
from ._element import _HxElement

BubbleSize = Literal["sm", "md"]
"""Physical size of a bubble. ``md`` is the standard size; ``sm`` shrinks the
padding and font-size for a more compact container."""


BubbleVariant = Literal["outline", "solid"]
"""Emphasis level. ``outline`` (default) is the tinted, bordered surface;
``solid`` fills the bubble with the appearance colour, matching solid buttons."""


class _KxBubble(_HxElement):
    """A ``<div class="hx-bubble">`` container with a tinted, rounded surface.

    Built via the :data:`bubble` factory — ``bubble(...)`` sets options and
    ``bubble[...]`` supplies the children. The ``appearance`` variant drives the
    surface tint and text colour via ``--hx-bubble--color``; ``color`` and
    ``text_color`` override the resolved background and text respectively.
    """

    def __init__(
        self,
        *,
        appearance: Appearance = "info",
        size: BubbleSize = "md",
        variant: BubbleVariant = "outline",
        color: str | None = None,
        text_color: str | None = None,
        children: y.Node | None = None,
        **kwargs: y.Attribute,
    ) -> None:
        """Configure the bubble.

        Args:
            appearance: Semantic colour variant (``neutral``, ``info``,
                ``success``, ``warning``, ``danger``, ``primary``). Selects the
                ``hx-bubble--{appearance}`` modifier that sets the surface tint
                and text colour. Defaults to ``"info"``.
            size: Physical size — ``"md"`` (standard) or ``"sm"`` (smaller
                padding and font-size). Selects the ``hx-bubble--{size}``
                modifier. Defaults to ``"md"``.
            variant: Emphasis — ``"outline"`` (default, tinted surface) or
                ``"solid"`` (filled with the appearance colour, matching
                solid buttons). Selects the ``hx-bubble--{variant}`` modifier.
            color: Optional background-colour override. Any CSS colour value
                (``"#e0f2fe"``, ``"var(--hx-color-info-050)"``, …). When set it
                replaces the appearance tint entirely.
            text_color: Optional text-colour override. Any CSS colour value.
                When set it replaces the appearance text colour.
            children: The bubble's content.
            **kwargs: Extra HTML attributes forwarded to the ``<div>``.
        """
        self._appearance = appearance
        self._size = size
        self._variant = variant
        self._color = color
        self._text_color = text_color
        self._children = children
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        overrides: dict[str, str] = {}
        if self._color is not None:
            overrides["--hx-bubble--bg"] = self._color
        if self._text_color is not None:
            overrides["--hx-bubble--text"] = self._text_color

        kwargs = self._kwargs
        if overrides:
            kwargs = merge_styles(overrides, **kwargs)

        return y.div(
            **cx(
                [
                    "hx-bubble",
                    f"hx-bubble--{self._appearance}",
                    f"hx-bubble--{self._size}",
                    f"hx-bubble--{self._variant}",
                ],
                **kwargs,
            )
        )[self._children]


class _KxBubbleFactory:
    """Public entry point for the bubble primitive (the :data:`bubble` singleton).

    Call or subscript it to build a bubble:

    * ``bubble(appearance="success")[content]`` — a success-tinted bubble.
    * ``bubble(color="#fff7ed", text_color="#9a3412")[content]`` — custom colours.
    * ``bubble[content]`` — a default (``info``) bubble.
    """

    def __call__(
        self,
        *,
        appearance: Appearance = "info",
        size: BubbleSize = "md",
        variant: BubbleVariant = "outline",
        color: str | None = None,
        text_color: str | None = None,
        **kwargs: y.Attribute,
    ) -> _KxBubble:
        """Build a :class:`_KxBubble`. See :meth:`_KxBubble.__init__` for the args."""
        return _KxBubble(
            appearance=appearance,
            size=size,
            variant=variant,
            color=color,
            text_color=text_color,
            children=None,
            **kwargs,
        )

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        """``bubble[children]`` — build a default bubble and fill it."""
        return self()[children]


#: The bubble primitive. Import as ``from pyhx.components import bubble`` (or via
#: ``c.bubble``) and use ``bubble(...)`` / ``bubble[...]``.
bubble = _KxBubbleFactory()
