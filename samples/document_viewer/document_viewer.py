"""Draft of the document viewer components (T-010), for reviewing the API.

Kept in the sample until the spec and the plan of T-010 are accepted; then it
moves to ``pyhx.components`` as ``c.document_viewer`` and the data types
(``c.Document``, ``c.Mark``, ...), its CSS to ``static/css/pyhx/components``
and its script to ``static/js/pyhx.document-viewer.js``.

The viewer is composed like ``c.card``: the root holds the documents, its
parts read them::

    dv = document_viewer
    dv(id="doc", documents=[registration, medical_report])[
        dv.toolbar(),          # title, pager, zoom, fit to width
        dv.thumbnails(),       # one group per document
        dv.pages(),            # all pages, one below the other
        dv.sidebar[...],       # the app's content, linked by annotation ids
    ]

A page has two kinds of annotations: a :class:`Mark` highlights an area like
a text marker, a :class:`Note` is a pin whose content the app shows (e.g. in
the sidebar). Anything on the page selects an annotation with
``data-hx-document-annotation="<viewer id>:<annotation id>"`` and carries
``aria-pressed`` while it is selected; a click on a mark or a pin dispatches
``hx-document:annotation-select`` (``detail.viewer``, ``detail.id``,
``detail.kind``) on the viewer. In the browser,
``pyhx.documentViewer(id)`` offers ``activate(id)``, ``clear()``,
``goTo("<document id>:<page>")``, ``setZoom(z)`` and ``fit()``.
"""

from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import htpy as y

from pyhx.components import Color, button
from pyhx.components.primitives._element import _HxElement
from pyhx.components.variants import Appearance
from pyhx.core.primitives import IconName, classnames
from pyhx.i18n import _

# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------

A4_ASPECT_RATIO = "210 / 297"
"""Aspect ratio assumed for a page without a size (A4 portrait)."""

MarkLook = Literal["fill", "outline", "fill-outline"]
"""How a mark is drawn: transparent tint without border, border without tint, or both."""


