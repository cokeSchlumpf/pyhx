# Document Viewer

`c.document_viewer` shows the pages of one or more documents, with marks (areas highlighted like a text marker) and notes (pins) on them, next to the app's own content: the values read from a document, the notes of the case workers.

Every scenario below is a page of the sample, with its explanation, its code and the live viewer:

```bash
poetry run fastapi dev samples/document_viewer/main.py
```

## Composition

The viewer is composed like `c.card`: the root holds the documents, its parts read them, and the app places the parts it wants.

```python
import pyhx.components as c
from pyhx.components.view_model import document_viewer as vm

dv = c.document_viewer

dv(id="case", documents=[registration, medical_report])[
    dv.toolbar(),       # title, pager, zoom, fit to width
    dv.thumbnails(),    # a group per document
    dv.pages(),         # all pages, one below the other
    dv.sidebar[...],    # the app's content
]
```

The viewer lays the parts out itself: toolbar on top, thumbnails on the left, pages in the middle, sidebar on the right. It fills its container, so give that a height, or use `CanvasShell(mode="full")` with the viewer as the page's content: it then fills the window below the header and scrolls inside. On a scrolling page, put it in a box with a fixed height. Zoom, the current page and the selection live in the browser; the server only renders the documents.

## Documents and pages

The data types are in `pyhx.components.view_model.document_viewer` (also reachable as `c.document_viewer.view_model`); their names are generic, so they are not in `pyhx.components` itself.

```python
registration = vm.Document(
    id="anmeldung",
    title="IV-Anmeldung 001.001",
    subtitle="Received 21.06.2026",
    pages=[vm.DocumentPage(src=f"/pages/anmeldung/{n}.png") for n in range(1, 13)],
)
```

- A page is an image: any URL an `<img>` loads. The app renders the pages, e.g. from a PDF.
- `width` and `height` of a page are optional and only give its aspect ratio, which reserves the page's space before the image loads. Without both, the viewer assumes A4 portrait and takes the real ratio from the image once it has loaded. Give them when you know them, so pages that are not A4 don't shift while loading.
- Ids of documents and annotations are unique within a viewer.

## Toolbar

`dv.toolbar()` shows the standard controls. `dv.toolbar[...]` shows the controls you give it, in that order, mixed with any node of your own:

```python
dv.toolbar[
    dv.back(href="/cases/42", label="Case"),
    dv.title(),                  # follows the document in view; dv.title("Fixed") stays
    dv.pager(),                  # page / pages of the document in view
    dv.zoom(),                   # − 100 % +
    dv.fit(),                    # fit to width
    dv.spacer(),                 # pushes the rest to the end
    c.pill("2 to check", appearance="warning", variant="outline"),
]
```

For your own icon controls use `c.button(icon=..., variant="ghost", size="sm", aria_label=...)`, as the viewer does.

## Several documents and thumbnails

With several documents the page column shows them one after another, each starting with its title; previous and next run across documents, and the toolbar's title and counter follow the document in view. `dv.thumbnails()` has a group per document, with headings by default only for more than one document; `grouped=True` or `grouped=False` decides otherwise.

A thumbnail shows a badge only when the app gives the page one: `vm.PageBadge("2", "2 values to check", appearance="warning")`. The `label` is read with the thumbnail by screen readers.

## Marks

A mark highlights an area of a page like a text marker: the tint blends into the page, so the text below keeps its contrast.

```python
vm.Mark(
    id="beruf",
    label="Occupation",                                    # accessible name
    box=vm.BoundingBox(x=0.084, y=0.164, width=0.081, height=0.025),
    style=vm.MarkStyle(color=c.Color.hex("#6d28d9"), look="fill"),
)
```

- Boxes are fractions (0–1) of the page's width and height, origin top left, so they stay in place at every zoom and resolution. `vm.BoundingBox.from_pixels(x=, y=, width=, height=, page_width=, page_height=)` converts pixels of the page image, e.g. from OCR.
- The style is a colour (an `Appearance` such as `"warning"`, or any `c.Color`) and a look: `fill` (tint), `outline` (border) or `fill-outline` (both). Map your categories and your confidence to styles; pyhx draws hover and selected for every style.
- One annotation is selected at a time. While one is selected, the other marks recede, so the selected one stands out even among many of the same kind. Selecting it again, or Esc, clears the selection.

## Notes

A note is a pin at a point of a page: a dot with a lighter ring, the same size at any zoom.

```python
vm.Note(id="note-au", label="Start of incapacity", at=vm.Point(0.89, 0.17), color="danger")
```

The viewer draws only the pin; show the note's content beside the viewer, e.g. in the sidebar (see below). Its accessible name is "Note: <label>".

## Linking the content beside the viewer

Anything on the page can select an annotation, and knows when it is selected:

```python
y.button(
    type="button",
    aria_pressed="false",                            # the viewer keeps it up to date
    data_hx_document_annotation="case:note-au",      # <viewer id>:<annotation id>
)["Start of incapacity"]
```

