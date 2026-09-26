import htpy as y

from pyhx.core.primitives import IconName, classnames

from ..variants import Appearance


class _Pill:
    def __call__(
        self,
        label: y.Node,
        *,
        value: y.Node | None = None,
        button: y.Node | None = None,
        appearance: Appearance = "info",
        **kwargs,
    ) -> y.Node:
        return y.span(
            role="pill",
            **classnames(["hx-pill", f"hx-pill--{appearance}"], **kwargs),
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
        )[y.i(data_feather=icon)]

    def container(self, *pills: y.Node, **kwargs) -> y.Node:
        return y.div(**classnames("hx-pill-container", **kwargs))[*pills]


pill = _Pill()
