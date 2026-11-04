"""Document viewer: pages of one or more documents with marks and notes.

Composed like :data:`~pyhx.components.card`: the root holds the documents,
its parts read them, and the app places the parts it wants::

    dv = c.document_viewer
    vm = c.document_viewer.view_model

    dv(id="case", documents=[registration, medical_report])[
        dv.toolbar(),                 # title, pager, zoom, fit to width
        dv.thumbnails(),              # a group per document, badges per page
        dv.pages(),                   # all pages in a scrolling column
        dv.sidebar[...],              # the app's content, linked to annotations
    ]

The documents are built from :mod:`pyhx.components.view_model.document_viewer`:
page images with optional sizes, marks (areas highlighted like a text marker)
and notes (pins whose content the app shows beside the viewer).

The browser part is ``pyhx.document-viewer.js``: zoom, the current page,
selection. Anything on the page selects an annotation with
``data-hx-document-annotation="<viewer id>:<annotation id>"`` and has
``aria-pressed="true"`` while it is selected; a click on a mark or a pin
dispatches ``hx-document:annotation-select`` (``detail.viewer``,
``detail.id``, ``detail.kind``) on the viewer; ``pyhx.documentViewer(id)``
returns ``activate(id)``, ``clear()``, ``goTo("<document id>:<page>")``,
``setZoom(zoom)``, ``fit()``, ``next()``, ``previous()`` and
``showCategory(category, shown)``.

Navigating annotations: marks with the same ``annotation`` are one annotation;
``annotation_pager()`` steps through the shown annotations in document order;
``category`` on marks and notes with ``hidden_categories`` on the root and
``data-hx-document-category-toggle="<viewer>:<category>"`` show and hide them
in the browser (``hx-document:categories``); a mark selected by a click, the
pager or on load scrolls its linked elements into view in their container.
"""

import unicodedata
from collections.abc import AsyncIterator, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import groupby
from typing import Any

import htpy as y

from pyhx.core.primitives import IconName, classnames
from pyhx.i18n import _, _n

from ..primitives._element import _HxElement
from ..primitives.button import button
from ..primitives.icon import icon
from ..view_model import document_viewer as view_model
from ..view_model.document_viewer import (
    Document,
    DocumentLink,
    DocumentPage,
    Mark,
    Note,
    css_color,
)


