"""Breadcrumb trail showing where the current page sits in the hierarchy.

A standalone component, independent of :func:`page_header`: it renders the
trail only, so a page template or page can place it wherever its layout
needs it (e.g. directly on the canvas above the content cards in
:class:`~pyhx.page_templates.CanvasShell`).
"""

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames


@component
def breadcrumbs(*items: y.Node, **kwargs) -> y.Node:
    """Render a breadcrumb trail following the W3C breadcrumb pattern.

    The items are wrapped in a ``<nav aria-label="Breadcrumb">`` and an ordered
    list. The last item is the current page and is marked with
    ``aria-current="page"``. The visual separator between items is supplied by
    CSS, so screen readers do not announce it.

    Parameters
    ----------
    *items : Node
        Breadcrumb entries in order, from the topmost ancestor to the current
        page. Use anchors for navigable entries and plain text for the current
        page.

    Examples
    --------
    >>> breadcrumbs(
    ...     y.a(href="/")["Meine Dossiers"],
    ...     "IV-2026-0142",
    ... )
    """
    ancestors, current = items[:-1], items[-1:]

    return y.nav(aria_label="Breadcrumb", **classnames("hx-breadcrumbs", **kwargs))[
        y.ol[
            [y.li[item] for item in ancestors],
            [y.li(aria_current="page")[item] for item in current],
        ]
    ]
