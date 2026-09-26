"""Page section component — a titled sub-section below a page header.

A block that sits in a page's main column *after* a :func:`page_header`. Its
header row mirrors the page header's look — a title on the left, optional
actions on the right, a thin bottom border — but with a slightly smaller title.

Designed to pair with :func:`page_header` and :class:`pyhx.page_templates.AppShell`:
the underlying CSS makes the section header sticky directly *below* the page
header (which is itself sticky below the app-shell header), and the section's
width tracks the width preset of the sibling page header it follows.
"""

from collections.abc import Mapping
from typing import Any

import htpy as y

from ..primitives._element import _HxElement


class _PageSection(_HxElement):
    def __init__(
        self,
        *,
        title: y.Node,
        actions: y.Node | None = None,
        content: y.Node | None = None,
        id: str | None = None,
        attrs: Mapping[str, Any] | None = None,
    ) -> None:
        """Render a titled section below a page header.

        Parameters
        ----------
        title : Node
            The section title — typically an ``y.h2[...]``.
        actions : Node, optional
            Section-level actions (buttons, status pills, …) rendered on the right
            edge of the header row. ``None`` (default) omits the actions area.
        content : Node, optional
            The section body, rendered below the (sticky) header row.
        id : str, optional
            An ``id`` for the outer ``.hx-page-section`` element. ``None`` (default)
            omits it, so existing callers render unchanged. Useful as a stable target
            for an htmx out-of-band swap of the whole section.
        attrs : Mapping, optional
            Extra attributes spread onto the outer ``.hx-page-section`` element —
            e.g. ``htmx(hx_swap_oob="outerHTML", as_dict=True)`` to make the section
            replace itself out-of-band. ``None`` (default) adds nothing.

        Examples
        --------
        >>> page_section(
        ...     title=y.h2["Members"],
        ...     actions=c.button("Add member"),
        ...     content=table,
        ... )
        """

        self._title = title
        self._actions = actions
        self._children = content
        self._id = id
        self._attrs = attrs

    def _render(self) -> y.Node:
        return y.div(
            class_="hx-page-section",
            id=self._id,
            **(dict(self._attrs) if self._attrs else {}),
        )[
            y.div(class_="hx-page-section__header")[
                y.div(class_="hx-page-section__title")[self._title],
                y.div(class_="hx-page-section__actions")[self._actions]
                if self._actions
                else None,
            ],
            y.div(class_="hx-page-section__content")[self._children],
        ]


page_section = _PageSection