@dataclass(frozen=True)
class _Viewer:
    id: str
    documents: tuple[Document, ...]
    start: str | None = None
    selected: str | None = None
    # one page at a time, annotations read-only (the source picker); internal
    paged: bool = False
    hidden_categories: frozenset[str] = frozenset()

    def start_page(self) -> tuple[Document, int]:
        """The document and page (1-based) the viewer opens at: ``start``, else the first page."""
        if self.start:
            document_id, _sep, page = self.start.rpartition(":")
            for document in self.documents:
                if (
                    document.id == document_id
                    and page.isdigit()
                    and 1 <= int(page) <= len(document.pages)
                ):
                    return document, int(page)
        return self.documents[0], 1

    def start_index(self) -> int:
        """The position of the start page among the pages of all documents (0-based)."""
        start, number = self.start_page()
        index = 0
        for document in self.documents:
            if document is start:
                return index + number - 1
            index += len(document.pages)
        return 0

    def page_count(self) -> int:
        return sum(len(d.pages) for d in self.documents)

    def shown(self, annotation: Mark | Note) -> bool:
        return annotation.category not in self.hidden_categories

    def annotation_count(self) -> int:
        """The number of shown annotations (marks of one annotation count once)."""
        return len(
            {
                a.annotation_id
                for d in self.documents
                for page in d.pages
                for a in page.annotations
                if self.shown(a)
            }
        )


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
        self,
        id: str,
        documents: Sequence[Document],
        kwargs: dict[str, y.Attribute],
        *,
        start: str | None = None,
        selected: str | None = None,
        paged: bool = False,
        hidden_categories: Iterable[str] = (),
        category_query: str | None = None,
    ) -> None:
        if not documents:
            raise ValueError("a document viewer needs at least one document")
        hidden = frozenset(hidden_categories)
        for category in hidden:
            view_model._category(category)
        self._state = _Viewer(
            id=id,
            documents=tuple(documents),
            start=start,
            selected=selected,
            paged=paged,
            hidden_categories=hidden,
        )
        self._category_query = category_query
        self._kwargs = kwargs

    def _render(self) -> y.Node:
        return y.div(
            id=self._state.id,
            data_hx_document_viewer=self._state.id,
            data_hx_document_start=self._state.start or None,
            data_hx_document_selected=self._state.selected or None,
            data_hx_document_paged=self._state.paged or None,
            data_hx_document_hidden=" ".join(sorted(self._state.hidden_categories))
            or None,
            data_hx_document_category_query=self._category_query,
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
    first, _number = _require(viewer, "title()").start_page()
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
    state = _require(viewer, "pager()")
    document, number = state.start_page()
    index = state.start_index()
    return y.div(class_="hx-document-viewer__group")[
        _tool("chevron-left", _("Previous page"), "prev", disabled=index == 0),
        y.span(class_="hx-document-viewer__counter", aria_live="polite")[
            y.span(data_hx_document_current=True)[str(number)],
            " / ",
            y.span(data_hx_document_count=True)[str(len(document.pages))],
        ],
        _tool(
            "chevron-right",
            _("Next page"),
            "next",
            disabled=index >= state.page_count() - 1,
        ),
    ]


@_viewer.consumer
def _annotation_pager(
    viewer: _Viewer | None, previous_label: str | None, next_label: str | None
) -> y.Node:
    state = _require(viewer, "annotation_pager()")
    total = state.annotation_count()
    return y.div(
        class_="hx-document-viewer__group hx-document-viewer__annotation-pager"
    )[
        _tool(
            "chevron-left",
            previous_label or _("Previous annotation"),
            "annotation-prev",
            disabled=total == 0,
        ),
        y.span(
            class_="hx-document-viewer__counter",
            aria_live="polite",
            data_hx_document_annotation_position=True,
        )[f"– / {total}"],
        _tool(
            "chevron-right",
            next_label or _("Next annotation"),
            "annotation-next",
            disabled=total == 0,
        ),
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
    start, start_number = state.start_page()
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
            _thumbnail(
                document, n, page, current=document is start and n == start_number
            )
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
    start, start_number = state.start_page()
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
            _page(
                document,
                n,
                page,
                eager=document is start and start_number <= n <= start_number + 1,
                paged=state.paged,
                shown=document is start and n == start_number,
                hidden=state.hidden_categories,
            )
            for n, page in enumerate(document.pages, start=1)
        ),
    ]


def _page(
    document: Document,
    number: int,
    page: DocumentPage,
    *,
    eager: bool,
    paged: bool = False,
    shown: bool = True,
    hidden: frozenset[str] = frozenset(),
) -> y.Node:
    return y.section(
        class_="hx-document-viewer__page",
        aria_label=_("Page {page}", page=number),
        data_hx_document_page=f"{document.id}:{number}",
        # without a size the ratio is assumed; the script corrects it on load
        data_hx_document_ratio=None if page.size_known else "assumed",
        style=f"aspect-ratio: {page.aspect_ratio};",
        # paged: only the current page is shown
        hidden=paged and not shown,
    )[
        y.img(
            src=page.src,
            alt="",
            loading=None if eager else "lazy",
            width=str(page.width) if page.size_known else None,
            height=str(page.height) if page.size_known else None,
        ),
        # paged (source picker): annotations are shown, not selectable
        y.div(class_="hx-document-viewer__annotations", inert=paged)[
            # notes after marks, so a pin stays on top of a mark
            (_mark(a, hidden) for a in page.annotations if isinstance(a, Mark)),
            (_note(a, hidden) for a in page.annotations if isinstance(a, Note)),
        ],
    ]


