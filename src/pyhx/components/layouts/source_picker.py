"""Source picker: choose a page of a set of documents, and optionally an area on it.

A form control built from the parts of :data:`~pyhx.components.document_viewer`::

    vm = c.document_viewer.view_model

    c.dialog_content(
        c.source_picker(id="source", documents=documents, name="source"),
        title="Add source",
        actions=c.button("Add", appearance="primary", hx_post="/sources"),
    )

It shows one page at a time; thumbnails and the pager choose the page. A
pointer drag on the page draws one box (the area), which can be moved and
resized by its corners and removed with Escape or "Clear area"; without a box
the whole page is the choice. The choice is posted in the hidden inputs
``<name>_document``, ``<name>_page`` and ``<name>_box`` (``"x,y,width,height"``
as fractions of the page, empty for the whole page) and read back with
:meth:`~pyhx.components.view_model.document_viewer.SourceChoice.from_form`.
Every change dispatches ``hx-source-picker:change`` on the picker
(``detail.picker``, ``detail.document``, ``detail.page``, ``detail.box``).

With many documents, ``files`` shows one document at a time with the
document switcher of ``document_viewer.files``; its entries are fetched with
htmx and replace the picker.

The browser part is the section "source picker" of ``pyhx.document-viewer.js``.
"""

from collections.abc import Sequence

import htpy as y

from pyhx.core.primitives import classnames
from pyhx.i18n import _

from ..primitives.button import button
from ..view_model.document_viewer import Document, DocumentLink, SourceChoice
from .document_viewer import _Root, _tool, document_viewer


def _resolve(
    documents: Sequence[Document], value: SourceChoice | None
) -> tuple[Document, int, SourceChoice | None]:
    """The document and page the picker opens at, and the value if it is among ``documents``."""
    if value is not None:
        for document in documents:
            if document.id == value.document_id and value.page <= len(document.pages):
                return document, value.page, value
    return documents[0], 1, None


def source_picker(
    *,
    id: str,
    documents: Sequence[Document],
    name: str = "source",
    value: SourceChoice | None = None,
    files: Sequence[DocumentLink] | None = None,
    **kwargs: y.Attribute,
) -> y.Node:
    """A form control to choose a page of ``documents`` and optionally an area on it.

    Parameters
    ----------
    id : str
        DOM id of the picker (its document viewer).
    documents : Sequence of Document
        The documents to choose from, as for ``c.document_viewer``; marks and
        notes on their pages are shown read-only.
    name : str
        Prefix of the hidden inputs ``<name>_document``, ``<name>_page`` and
        ``<name>_box``.
    value : SourceChoice, optional
        The choice it opens with, e.g. a source being edited; without it, or
        when its page isn't among ``documents``, the first page, whole.
    files : Sequence of DocumentLink, optional
        For many documents: the toolbar shows the document switcher of
        ``document_viewer.files`` instead of the title, and ``documents``
        holds only the current one. Choosing an entry (or previous/next)
        doesn't leave the page: its ``href`` is fetched with htmx and must
        return the picker for that document, which replaces this one (also
        inside a dialog). With fewer than two entries the toolbar shows the
        title, as without ``files``.
    **kwargs
        Further attributes of the picker's root element.

    Returns
    -------
    Node
        The picker.

    Raises
    ------
    ValueError
        If ``documents`` is empty.
    """
    if not documents:
        raise ValueError("a source picker needs at least one document")
    document, page, value = _resolve(documents, value)
    has_box = value is not None and value.box is not None
    dv = document_viewer
    root = _Root(
        id,
        documents,
        classnames("hx-source-picker", data_hx_source_picker=name, **kwargs),
        start=f"{document.id}:{page}",
        paged=True,
    )
    return root[
        dv.toolbar[
            # a single document looks as without a switcher
            dv.files(files) if files is not None and len(files) > 1 else dv.title(),
            dv.pager(),
            dv.zoom(),
            _tool("maximize-2", _("Fit page"), "fit"),
        ],
        dv.thumbnails(),
        dv.pages(),
        y.div(
            class_="hx-source-picker__footer",
            data_text_whole=_(
                "{document}, page {page}: whole page",
                document="{document}",
                page="{page}",
            ),
            data_text_area=_(
                "{document}, page {page}: marked area",
                document="{document}",
                page="{page}",
            ),
            data_text_area_label=_("Marked area"),
            data_text_area_keys=_(
                "Arrow keys move the area, Shift and arrow keys resize it, Delete removes it."
            ),
        )[
            y.div(class_="hx-source-picker__status")[
                y.strong(aria_live="polite", data_hx_source_picker_status=True)[
                    _(
                        "{document}, page {page}: marked area",
                        document=document.title,
                        page=page,
                    )
                    if has_box
                    else _(
                        "{document}, page {page}: whole page",
                        document=document.title,
                        page=page,
                    )
                ],
                y.span(class_="hx-source-picker__hint", data_when="whole")[
                    _("Drag on the page to mark an area.")
                ],
                y.span(class_="hx-source-picker__hint", data_when="area")[
                    _("Drag the area or its corners to change it.")
                ],
            ],
            button(
                _("Clear area"),
                icon="x",
                variant="ghost",
                size="sm",
                type="button",
                disabled=not has_box,
                data_hx_source_picker_clear=True,
            ),
            y.input(type="hidden", name=f"{name}_document", value=document.id),
            y.input(type="hidden", name=f"{name}_page", value=str(page)),
            y.input(
                type="hidden",
                name=f"{name}_box",
                value=value.box_value if value is not None else "",
            ),
        ],
    ]