- A click selects the annotation and scrolls it into view; hover and focus highlight it. This works for content swapped in by HTMX later.
- While the annotation is selected, every element linked to it has `aria-pressed="true"`, so CSS alone can show a note's text: `.entry[aria-pressed="true"] .text { display: block; }`.
- `attrs` adds your attributes to a mark's or a pin's button, e.g. `attrs={"hx-get": "/notes/au", "hx-target": "#note"}`.
- A click on a mark or a pin dispatches `hx-document:annotation-select` on the viewer, with `detail.viewer`, `detail.id` and `detail.kind` (`"mark"` or `"note"`).
- In your own JavaScript, `pyhx.documentViewer("case")` returns `activate(id)`, `clear()`, `goTo("anmeldung:9")`, `setZoom(1.5)` and `fit()`.

## Opening at a page

A link to a place in a document opens the viewer there, without a jump from page 1:

```python
dv(
    id="case",
    documents=[registration],
    start="anmeldung:9",   # "<document id>:<page>": pager, title and thumbnail of that page
    selected="beruf",      # an annotation: selected and scrolled into view; wins over start
)[...]
```

The server renders the pager, the title, the current thumbnail and the page's image (loaded at once) for the start page; on load the viewer shows it without smooth scrolling. An unknown `start` opens the first page, an unknown `selected` selects nothing. Both are optional.

## One document at a time: the document switcher

With many documents (a case with hundreds of files), show one at a time and let `dv.files` switch between them:

```python
dv.toolbar[
    dv.back(href="/cases/42", label="Case"),
    dv.files([
        vm.DocumentLink("MRI_LWS.pdf", href="/cases/42/documents?file=7", group="Radiology", detail="6 p.", current=True),
        vm.DocumentLink("Befund.pdf", group="Radiology", detail="Pages not ready"),   # no href: greyed out
        ...
    ]),
    dv.pager(), dv.zoom(), dv.fit(),
]
```

- The button shows the current entry's title and group; it opens a dropdown directly below it with a search field, the entries under their groups (in the order given, so sort them), each with its `detail`, the current one checked.
- Typing filters by title and group in the browser (case and accents ignored); ↑/↓ move through the entries, Enter opens one; a click outside or Esc closes the dropdown.
- Beside it, previous and next document (the neighbouring entries with a link) and the position ("4 of 37 documents").
- An entry without `href` is shown greyed out and can't be chosen. Choosing an entry follows its `href`: the app renders the viewer with that document.
- At phone width the dropdown spans the toolbar and its entries are 44 px high.

## Navigating annotations

An app that lists its annotations beside the viewer (findings, values read, remarks) gets these from the viewer; the sample page "Annotation list" shows them together.

### One annotation, several marks

A quote over two lines, or from one page to the next, is several boxes. Give its marks the same `annotation`: they are selected, highlighted on hover, linked and stepped through as one, and selecting it scrolls to its first mark.

```python
vm.Mark(id="r1-a", annotation="r1", label="Remark", box=line_1, category="remark")
vm.Mark(id="r1-b", annotation="r1", label="Remark", box=line_2, category="remark")

y.button(type="button", aria_pressed="false", data_hx_document_annotation="list:r1")["Remark"]
```

Without `annotation` a mark is an annotation of its own, named by its `id`. `data-hx-document-annotation`, `selected=`, `activate(id)` and `detail.id` of `hx-document:annotation-select` use the annotation's id.

### Previous and next

`dv.annotation_pager()` steps through the shown annotations in document order (document, page, then the top and left of the first mark), with the position "3 / 12" between the buttons; marks and notes count, the marks of one annotation once. Next without a selection starts at the first annotation, previous at the last; both wrap around. Put it in the toolbar or the sidebar; name your annotations with `previous_label` and `next_label`, e.g. "Next finding".

### Categories

Marks and notes take a `category` (no whitespace). The app's toggles show and hide a category in the browser, without a request:

```python
dv(id="list", documents=[document], hidden_categories=["check"])[  # hidden at first
    ...,
    dv.sidebar[
        y.button(type="button", aria_pressed="true", data_hx_document_category_toggle="list:remark")["Remarks"],
        y.section(data_hx_document_category="list:remark")[...],  # hidden with the category
        dv.annotation_pager(),
    ],
]
```

- A toggle has `aria-pressed="true"` while its category is shown; the viewer keeps it up to date.
- `data-hx-document-categories-show="<viewer>"` and `data-hx-document-categories-hide="<viewer>"` on a button show and hide all categories at once ("All", "None"); the viewer disables them while they would change nothing. In JavaScript: `showAll()`, `hideAll()`.
- Hidden marks and notes are not drawn and the pager skips them; elements with `data-hx-document-category="<viewer>:<category>"` (entries, headings) are hidden with them. Hiding the category of the selected annotation clears the selection.
- Every change dispatches `hx-document:categories` on the viewer, with `detail.viewer` and `detail.hidden`.
- `category_query="types"` keeps the shown categories in that URL parameter (comma separated, written with `history.replaceState` after every change); read it when the page loads and pass the others as `hidden_categories`, so a reload or a shared link shows the same.
- Content swapped in by HTMX later gets the current state.