def _mark(mark: Mark, hidden: frozenset[str] = frozenset()) -> y.Node:
    box = mark.box
    return y.button(
        dict(mark.attrs or {}),
        type="button",
        class_="hx-document-viewer__mark",
        aria_label=mark.label,
        aria_pressed="false",
        title=mark.label,
        data_hx_document_annotation_id=mark.annotation_id,
        data_hx_document_category=mark.category,
        hidden=mark.category in hidden,
        data_kind="mark",
        data_look=mark.style.look,
        style=(
            f"left: {_pct(box.x)}; top: {_pct(box.y)}; "
            f"width: {_pct(box.width)}; height: {_pct(box.height)}; "
            f"--document-viewer--color: {css_color(mark.style.color)};"
        ),
    )


def _note(note: Note, hidden: frozenset[str] = frozenset()) -> y.Node:
    return y.button(
        dict(note.attrs or {}),
        type="button",
        class_="hx-document-viewer__note",
        aria_label=_("Note: {label}", label=note.label),
        aria_pressed="false",
        title=note.label,
        data_hx_document_annotation_id=note.id,
        data_hx_document_category=note.category,
        hidden=note.category in hidden,
        data_kind="note",
        style=(
            f"left: {_pct(note.at.x)}; top: {_pct(note.at.y)}; "
            f"--document-viewer--color: {css_color(note.color)};"
        ),
    )


