"""Icons: Feather icons and PyHX's own SVG icons behind one function.

Feather icons render as ``<i data-feather="…">``, which ``feather.replace()``
swaps for an SVG in the browser (as before). Own icons are SVG files in
``static/icons``; they are read once at import and inlined on the server,
so they need no JavaScript and survive htmx swaps. Both get ``width`` and
``height`` of 24 like Feather's SVGs, so CSS that sizes icons in a context
(``.hx-button svg``, …) treats them the same.
"""

import re
from pathlib import Path
from typing import get_args

import htpy as y
from markupsafe import Markup

from pyhx.core.primitives import classnames
from pyhx.core.primitives.icon_name import CustomIconName, IconName

from ..variants import Appearance

ICONS_DIR = Path(__file__).resolve().parents[2] / "static" / "icons"

_SVG = re.compile(r"<svg\b([^>]*)>(.*)</svg>", re.DOTALL)
_ATTRIBUTE = re.compile(r'([\w:-]+)="([^"]*)"')


def _load_custom_icons() -> dict[str, tuple[dict[str, str], Markup]]:
    """Root attributes and inner markup of every own icon, by name."""
    icons: dict[str, tuple[dict[str, str], Markup]] = {}
    for name in get_args(CustomIconName):
        match = _SVG.search((ICONS_DIR / f"{name}.svg").read_text())
        if match is None:
            raise ValueError(f"static/icons/{name}.svg contains no <svg> element")
        attributes = dict(_ATTRIBUTE.findall(match.group(1)))
        attributes.pop("xmlns", None)  # implied for inline SVG in HTML
        icons[name] = (attributes, Markup(match.group(2).strip()))
    return icons


_CUSTOM_ICONS = _load_custom_icons()


def icon(
    icon_name: IconName,
    *,
    circle: bool = False,
    appearance: Appearance = "neutral",
    **kwargs: y.Attribute,
) -> y.Node:
    """Render an icon by name: a Feather icon or one of PyHX's own.

    Parameters
    ----------
    icon_name : IconName
        A Feather icon name (``"check"``) or an own icon (``"check-2"``,
        ``"swap"``, …, see :data:`~pyhx.core.primitives.CustomIconName`).
    circle : bool, default False
        Put the icon in a round, tinted badge (e.g. in front of a list row).
    appearance : Appearance, default "neutral"
        Colour of the badge: tint and icon from the appearance colour, as
        for pills. Only used with ``circle=True``.
    **kwargs
        Extra attributes for the icon element.

    Examples
    --------
    >>> icon("check")
    >>> icon("swap", circle=True, appearance="danger")
    """
    node = _icon(icon_name, **kwargs)
    if not circle:
        return node

    return y.span(
        class_=f"hx-icon-circle hx-icon-circle--{appearance}", aria_hidden="true"
    )[node]


def _icon(icon_name: IconName, **kwargs: y.Attribute) -> y.Node:
    custom = _CUSTOM_ICONS.get(icon_name)
    if custom is None:
        return y.i(data_feather=icon_name, **kwargs)

    attributes, inner = custom
    return y.svg(
        attributes,
        width="24",
        height="24",
        aria_hidden="true",
        focusable="false",
        **classnames(["hx-icon", f"hx-icon-{icon_name}"], **kwargs),
    )[inner]