def _fraction(name: str, value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def _css_color(color: Appearance | Color) -> str:
    return color.value if isinstance(color, Color) else Color.appearance(color).value


@dataclass(frozen=True)
class Point:
    """A point on a page, as fractions (0–1) of its width and height, origin top left."""

    x: float
    y: float

    def __post_init__(self) -> None:
        _fraction("x", self.x)
        _fraction("y", self.y)

    @classmethod
    def from_pixels(
        cls, *, x: float, y: float, page_width: float, page_height: float
    ) -> Point:
        """A point from pixels of the page image (e.g. OCR coordinates)."""
        return cls(x=x / page_width, y=y / page_height)


@dataclass(frozen=True)
class BoundingBox:
    """A box on a page, as fractions (0–1) of its width and height, origin top left.

    Stays in place at every zoom and image resolution.
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
        """A box from pixels of the page image (e.g. OCR coordinates)."""
        return cls(
            x=x / page_width,
            y=y / page_height,
            width=width / page_width,
            height=height / page_height,
        )


@dataclass(frozen=True)
class MarkStyle:
    """Colour and look of a mark; pyhx draws hover and selected for every style."""

    color: Appearance | Color = "info"
    look: MarkLook = "fill"


@dataclass(frozen=True)
class Mark:
    """An area of a page highlighted like a text marker.

    ``label`` is its accessible name; ``attrs`` are further attributes of its
    button (e.g. ``hx-get``).
    """

    id: str
    box: BoundingBox
    label: str
    style: MarkStyle = MarkStyle()
    attrs: Mapping[str, y.Attribute] | None = None


@dataclass(frozen=True)
class Note:
    """A note at a point of a page, drawn as a pin.

    The viewer draws only the pin; the app shows the note's content beside
    the viewer. ``label`` is the pin's accessible name ("Note: <label>");
    ``attrs`` are further attributes of its button (e.g. ``hx-get``).
    """

    id: str
    at: Point
    label: str
    color: Appearance | Color = "warning"
    attrs: Mapping[str, y.Attribute] | None = None


type Annotation = Mark | Note


@dataclass(frozen=True)
class PageBadge:
    """The badge of a page's thumbnail, chosen by the app.

    ``text`` is what it shows (a count, "!"), ``label`` what it means, read
    with the thumbnail by screen readers ("2 values to check").
    """

    text: str
    label: str
    appearance: Appearance = "neutral"


@dataclass(frozen=True)
class DocumentPage:
    """One page image.

    ``width`` and ``height`` (pixels of the image, or any numbers in its
    proportions) only give the page's aspect ratio, which reserves its space
    before the image is loaded. Without both, the viewer assumes A4 portrait
    and takes the real ratio from the image once it has loaded. Marks and
    notes never depend on them: they are fractions of the page.
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
        return self.width is not None and self.height is not None

    @property
    def aspect_ratio(self) -> str:
        """CSS aspect ratio of the page: from its size, else A4 portrait."""
        if self.width is not None and self.height is not None:
            return f"{self.width} / {self.height}"
        return A4_ASPECT_RATIO


@dataclass(frozen=True)
class Document:
    """A document of the viewer: its title and its pages."""

    id: str
    title: str
    pages: Sequence[DocumentPage]
    subtitle: str | None = None


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class _Viewer:
    id: str
    documents: tuple[Document, ...]


_viewer: y.Context[_Viewer | None] = y.Context("hx-document-viewer", default=None)


def _require(viewer: _Viewer | None, part: str) -> _Viewer:
    if viewer is None:
        raise RuntimeError(
            f"document_viewer.{part} must be used inside document_viewer(...)[...]"
        )
    return viewer


def _pct(value: float) -> str:
    return f"{value * 100:.4f}%"


def _tool(icon: IconName, label: str, action: str, *, disabled: bool = False) -> y.Node:
    """An icon control of the toolbar: the quiet (ghost) button of pyhx."""
    return button(
        icon=icon,
        variant="ghost",
        size="sm",
        aria_label=label,
        disabled=disabled,
        type="button",
        data_hx_document_action=action,
    )


class _Root(_HxElement):
    def __init__(
        self, id: str, documents: Sequence[Document], kwargs: dict[str, y.Attribute]
    ) -> None:
        if not documents:
            raise ValueError("a document viewer needs at least one document")
        self._state = _Viewer(id=id, documents=tuple(documents))
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        return y.div(
            id=self._state.id,
            data_hx_document_viewer=self._state.id,
            **classnames("hx-document-viewer", **self._kwargs),
        )[_viewer.provider(self._state, self._children)]


class _Toolbar(_HxElement):
    def __init__(self, kwargs: dict[str, y.Attribute]) -> None:
        self._kwargs = kwargs

    # ``toolbar()`` without children is rendered by htpy as a child of the
    # viewer: render it within the viewer's context, not through ``__html__``.
    def iter_chunks(
        self, context: Mapping[y.Context[Any], Any] | None = None
    ) -> Iterator[str]:
        yield from self._render().iter_chunks(context)

    async def aiter_chunks(
        self, context: Mapping[y.Context[Any], Any] | None = None
    ) -> AsyncIterator[str]:
        async for chunk in self._render().aiter_chunks(context):
            yield chunk

    def _render(self) -> y.Element:
        controls = self._children
        if controls is None:
            controls = [
                document_viewer.title(),
                document_viewer.pager(),
                document_viewer.zoom(),
                document_viewer.fit(),
            ]
        return y.div(
            role="toolbar",
            aria_label=_("Document"),
            **classnames("hx-document-viewer__toolbar", **self._kwargs),
        )[controls]


class _Sidebar(_HxElement):
    def __init__(self, kwargs: dict[str, y.Attribute]) -> None:
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        return y.aside(**classnames("hx-document-viewer__sidebar", **self._kwargs))[
            self._children
        ]


@_viewer.consumer
def _title(viewer: _Viewer | None, title: y.Node, subtitle: y.Node) -> y.Node:
    first = _require(viewer, "title()").documents[0]
    follows = title is None
    return y.div(class_="hx-document-viewer__title")[
        y.strong(data_hx_document_title=follows or None)[
            first.title if follows else title
        ],
        y.span(data_hx_document_subtitle=follows or None)[
            (first.subtitle or "") if follows else subtitle
        ],
    ]


@_viewer.consumer
def _pager(viewer: _Viewer | None) -> y.Node:
    documents = _require(viewer, "pager()").documents
    first = documents[0]
    single = len(documents) == 1 and len(first.pages) <= 1
    return y.div(class_="hx-document-viewer__group")[
        _tool("chevron-left", _("Previous page"), "prev", disabled=True),
        y.span(class_="hx-document-viewer__counter", aria_live="polite")[
            y.span(data_hx_document_current=True)["1"],
            " / ",
            y.span(data_hx_document_count=True)[str(len(first.pages))],
        ],
        _tool("chevron-right", _("Next page"), "next", disabled=single),
    ]


@_viewer.consumer
def _thumbnails(viewer: _Viewer | None, grouped: bool | None) -> y.Node:
    state = _require(viewer, "thumbnails()")
    headings = len(state.documents) > 1 if grouped is None else grouped
    return y.nav(class_="hx-document-viewer__thumbnails", aria_label=_("Pages"))[
        (_thumbnail_group(state, document, headings) for document in state.documents)
    ]


def _thumbnail_group(state: _Viewer, document: Document, heading: bool) -> y.Node:
    heading_id = f"{state.id}--{document.id}--thumbnails"
    first = state.documents[0]
    return y.div(
        class_="hx-document-viewer__thumbnail-group",
        role="group",
        aria_labelledby=heading_id if heading else None,
        aria_label=None if heading else document.title,
    )[
        y.div(class_="hx-document-viewer__thumbnail-heading", id=heading_id)[
            document.title
        ]
        if heading
        else None,
        (
            _thumbnail(document, n, page, current=document is first and n == 1)
            for n, page in enumerate(document.pages, start=1)
        ),
    ]


def _thumbnail(
    document: Document, number: int, page: DocumentPage, *, current: bool
) -> y.Node:
    badge = page.badge
    page_label = _("Page {page}", page=number)
    return y.button(
        type="button",
        class_="hx-document-viewer__thumbnail",
        aria_label=f"{page_label}, {badge.label}" if badge else page_label,
        aria_current="page" if current else None,
        data_hx_document_goto=f"{document.id}:{number}",
    )[
        y.span(class_="hx-document-viewer__thumbnail-image")[
            y.img(
                src=page.src,
                alt="",
                loading="lazy",
                width=str(page.width) if page.size_known else None,
                height=str(page.height) if page.size_known else None,
                style=f"aspect-ratio: {page.aspect_ratio};",
            ),
            y.span(
                class_="hx-document-viewer__badge",
                data_appearance=badge.appearance,
                aria_hidden="true",
            )[badge.text]
            if badge
            else None,
        ],
        y.span(class_="hx-document-viewer__thumbnail-number")[str(number)],
    ]


@_viewer.consumer
def _pages(viewer: _Viewer | None) -> y.Node:
    state = _require(viewer, "pages()")
    headings = len(state.documents) > 1
    return y.div(class_="hx-document-viewer__pages", tabindex="0")[
        (_document(state, document, headings) for document in state.documents)
    ]


def _document(state: _Viewer, document: Document, heading: bool) -> y.Node:
    first = state.documents[0]
    return y.section(
        class_="hx-document-viewer__document",
        aria_label=document.title,
        data_hx_document_id=document.id,
        data_title=document.title,
        data_subtitle=document.subtitle or "",
    )[
        y.h2(class_="hx-document-viewer__document-heading")[document.title]
        if heading
        else None,
        (
            _page(document, n, page, eager=document is first and n <= 2)
            for n, page in enumerate(document.pages, start=1)
        ),
    ]


def _page(
    document: Document, number: int, page: DocumentPage, *, eager: bool
) -> y.Node:
    return y.section(
        class_="hx-document-viewer__page",
        aria_label=_("Page {page}", page=number),
        data_hx_document_page=f"{document.id}:{number}",
        # without a size the ratio is assumed; the script corrects it on load
        data_hx_document_ratio=None if page.size_known else "assumed",
        style=f"aspect-ratio: {page.aspect_ratio};",
    )[
        y.img(
            src=page.src,
            alt="",
            loading=None if eager else "lazy",
            width=str(page.width) if page.size_known else None,
            height=str(page.height) if page.size_known else None,
        ),
        y.div(class_="hx-document-viewer__annotations")[
            # notes after marks, so a pin stays on top of a mark
            (_mark(a) for a in page.annotations if isinstance(a, Mark)),
            (_note(a) for a in page.annotations if isinstance(a, Note)),
        ],
    ]


def _mark(mark: Mark) -> y.Node:
    box = mark.box
    return y.button(
        dict(mark.attrs or {}),
        type="button",
        class_="hx-document-viewer__mark",
        aria_label=mark.label,
        aria_pressed="false",
        title=mark.label,
        data_hx_document_annotation_id=mark.id,
        data_kind="mark",
        data_look=mark.style.look,
        style=(
            f"left: {_pct(box.x)}; top: {_pct(box.y)}; "
            f"width: {_pct(box.width)}; height: {_pct(box.height)}; "
            f"--document-viewer--color: {_css_color(mark.style.color)};"
        ),
    )


def _note(note: Note) -> y.Node:
    return y.button(
        dict(note.attrs or {}),
        type="button",
        class_="hx-document-viewer__note",
        aria_label=_("Note: {label}", label=note.label),
        aria_pressed="false",
        title=note.label,
        data_hx_document_annotation_id=note.id,
        data_kind="note",
        style=(
            f"left: {_pct(note.at.x)}; top: {_pct(note.at.y)}; "
            f"--document-viewer--color: {_css_color(note.color)};"
        ),
    )


class _SidebarFactory:
    def __call__(self, **kwargs: y.Attribute) -> _Sidebar:
        return _Sidebar(kwargs)

    def __getitem__(self, children: y.Node) -> y.Node:
        return self()[children]


class _ToolbarFactory:
    def __call__(self, **kwargs: y.Attribute) -> _Toolbar:
        return _Toolbar(kwargs)

    def __getitem__(self, children: y.Node) -> y.Node:
        return self()[children]


class _DocumentViewer:
    """The document viewer: ``document_viewer(id=..., documents=[...])[parts]``.

    Parts (each reads the documents of the surrounding viewer):

    - ``toolbar`` – ``toolbar()`` renders the standard controls (title, pager,
      zoom, fit); ``toolbar[...]`` takes the controls to show, in that order,
      mixed with the app's own (any node, e.g. ``c.button(..., variant="ghost")``);
    - the controls ``back(href, label)``, ``title(title=None, subtitle=None)``
      (without a title it follows the document in view), ``pager()``,
      ``zoom()``, ``fit()`` and ``spacer()`` (pushes what follows to the end);
    - ``thumbnails(grouped=None)`` – one group per document, headings by
      default only with more than one document;
    - ``pages()`` – the pages of all documents in a scrolling column;
    - ``sidebar[...]`` – a pane for the app's content, beside the pages and
      below them at phone width.
    """

    toolbar = _ToolbarFactory()
    sidebar = _SidebarFactory()

    def __call__(
        self, *, id: str, documents: Sequence[Document], **kwargs: y.Attribute
    ) -> _Root:
        return _Root(id, documents, kwargs)

    def back(self, href: str, label: str) -> y.Node:
        return button(label, icon="chevron-left", href=href, variant="ghost", size="sm")

    def title(self, title: y.Node = None, subtitle: y.Node = None) -> y.Node:
        return _title(title, subtitle)

    def pager(self) -> y.Node:
        return _pager()

    def zoom(self) -> y.Node:
        return y.div(class_="hx-document-viewer__group")[
            _tool("minus", _("Zoom out"), "zoom-out"),
            y.span(
                class_="hx-document-viewer__zoom",
                aria_live="polite",
                data_hx_document_zoom=True,
            )["100 %"],
            _tool("plus", _("Zoom in"), "zoom-in"),
        ]

    def fit(self) -> y.Node:
        return _tool("maximize-2", _("Fit to width"), "fit")

    def spacer(self) -> y.Node:
        return y.span(class_="hx-document-viewer__spacer", aria_hidden="true")

    def thumbnails(self, *, grouped: bool | None = None) -> y.Node:
        return _thumbnails(grouped)

    def pages(self) -> y.Node:
        return _pages()


document_viewer = _DocumentViewer()
"""The document viewer component; see :class:`_DocumentViewer`."""