def _searchable(text: str) -> str:
    """``text`` as the switcher's filter compares it: lower case, without accents."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


@_viewer.consumer
def _files(viewer: _Viewer | None, entries: tuple[DocumentLink, ...]) -> y.Node:
    _require(viewer, "files()")
    current = next((i for i, e in enumerate(entries) if e.current), None)
    linked = [i for i, e in enumerate(entries) if e.href]
    before = [i for i in linked if current is not None and i < current]
    after = [i for i in linked if current is not None and i > current]
    previous = entries[before[-1]] if before else None
    following = entries[after[0]] if after else None
    shown = entries[current] if current is not None else None
    total = len(entries)
    return y.div(class_="hx-document-viewer__files")[
        y.details(class_="hx-document-viewer__files-menu")[
            y.summary(class_="hx-document-viewer__files-button")[
                y.span(class_="hx-document-viewer__files-current")[
                    y.strong[shown.title if shown else _("Documents")],
                    y.span[shown.group or ""] if shown else None,
                ],
                icon("chevron-down", aria_hidden="true"),
            ],
            y.div(class_="hx-document-viewer__files-panel")[
                y.label(class_="hx-document-viewer__files-search")[
                    _("Search"),
                    y.input(
                        type="search",
                        autocomplete="off",
                        data_hx_document_files_search=True,
                    ),
                ],
                y.div(class_="hx-document-viewer__files-list")[
                    (
                        _files_group(group, list(items))
                        for group, items in groupby(entries, key=lambda e: e.group)
                    )
                ],
                y.div(class_="hx-document-viewer__files-footer")[
                    y.span(
                        data_hx_document_files_matches=True,
                        # the script fills in {n} while filtering
                        data_template=_("{n} of {total} match", n="{n}", total=total),
                    )[_("{n} of {total} match", n=total, total=total)],
                    " · ",
                    _("↑↓ to move, Enter to open"),
                ],
            ],
        ],
        button(
            icon="arrow-up",
            href=previous.href if previous else None,
            disabled=previous is None,
            variant="ghost",
            size="sm",
            aria_label=_("Previous document"),
            title=previous.title if previous else None,
        ),
        button(
            icon="arrow-down",
            href=following.href if following else None,
            disabled=following is None,
            variant="ghost",
            size="sm",
            aria_label=_("Next document"),
            title=following.title if following else None,
        ),
        y.span(class_="hx-document-viewer__files-position")[
            _n(
                "{n} of {total} document",
                "{n} of {total} documents",
                total,
                n=(current or 0) + 1,
                total=total,
            )
        ]
        if shown
        else None,
    ]


def _files_group(group: str | None, entries: list[DocumentLink]) -> y.Node:
    return y.div(
        class_="hx-document-viewer__files-group", role="group", aria_label=group
    )[
        y.div(class_="hx-document-viewer__files-heading", aria_hidden="true")[group]
        if group
        else None,
        (_files_entry(entry) for entry in entries),
    ]


def _files_entry(entry: DocumentLink) -> y.Node:
    content = [
        y.span(class_="hx-document-viewer__files-check")[
            icon("check", aria_hidden="true") if entry.current else None
        ],
        y.span(class_="hx-document-viewer__files-name")[entry.title],
        y.span(class_="hx-document-viewer__files-detail")[entry.detail or ""],
    ]
    search = _searchable(f"{entry.title} {entry.group or ''}")
    if entry.href:
        return y.a(
            href=entry.href,
            class_="hx-document-viewer__files-entry",
            aria_current="true" if entry.current else None,
            data_hx_document_search=search,
        )[content]
    return y.span(
        class_="hx-document-viewer__files-entry",
        aria_disabled="true",
        data_hx_document_search=search,
    )[content]


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
    - ``annotation_pager(previous_label=None, next_label=None)`` – previous and
      next annotation with the position, in the toolbar or the sidebar;
    - ``thumbnails(grouped=None)`` – one group per document, headings by
      default only with more than one document;
    - ``files(entries)`` – a toolbar control to switch between documents shown
      one at a time: the current one on a button that opens a searchable list
      of :class:`~pyhx.components.view_model.document_viewer.DocumentLink`,
      grouped, with previous and next document beside it;
    - ``pages()`` – the pages of all documents in a scrolling column;
    - ``sidebar[...]`` – a pane for the app's content, beside the pages and
      below them at phone width.
    """

    toolbar = _ToolbarFactory()
    sidebar = _SidebarFactory()
    view_model = view_model
    """The data types: :mod:`pyhx.components.view_model.document_viewer`."""

    def __call__(
        self,
        *,
        id: str,
        documents: Sequence[Document],
        start: str | None = None,
        selected: str | None = None,
        hidden_categories: Iterable[str] = (),
        category_query: str | None = None,
        **kwargs: y.Attribute,
    ) -> _Root:
        """The viewer's root.

        ``start`` (``"<document id>:<page>"``) opens it at that page instead of
        the first one; ``selected`` (an annotation id) selects that annotation
        and scrolls it into view when the page loads, and wins over ``start``.
        ``hidden_categories`` hides the marks and notes of those categories
        until the user shows them (``data-hx-document-category-toggle``);
        ``category_query`` names a URL parameter in which the browser keeps
        the shown categories (comma separated) after the user changed them,
        for the app to read them as ``hidden_categories`` when the page loads.
        """
        return _Root(
            id,
            documents,
            kwargs,
            start=start,
            selected=selected,
            hidden_categories=hidden_categories,
            category_query=category_query,
        )

    def back(self, href: str, label: str) -> y.Node:
        return button(label, icon="chevron-left", href=href, variant="ghost", size="sm")

    def title(self, title: y.Node = None, subtitle: y.Node = None) -> y.Node:
        return _title(title, subtitle)

    def pager(self) -> y.Node:
        return _pager()

    def annotation_pager(
        self, *, previous_label: str | None = None, next_label: str | None = None
    ) -> y.Node:
        """Previous and next annotation with the position ("3 / 12").

        In document order, skipping hidden categories; marks of one annotation
        count once. The labels name the app's annotations, e.g. "Next finding".
        """
        return _annotation_pager(previous_label, next_label)

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

    def files(self, entries: Sequence[DocumentLink]) -> y.Node:
        return _files(tuple(entries))


document_viewer = _DocumentViewer()
"""The document viewer component singleton; see :class:`_DocumentViewer`."""
