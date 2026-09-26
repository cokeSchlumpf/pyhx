from collections.abc import Mapping
from typing import Literal

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import IconName, classnames

from ..variants import Appearance, Size, Variant


@component
def button(
    label: y.Node | None = None,
    *attrs: Mapping[str, y.Attribute],
    appearance: Appearance = "neutral",
    variant: Variant = "solid",
    size: Size = "md",
    icon: IconName | None = None,
    icon_position: Literal["left", "right"] = "left",
    href: str | None = None,
    disabled: bool = False,
    **kwargs,
) -> y.Node:
    """A button styled by appearance, variant, and size, with optional icon.

    When ``icon`` is supplied without a ``label``, the button renders as a
    square icon-only button — remember to pass ``aria_label=...`` in that
    case so the action is still announced to assistive technologies.

    When ``href`` is supplied, the element renders as ``<a href=...>``
    instead of ``<button>`` — useful for navigation that should look like
    a button. The ``hx-button*`` classes are class-based, so the same
    appearance / variant / size rules apply on either tag. For new-tab
    navigation pass ``target="_blank"`` and ``rel="noopener noreferrer"``
    yourself; the helper doesn't infer them. ``role`` is left unset so
    screen readers announce the element as a link (semantically correct
    when it actually navigates).

    Examples
    --------
    >>> button("Save")                                                # solid neutral
    >>> button("Save", appearance="primary")                          # solid primary CTA
    >>> button("Save", icon="save")                                   # icon left + label
    >>> button("Next", icon="arrow-right", icon_position="right")     # label + icon right
    >>> button(icon="x", aria_label="Close", variant="ghost")         # icon-only close
    >>> button("Save", size="lg", appearance="primary")               # large CTA
    >>> button("Docs", href="/docs")                                  # in-app navigation
    >>> button("GitHub", href="https://github.com/…",
    ...        target="_blank", rel="noopener noreferrer")            # new tab
    >>> button("Save", disabled=True)                                 # disabled button
    >>> button("Docs", href="/docs", disabled=True)                   # disabled link

    ``disabled=True`` renders as the native ``<button disabled>`` when no
    ``href`` is set. The anchor variant has no native disabled state, so
    it ships ``aria-disabled="true"`` plus ``tabindex="-1"`` and drops
    the ``href`` — the styling rule in ``button.css`` keys off both
    selectors, so the disabled appearance is identical on either tag.
    """
    icon_node: y.Node = y.i(data_feather=icon) if icon is not None else None
    is_icon_only = icon is not None and label is None

    if is_icon_only:
        inner: y.Node = icon_node
    elif icon_node is None:
        inner = label
    elif icon_position == "right":
        inner = [label, icon_node]
    else:
        inner = [icon_node, label]

    classes = [
        "hx-button",
        f"hx-button--{variant}",
        f"hx-button--{appearance}",
        f"hx-button--{size}",
    ]
    if is_icon_only and variant != "link":
        classes.append("hx-button--icon-only")

    if href is not None:
        anchor_attrs: dict = {}
        if disabled:
            anchor_attrs["aria_disabled"] = "true"
            anchor_attrs["tabindex"] = "-1"
            anchor_attrs["role"] = "link"
        else:
            anchor_attrs["href"] = href
        return y.a(*attrs, **anchor_attrs, **classnames(classes, **kwargs))[inner]

    return y.button(*attrs, disabled=disabled, **classnames(classes, **kwargs))[inner]
