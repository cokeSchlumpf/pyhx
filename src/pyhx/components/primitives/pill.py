from typing import Literal

import htpy as y

from pyhx.core.primitives import IconName, classnames

from ..variants import Appearance, Size
from .icon import icon as render_icon

PillVariant = Literal["solid", "outline"]
"""Emphasis of a pill: ``solid`` is the tint alone, ``outline`` adds a thin
edge in the appearance colour (e.g. for a status next to a heading). A subset
of :data:`~pyhx.components.variants.Variant`; ghost, link and glass have no
meaning for a pill."""


class _Pill:
    def __call__(
        self,
        label: y.Node,
        *,
        value: y.Node | None = None,
        button: y.Node | None = None,
        appearance: Appearance = "info",
        size: Size = "md",
        variant: PillVariant = "solid",
        **kwargs,
    ) -> y.Node:
        return y.span(
            role="pill",
            **classnames(
                [
                    "hx-pill",
                    f"hx-pill--{appearance}",
                    f"hx-pill--{size}",
                    f"hx-pill--{variant}",
                ],
                **kwargs,
            ),
        )[
            y.span(class_="hx-pill__label")[label],
            y.span(class_="hx-pill__value")[value] if value else None,
            y.span(class_="hx-pill__button")[button] if button else None,
        ]

    def button(
        self,
        *,
        aria_label: str,
        icon: IconName = "x",
        **kwargs,
    ) -> y.Node:
        return y.button(
            type="button",
            aria_label=aria_label,
            **classnames("hx-pill__close", **kwargs),
        )[render_icon(icon)]

    def container(self, *pills: y.Node, **kwargs) -> y.Node:
        return y.div(**classnames("hx-pill-container", **kwargs))[*pills]


pill = _Pill()
