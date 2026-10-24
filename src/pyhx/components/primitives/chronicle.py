"""Chronicle component — entries in time order, connected by a line.

Each entry has a date on the left, a marker (a dot, or an icon in a circle)
on a vertical line, and content on the right::

    c.chronicle[
        c.chronicle.entry(date="12.04.2026", color="#F194B4")[
            c.chronicle.title[
                y.a(href="/dokument/5")["Arbeitgeberfragebogen"],
                c.pill("Neu", appearance="success", variant="outline"),
            ],
            c.meta("Arbeitgeberfragebogen", "Muster Bau AG", "3 Seiten"),
            c.chronicle.text["Seit 01.04.2026 Einsatz zu 50%"],
        ],
        c.chronicle.entry(date="15.03.2026", icon="check-2", appearance="success")[
            c.chronicle.title["IV-Anmeldung validiert"],
        ],
    ]

A link in the title stretches across the whole entry (no JavaScript), like
``card.link`` in a card row. Inside a card, put the chronicle directly into
the card; it brings its own padding.
"""

import htpy as y

from pyhx.core.primitives import IconName, classnames

from ..variants import Appearance
from ._element import _HxElement, _KxSimpleElement, _KxSimpleElementFactory
from .icon import icon as render_icon


class _HxChronicleEntry(_HxElement):
    """One ``<li>`` of the chronicle; built via :meth:`_Chronicle.entry`."""

    def __init__(
        self,
        *,
        date: y.Node = None,
        icon: IconName | None = None,
        appearance: Appearance = "neutral",
        color: str | None = None,
        **kwargs: y.Attribute,
    ) -> None:
        self._date = date
        self._icon = icon
        self._appearance = appearance
        self._color = color
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        if self._icon is None:
            marker: y.Node = y.span(
                class_=f"hx-chronicle__dot hx-chronicle__dot--{self._appearance}"
            )
        else:
            marker = render_icon(self._icon, circle=True, appearance=self._appearance)

        # A free colour overrides the appearance, for dots and circles alike
        # (see `.hx-chronicle__entry--colored` in chronicle.css).
        return y.li(
            style=f"--chronicle--color: {self._color}" if self._color else None,
            **classnames(
                {
                    "hx-chronicle__entry": True,
                    "hx-chronicle__entry--colored": self._color is not None,
                },
                **self._kwargs,
            ),
        )[
            y.span(class_="hx-chronicle__date")[self._date],
            y.span(class_="hx-chronicle__marker", aria_hidden="true")[marker],
            y.div(class_="hx-chronicle__content")[self._children],
        ]


class _Chronicle:
    """The chronicle component and its parts.

    Instantiated once below as the module-level :data:`chronicle`. Subscript
    it (``chronicle[...]``) with entries, or call it first for attributes of
    the ``<ol>`` (``chronicle(id="documents")[...]``).

    Parts:

    * ``entry(date=…, icon=…, appearance=…, color=…)`` — one entry. Without
      ``icon`` its marker is a dot; with ``icon`` it is the icon in a circle
      (as ``icon(..., circle=True)``). ``appearance`` colours the marker like
      a pill; ``color`` sets any CSS colour instead (e.g. per document type).
    * ``title`` — first line; holds the title and e.g. a pill. A link in it
      makes the whole entry clickable.
    * ``text`` — muted description below; use :func:`meta` for a line of
      metadata between title and text.
    """

    def __init__(self) -> None:
        self._list = _KxSimpleElementFactory("hx-chronicle", y.ol)
        self.title = _KxSimpleElementFactory("hx-chronicle__title")
        self.text = _KxSimpleElementFactory("hx-chronicle__text", y.p)

    def __call__(self, **kwargs: y.Attribute) -> _KxSimpleElement:
        return self._list(**kwargs)

    def __getitem__(self, children: y.Node | None = None) -> y.Node:
        return self._list[children]

    def entry(
        self,
        *,
        date: y.Node = None,
        icon: IconName | None = None,
        appearance: Appearance = "neutral",
        color: str | None = None,
        **kwargs: y.Attribute,
    ) -> _HxChronicleEntry:
        """Build an entry; supply its content with ``[...]``.

        Parameters
        ----------
        date : Node, optional
            Shown right-aligned in the date column.
        icon : IconName, optional
            Show this icon in a circle instead of the dot.
        appearance : Appearance, default "neutral"
            Colour of the marker, as for pills.
        color : str, optional
            Any CSS colour for the marker; overrides ``appearance``.
        **kwargs
            Extra attributes for the ``<li>``.
        """
        return _HxChronicleEntry(
            date=date, icon=icon, appearance=appearance, color=color, **kwargs
        )


chronicle = _Chronicle()
"""The chronicle component singleton; see :class:`_Chronicle`."""
