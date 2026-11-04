"""View model of the document viewer (``c.document_viewer``).

The values an app builds to show documents in :data:`pyhx.components.document_viewer`:
:class:`Document` with its :class:`DocumentPage` s, a :class:`PageBadge` per
thumbnail, and the annotations of a page, :class:`Mark` (an area highlighted
like a text marker, styled by :class:`MarkStyle`) and :class:`Note` (a pin).
:class:`DocumentLink` is an entry of the document switcher (``dv.files``).
Positions are fractions (0–1) of the page, :class:`BoundingBox` and
:class:`Point`, with ``from_pixels`` for coordinates in pixels of the page
image.

The names are generic, so they live in this module instead of
``pyhx.components``; reach them as ``c.document_viewer.view_model`` or::

    from pyhx.components.view_model import document_viewer as vm

All values are immutable and validated on creation.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

import htpy as y

from ..variants import Appearance
from .color import Color

__all__ = [
    "A4_ASPECT_RATIO",
    "Annotation",
    "BoundingBox",
    "Document",
    "DocumentLink",
    "DocumentPage",
    "Mark",
    "MarkLook",
    "MarkStyle",
    "Note",
    "PageBadge",
    "Point",
    "css_color",
]

A4_ASPECT_RATIO = "210 / 297"
"""Aspect ratio assumed for a page without a size (A4 portrait)."""

MarkLook = Literal["fill", "outline", "fill-outline"]
"""How a mark is drawn: ``fill`` a transparent tint without border,
``outline`` a border without tint, ``fill-outline`` both."""


def _fraction(name: str, value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def css_color(color: Appearance | Color) -> str:
    """Return the CSS value of an appearance or a colour.

    Parameters
    ----------
    color : Appearance or Color
        An appearance (resolved to its ``600`` shade) or any colour.

    Returns
    -------
    str
        A CSS colour, e.g. ``"var(--hx-color-warning-600)"`` or ``"#6d28d9"``.
    """
    return color.value if isinstance(color, Color) else Color.appearance(color).value


@dataclass(frozen=True)
class Point:
    """A point on a page, as fractions of its width and height.

    Attributes
    ----------
    x, y : float
        From the left and from the top, 0–1 of the page's width and height.

    Raises
    ------
    ValueError
        If a value is outside 0–1.
    """

    x: float
    y: float

    def __post_init__(self) -> None:
        _fraction("x", self.x)
        _fraction("y", self.y)

    @classmethod
    def from_pixels(
        cls, *, x: float, y: float, page_width: float, page_height: float
    ) -> Point:
        """Build a point from pixels of the page image (e.g. OCR coordinates).

        Parameters
        ----------
        x, y : float
            The point in pixels of the page image.
        page_width, page_height : float
            The size of the page image in pixels.
        """
        return cls(x=x / page_width, y=y / page_height)


@dataclass(frozen=True)
class BoundingBox:
    """A box on a page, as fractions of its width and height, origin top left.

    Fractions keep the box in place at every zoom and image resolution.

    Attributes
    ----------
    x, y : float
        The top left corner, 0–1 of the page's width and height.
    width, height : float
        The size, 0–1 of the page's width and height.

    Raises
    ------
    ValueError
        If a value is outside 0–1 or the box reaches beyond the page.
    """

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        for name in ("x", "y", "width", "height"):
            _fraction(name, getattr(self, name))
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("the box must lie within the page")

    @classmethod
    def from_pixels(
        cls,
        *,
        x: float,
        y: float,
        width: float,
        height: float,
        page_width: float,
        page_height: float,
    ) -> BoundingBox:
        """Build a box from pixels of the page image (e.g. OCR coordinates).

        Parameters
        ----------
        x, y, width, height : float
            The box in pixels of the page image.
        page_width, page_height : float
            The size of the page image in pixels.
        """
        return cls(
            x=x / page_width,
            y=y / page_height,
            width=width / page_width,
            height=height / page_height,
        )


@dataclass(frozen=True)
class MarkStyle:
    """Colour and look of a mark; pyhx draws hover and selected for every style.

    Attributes
    ----------
    color : Appearance or Color
        An appearance (``"warning"`` for low confidence, ...) or any colour,
        e.g. one per category of the app.
    look : MarkLook
        ``fill`` (default), ``outline`` or ``fill-outline``.
    """

    color: Appearance | Color = "info"
    look: MarkLook = "fill"


@dataclass(frozen=True)
class Mark:
    """An area of a page highlighted like a text marker.

    Attributes
    ----------
    id : str
        Unique within the viewer; links the mark to the app's content
        (``data-hx-document-annotation="<viewer id>:<id>"``).
    box : BoundingBox
        Where the mark is on the page.
    label : str
        Accessible name and tooltip of the mark.
    style : MarkStyle
        Colour and look.
    attrs : Mapping, optional
        Further attributes of the mark's button, e.g. ``hx-get`` and
        ``hx-target``.
    """

    id: str
    box: BoundingBox
    label: str
    style: MarkStyle = MarkStyle()
    attrs: Mapping[str, y.Attribute] | None = None


@dataclass(frozen=True)
class Note:
    """A note at a point of a page, drawn as a pin.

    The viewer draws only the pin; the app shows the note's content beside the
    viewer, e.g. in the sidebar entry linked to the note.

    Attributes
    ----------
    id : str
        Unique within the viewer; links the pin to the app's content.
    at : Point
        Where the pin is on the page (its centre).
    label : str
        The pin's accessible name is "Note: <label>"; also its tooltip.
    color : Appearance or Color
        Colour of the pin (default ``"warning"``).
    attrs : Mapping, optional
        Further attributes of the pin's button, e.g. ``hx-get`` and
        ``hx-target``.
    """

    id: str
    at: Point
    label: str
    color: Appearance | Color = "warning"
    attrs: Mapping[str, y.Attribute] | None = None


type Annotation = Mark | Note
"""An annotation of a page: a :class:`Mark` or a :class:`Note`."""


@dataclass(frozen=True)
class PageBadge:
    """The badge of a page's thumbnail, chosen by the app.

    Attributes
    ----------
    text : str
        What the badge shows: a count, "!".
    label : str
        What it means, read with the thumbnail by screen readers
        ("2 values to check").
    appearance : Appearance
        Colour of the badge (default ``"neutral"``).
    """

    text: str
    label: str
    appearance: Appearance = "neutral"


@dataclass(frozen=True)
class DocumentPage:
    """One page of a document: an image and its annotations.

    Attributes
    ----------
    src : str
        URL of the page image; anything an ``<img>`` loads.
    width, height : int, optional
        Only the page's aspect ratio (pixels of the image, or any numbers in
        its proportions); it reserves the page's space before the image is
        loaded. Without both, the viewer assumes A4 portrait and takes the
        real ratio from the image once it has loaded. Annotations never depend
        on them.
    annotations : Sequence of Annotation
        Marks and notes of the page.
    badge : PageBadge, optional
        Badge of the page's thumbnail; none if not given.

    Raises
    ------
    ValueError
        If ``width`` or ``height`` is not positive.
    """

    src: str
    width: int | None = None
    height: int | None = None
    annotations: Sequence[Annotation] = ()
    badge: PageBadge | None = None

    def __post_init__(self) -> None:
        for name in ("width", "height"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive, got {value}")

    @property
    def size_known(self) -> bool:
        """Whether both ``width`` and ``height`` are given."""
        return self.width is not None and self.height is not None

    @property
    def aspect_ratio(self) -> str:
        """CSS aspect ratio of the page: from its size, else A4 portrait."""
        if self.width is not None and self.height is not None:
            return f"{self.width} / {self.height}"
        return A4_ASPECT_RATIO


@dataclass(frozen=True)
class Document:
    """A document of the viewer.

    Attributes
    ----------
    id : str
        Unique within the viewer; addresses its pages
        (``"<document id>:<page>"``).
    title : str
        Shown in the toolbar while the document is in view, above its pages
        and its thumbnails when the viewer has several documents.
    pages : Sequence of DocumentPage
        The pages, in order.
    subtitle : str, optional
        Shown below the title in the toolbar, e.g. the date received.
    """

    id: str
    title: str
    pages: Sequence[DocumentPage]
    subtitle: str | None = None


@dataclass(frozen=True)
class DocumentLink:
    """An entry of the document switcher (``document_viewer.files``): a document to switch to.

    Attributes
    ----------
    title : str
        The document's name, shown in the list and, for the current entry, on
        the switcher's button.
    href : str, optional
        Where choosing it leads, e.g. the viewer with that document. Without
        it the entry is shown greyed out and can't be chosen (e.g. its pages
        aren't ready).
    group : str, optional
        The group it is listed under, e.g. its folder; entries of a group
        follow each other in the order given.
    detail : str, optional
        Shown at the end of the entry, e.g. the number of pages.
    current : bool
        Whether it is the document the viewer shows.
    """

    title: str
    href: str | None = None
    group: str | None = None
    detail: str | None = None
    current: bool = False