### Linked entries in view

When an annotation is selected by a click on a mark, by the pager or on load (`selected=`), each linked element outside its scrolling container (e.g. the sidebar) is scrolled into view inside it; the page and the page column don't move. A click on the linked element itself doesn't scroll it.

In your own JavaScript, `pyhx.documentViewer("list")` also returns `next()`, `previous()` and `showCategory(category, shown)`.

## Sidebar and phone width

`dv.sidebar[...]` is a pane for your content beside the pages, scrolling on its own; set its width with the CSS custom property `--document-viewer--sidebar-width` (default 22rem). Below 40rem the thumbnails are hidden, the toolbar wraps, the pages start at fit to width and the sidebar moves below the pages. On touch devices two fingers zoom.

## Source picker: choosing a page and an area

`c.source_picker` is a form control built from the viewer's parts: the user chooses a page of a set of documents and may mark one area on it, e.g. the source of a statement they write. It takes the same `Document`s and fits in a dialog:

```python
from fastapi import Request

vm = c.document_viewer.view_model


@router.fragment.get("/sources/new")
async def add_source() -> y.Node:
    return c.dialog_content(
        c.source_picker(
            id="source-picker",
            documents=documents,  # vm.Document, as for the viewer
            name="source",  # inputs source_document, source_page, source_box
            value=None,  # or vm.SourceChoice("report", 2, vm.BoundingBox(...)) to edit one
        ),
        title="Add source",
        actions=[
            c.button("Cancel", hx_post=c.close_dialog.url()),
            c.button("Use source", appearance="primary", hx_post=use_source.url()),
        ],
    )


@router.fragment.post("/sources")
async def use_source(request: Request) -> y.Node:
    choice = vm.SourceChoice.from_form(await request.form(), name="source")
    # choice.document_id, choice.page (1-based), choice.box (BoundingBox, or None for the whole page)
    ...
```

- It shows one page at a time; the thumbnails (a strip at phone width) and previous/next choose the page, also by keyboard. Without `value` the first page is chosen; a `value` whose document or page isn't among `documents` falls back to it.
- A pointer drag on the page (mouse, touch, pen) draws one area; drag it to move it, drag a corner to resize it. On the focused area, arrow keys move it, Shift + arrow keys resize it, Delete removes it. Escape or "Clear area" removes it too; Escape in a dialog closes the dialog only when there is no area. Another page removes the area. Without an area the whole page is the choice.
- The hidden inputs `<name>_document`, `<name>_page` and `<name>_box` always hold the choice; `<name>_box` is `"x,y,width,height"` in fractions of the page (four decimals, origin top left), empty for the whole page. `SourceChoice.from_form` returns `None` without a document and raises `ValueError` for a malformed page or box; checking that the document and page exist is the app's job.
- Every change dispatches `hx-source-picker:change` on the picker, with `detail.picker`, `detail.document`, `detail.page` and `detail.box` (`{x, y, width, height}` or `null`), e.g. for `hx-trigger`. The viewer itself dispatches `hx-document:page` (`detail.viewer`, `detail.page` as `"<document id>:<page>"`) whenever its current page changes.
- Marks and notes of the pages are shown, but can't be selected. The page fits the picker when it opens and on "Fit page"; one finger on the page draws, so a page zoomed in beyond the picker scrolls with two fingers or its scroll bars.
- In a dialog, the dialog widens to 64rem for the picker; the picker is `min(36rem, 70dvh)` high. When the server sends the dialog again (e.g. with an error), the picker takes the choice of its inputs, so render it with the posted `value`.

### Many documents: the document switcher in the picker

With one or a few documents, pass them all in `documents`. With many, pass only the current one and give `files`, the entries of the document switcher of `dv.files` (`vm.DocumentLink`: title, href, group, detail, current). The toolbar then shows the switcher instead of the title: search, groups, previous and next document, the position.

```python
def picker(document_id: str, value: vm.SourceChoice | None = None) -> y.Node:
    document = documents[document_id]
    return c.source_picker(
        id="source-picker",
        documents=[document],  # only the current one
        files=[
            vm.DocumentLink(d.title, href=f"/sources/picker?document={d.id}", group=d.folder, current=d is document)
            for d in documents.values()
        ],
        value=value,
    )


@router.fragment.get("/sources/picker")
async def picker_for(document: str) -> y.Node:
    return picker(document)  # the picker alone, no dialog around it
```

Inside the picker, choosing an entry (or previous/next) doesn't leave the page: the script fetches its `href` with htmx and replaces the picker with the answer (`outerHTML` of the picker), so it works in a dialog. Return the picker for that document with the same `id` and `name`; its inputs then hold that document's choice (page 1, whole page, unless you give a `value`). With fewer than two entries in `files` the picker looks as without them: the title, no switcher.
