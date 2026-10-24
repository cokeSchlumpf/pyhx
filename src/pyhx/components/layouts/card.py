"""Card component — a white box on the canvas, built by composition.

A card is a ``<section class="hx-card">`` whose parts are sub-components of
:data:`card`::

    c.card[
        c.card.header[
            c.card.title[y.h2["Zusammenfassung"]],
            c.card.subtle["Jeder Satz mit Quelle"],
            c.card.subtitle["Aktualisiert am 15.03.2026"],
            c.card.actions[c.button("Bearbeiten")],
        ],
        c.card.section[c.card.label["Ausgangslage"], y.p[...]],
        c.card.list[
            c.card.item[
                c.card.link(href="/dokument/1")["IV-Anmeldung"],
                c.card.subtle["Eingang 15.03.2026 · 12 Seiten"],
            ],
        ],
        c.card.footer[c.button("Übernehmen", appearance="primary")],
    ]

The CSS places the parts, so their order inside the header does not matter:
title and subtle text share the first line, actions sit on its right, the
subtitle always goes to a second line. Consecutive parts (header, sections,
lists, footer) are separated by a thin line.

Passing ``open`` makes the card collapsible: ``card(open=False)[...]`` wraps
the parts in a native ``<details>`` element and the header renders as its
``<summary>``, so the card expands and collapses without JavaScript.
"""

from collections.abc import Mapping

import htpy as y

from pyhx.core.primitives import Omit, classnames, omit

from ..primitives._element import (
    _HxElement,
    _KxSimpleElement,
    _KxSimpleElementFactory,
)
from ..primitives.icon import icon

# Whether the parts render inside a collapsible card or group. Every card
# and group provides its own value, so a fixed group in a collapsible card
# (and vice versa) is not affected.
_collapsible: y.Context[bool] = y.Context("hx-card-collapsible", default=False)


class _HxCard(_HxElement):
    """The ``<section class="hx-card">``; built via :data:`card`."""

    def __init__(self, *, open: bool | Omit = omit, **kwargs: y.Attribute) -> None:
        self._open = open
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        section = y.section(**classnames("hx-card", **self._kwargs))

        if isinstance(self._open, Omit):
            return section[_collapsible.provider(False, self._children)]

        return section[
            y.details(class_="hx-card__details", open=self._open)[
                _collapsible.provider(True, self._children)
            ]
        ]


class _HxCardGroup(_HxElement):
    """An unpadded block inside a card, e.g. a label above a list; a
    ``<details>`` when ``open`` is given."""

    def __init__(self, *, open: bool | Omit = omit, **kwargs: y.Attribute) -> None:
        self._open = open
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        attrs = classnames("hx-card__group", **self._kwargs)

        if isinstance(self._open, Omit):
            return y.div(**attrs)[_collapsible.provider(False, self._children)]

        return y.details(open=self._open, **attrs)[
            _collapsible.provider(True, self._children)
        ]


@_collapsible.consumer
def _header(
    collapsible: bool, children: y.Node, kwargs: dict[str, y.Attribute]
) -> y.Node:
    if not collapsible:
        return y.header(**classnames("hx-card__header", **kwargs))[children]

    return y.summary(**classnames("hx-card__header", **kwargs))[
        children,
        y.span(class_="hx-card__chevron", aria_hidden="true")[icon("chevron-down-2")],
    ]


class _HxCardHeader(_HxElement):
    """``<header>``, or the ``<summary>`` toggle in a collapsible card or
    group."""

    def __init__(self, **kwargs: y.Attribute) -> None:
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        return _header(self._children, self._kwargs)


class _HxCardGroupFactory:
    def __call__(
        self, *, open: bool | Omit = omit, **kwargs: y.Attribute
    ) -> _HxCardGroup:
        return _HxCardGroup(open=open, **kwargs)

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        return self()[children]


class _HxCardHeaderFactory:
    def __call__(self, **kwargs: y.Attribute) -> _HxCardHeader:
        return _HxCardHeader(**kwargs)

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        return self()[children]


class _HxCardButtonFactory(_KxSimpleElementFactory):
    """Like the base factory, but with a ``type="button"`` default, so the
    button doesn't submit a surrounding form."""

    def __call__(
        self, *args: Mapping[str, y.Attribute], **kwargs: y.Attribute
    ) -> _KxSimpleElement:
        return super().__call__(*args, **{"type": "button", **kwargs})


class _Card:
    """The card component and its parts.

    Instantiated once below as the module-level :data:`card`. Subscript it
    (``card[...]``) for a plain card, or call it first for options
    (``card(open=False, id="history")[...]``). Every part accepts extra
    attributes the same way: ``card.section(id="history")[...]``.

    Parts:

    * ``header`` — top row. Holds ``title``, ``subtle``, ``subtitle`` and
      ``actions``. In a collapsible card it is the toggle.
    * ``title`` — wraps the heading (pass e.g. ``y.h2[...]``).
    * ``subtle`` — muted text on the title line; wraps below when space
      runs out. In a list item it is the muted description line.
    * ``subtitle`` — muted second line below the title.
    * ``actions`` — buttons on the right of the title line.
    * ``section`` — padded body block.
    * ``group`` — unpadded block, e.g. a ``label`` above a ``list``, so the
      rows run edge to edge. ``group(open=False)[...]`` makes it collapsible
      like a card: its ``header`` becomes the toggle. A card can hold any
      number of (collapsible) groups.
    * ``label`` — small heading inside a section; wraps text or a heading
      (``card.label[y.h3["Ausgangslage"]]``).
    * ``list`` / ``item`` — rows separated by thin lines.
    * ``link`` / ``button`` — make a whole list item clickable: the element
      stretches an invisible overlay across the item (no JavaScript). Other
      links and buttons in the item stay clickable on their own.
    * ``footer`` — right-aligned buttons at the bottom.
    """

    def __init__(self) -> None:
        self.header = _HxCardHeaderFactory()
        self.title = _KxSimpleElementFactory("hx-card__title")
        self.subtle = _KxSimpleElementFactory("hx-card__subtle", y.span)
        self.subtitle = _KxSimpleElementFactory("hx-card__subtitle", y.p)
        self.actions = _KxSimpleElementFactory("hx-card__actions")
        self.section = _KxSimpleElementFactory("hx-card__section")
        self.group = _HxCardGroupFactory()
        self.label = _KxSimpleElementFactory("hx-card__label")
        self.list = _KxSimpleElementFactory("hx-card__list", y.ul)
        self.item = _KxSimpleElementFactory("hx-card__item", y.li)
        self.link = _KxSimpleElementFactory("hx-card__link", y.a)
        self.button = _HxCardButtonFactory("hx-card__button", y.button)
        self.footer = _KxSimpleElementFactory("hx-card__footer", y.footer)

    def __call__(self, *, open: bool | Omit = omit, **kwargs: y.Attribute) -> _HxCard:
        """Configure the card.

        Parameters
        ----------
        open : bool, optional
            Makes the card collapsible and sets its initial state: the parts
            are wrapped in a ``<details>`` element and the header becomes its
            ``<summary>`` toggle. Omitted (default), the card is not
            collapsible. A collapsible card must start with ``card.header``
            (``<details>`` needs its ``<summary>`` first) and should not put
            ``card.actions`` in it: the whole header is the toggle, so a
            button there would also expand and collapse the card.
        **kwargs
            Extra attributes for the ``<section>``.
        """
        return _HxCard(open=open, **kwargs)

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        return self()[children]


card = _Card()
"""The card component singleton; see :class:`_Card`."""
