# T-010 Document viewer with annotations: spec

The API is easiest to review by its use: `samples/document_viewer` shows each scenario with an explanation, its code and the live viewer (`poetry run fastapi dev samples/document_viewer/main.py`, overview at `/`). The draft component there (`samples/document_viewer/document_viewer.py`) implements this spec's API; the plan moves it into `pyhx.components`.

## Requirements

### Composition

- **R1** `pyhx.components` exports `document_viewer` (`c.document_viewer`), composed like `c.card`: `c.document_viewer(id=..., documents=[...])[parts]` renders the viewer's root; each part reads the documents of the surrounding viewer, and a part used outside a viewer raises an error naming the part.
- **R2** A viewer needs at least one document; the ids of documents and of annotations are unique within the viewer (they address pages and annotations in the browser).
- **R3** The parts are `toolbar`, `thumbnails(grouped=None)`, `pages()` and `sidebar`; an app places the ones it wants, and the viewer lays them out: toolbar on top, thumbnails left, pages in the middle, sidebar right.
- **R4** The viewer works inside `CanvasShell(mode="full")` (filling the window) and inside any container with a height (e.g. a fixed-height box on a scrolling page).

### Data

- **R5** The data types live in their own namespace, not in `pyhx.components` itself (their names are generic): `pyhx.components.view_model.document_viewer`, also reachable as `c.document_viewer.view_model`. They are `Document` (id, title, optional subtitle, pages), `DocumentPage` (image URL, optional width and height, annotations, optional badge), `PageBadge`, `Mark`, `MarkStyle`, `Note`, `BoundingBox` and `Point`; they are immutable and validated on creation.
- **R6** `BoundingBox` (`x`, `y`, `width`, `height`) and `Point` (`x`, `y`) are fractions 0–1 of the page's width and height, origin top left; values outside 0–1, or a box reaching beyond the page, are refused with a `ValueError`. `from_pixels(..., page_width=, page_height=)` builds them from pixels of the page image.
- **R7** A page image is any URL an `<img>` loads. A page's `width` and `height` are optional and give only its aspect ratio, which reserves the page's space before the image is loaded; they never affect marks and notes. Without both (none or only one given), the viewer assumes A4 portrait (210 : 297) and takes the real ratio from the image once it has loaded; a width or height that is not positive is refused with a `ValueError`.

### Toolbar

- **R8** `toolbar()` without children shows the standard controls: title, pager, zoom, fit to width.
- **R9** `toolbar[...]` shows the controls it is given, in that order; they are the viewer's controls `back(href, label)`, `title(title=None, subtitle=None)`, `pager()`, `zoom()`, `fit()` and `spacer()`, and any node of the app (e.g. `c.button(..., variant="ghost")`, `c.pill(...)`).
- **R10** `title()` without a title shows the title and subtitle of the document in view and follows the scroll; with a title it stays fixed.
- **R11** `pager()` shows "page / pages" of the document in view with previous and next; previous and next run across documents and are disabled at the first and the last page.
- **R12** `zoom()` zooms out and in by steps (50 % to 300 %) and shows the zoom; `fit()` fits the page width to the column. Zooming keeps the same place of the document in view.
- **R13** The viewer's buttons are pyhx's quiet (`ghost`) buttons with an accessible name; `back` is a link styled the same way.
- **R14** `spacer()` pushes the controls after it to the end of the toolbar.

### Pages and thumbnails

- **R15** `pages()` shows the pages of all documents one after another in a scrolling column, each document starting with its title when the viewer has more than one; page images load when they come near the view.
- **R16** The current page is the page under the middle of the column; it updates while the user scrolls. A scroll the viewer starts (thumbnail, previous/next, selecting an annotation) selects its target at once, without passing through the pages on the way.
- **R17** `thumbnails()` shows one thumbnail per page, a group per document; the group has a heading when `grouped=True`, or with `grouped=None` (default) when the viewer has more than one document. The current page's thumbnail is marked (`aria-current="page"`) and kept in view; a click scrolls to its page.
- **R18** A thumbnail shows the page's `PageBadge` (text, appearance) if it has one, and none otherwise; the badge's `label` is part of the thumbnail's accessible name ("Page 6, 2 values to check").

### Annotations

- **R19** A `Mark` is a box with an id, a label (its accessible name) and a `MarkStyle`: a colour (an `Appearance` or a `Color`) and a look (`fill`: tint without border, `outline`: border without tint, `fill-outline`: both). The tint blends with the page like a text marker, so the text below keeps its contrast.
- **R20** A `Note` is a point with an id, a label and a colour, drawn as a pin (a dot with a lighter ring) of the same size at every zoom, on top of the marks; its accessible name is "Note: <label>". The viewer shows no content of the note.
- **R21** Marks and pins are buttons; `attrs` adds the app's attributes to them (e.g. `hx-get`, `hx-target`), which work as on any element.
- **R22** pyhx draws hover and selected for every mark and pin. One annotation of a viewer is selected at a time; while one is selected, the other marks recede. Selecting the selected annotation again, or Esc in the viewer, clears the selection.
- **R23** A click on a mark or a pin selects it and dispatches `hx-document:annotation-select` on the viewer (bubbling), with `detail.viewer`, `detail.id` and `detail.kind` (`"mark"` or `"note"`).

### Linking the content beside the viewer

- **R24** Any element with `data-hx-document-annotation="<viewer id>:<annotation id>"` selects that annotation on click (scrolling it into view) and highlights it on hover and focus; it also works for elements HTMX swaps in later.
- **R25** While an annotation is selected, every element linked to it has `aria-pressed="true"`, the others `"false"`; so the app can show a note's content in its sidebar with CSS alone.
- **R26** In the browser, `pyhx.documentViewer(id)` returns the viewer with `activate(annotationId)`, `clear()`, `goTo("<document id>:<page>")`, `setZoom(zoom)` and `fit()`.

### Sidebar

- **R27** `sidebar[...]` is a pane for the app's content beside the pages, scrolling on its own; its width is the CSS custom property `--document-viewer--sidebar-width` (default 22rem).

### Phone width and touch

- **R28** Below 40rem the thumbnails are hidden, the toolbar wraps into compact rows, the pages start at fit to width, the sidebar sits below the pages with at most 40 % of the height, and the page has no horizontal scroll outside the page column.
- **R29** On touch devices two fingers on the page column zoom (pinch); one finger scrolls.

### Texts, docs, tests

- **R30** The viewer's texts ("Document", "Pages", "Page {page}", "Note: {label}", "Previous page", "Next page", "Zoom in", "Zoom out", "Fit to width") are marked for translation and translated to de, it and fr.
- **R31** `samples/document_viewer` documents the component by example: an overview with the API at a glance, and one page per scenario with an explanation, the code cut from the page's own source, and the live viewer: basic viewer, several documents (groups, badges), marks (styles, stepping through a kind with the spotlight, the JavaScript API), notes (sidebar content by CSS, `hx-get` on a pin, the event), custom toolbar, and a case page with everything together.
- **R32** `docs/guides/document-viewer.md` (in the mkdocs nav under "Building Apps") explains the component and its scenarios in short, links the sample, and `poe docs-build` passes.
- **R33** The `/full` page of `samples/canvas_layout` shows a document viewer (with thumbnails and a sidebar) instead of the three placeholder panes.
- **R34** Tests cover the composition (standard and custom toolbar, fixed and following title, groups, badges, marks and notes with `attrs`, the sidebar, a part outside a viewer, a viewer without documents), the page size (given, missing, only one given, not positive), the geometry and its validation, and every sample page.

## Design

### API

```python
import pyhx.components as c

dv = c.document_viewer
vm = c.document_viewer.view_model   # or: from pyhx.components.view_model import document_viewer as vm
registration = vm.Document(
    id="anmeldung",
    title="IV-Anmeldung 001.001",
    subtitle="Received 21.06.2026",
    pages=[
        vm.DocumentPage(
            src=page_url(1), width=1240, height=1754,
            badge=vm.PageBadge("2", "2 values to check", appearance="warning"),
            annotations=[
                vm.Mark(id="beruf", label="Occupation",
                       box=vm.BoundingBox.from_pixels(x=104, y=288, width=180, height=44,
                                                     page_width=1240, page_height=1754),
                       style=vm.MarkStyle(color=c.Color.hex("#6d28d9"))),
                vm.Note(id="note-au", label="Start of incapacity",
                       at=vm.Point(0.89, 0.17), color="danger",
                       attrs={"hx-get": "/notes/au", "hx-target": "#note"}),
            ],
        ),
        ...
    ],
)

dv(id="case", documents=[registration, medical_report])[
    dv.toolbar[dv.back(href="/cases/42", label="Case"), dv.title(), dv.pager(),
               dv.zoom(), dv.fit(), dv.spacer(), c.pill("3 to check")],
    dv.thumbnails(),
    dv.pages(),
    dv.sidebar[...],   # the app's content: data-hx-document-annotation="case:<id>"
]
```

### Rendering

- `c.document_viewer` is a singleton like `c.card`; calling it returns the root element, which provides the viewer's state (`id`, documents) through an htpy `Context`. The parts are context consumers, so they find the documents wherever the app places them inside the root.
- `toolbar()` without children is rendered within the context (it implements htpy's `iter_chunks`, not only `__html__`), so the standard controls can read the documents.
- Marks and notes are absolutely positioned buttons in an overlay over each page image, positioned in % of the page; pages get a width of `--document-viewer--page-width × --document-viewer--zoom` and an `aspect-ratio` from their size, so zoom is a single custom property and boxes stay in place.
- A page without both sizes gets the A4 ratio and `data-hx-document-ratio="assumed"`; when its image loads, the script sets the ratio from the image's natural size (page and thumbnail) and removes the marker. Lazy loading keeps working, since every page has a height before its image arrives.
- Data types are frozen dataclasses (like `Color`), validated in `__post_init__`, in `pyhx.components.view_model.document_viewer` next to the other view values; the singleton exposes the module as `c.document_viewer.view_model`. A package of its own named `document_viewer` is avoided, since importing it would shadow the singleton `c.document_viewer`.

### Browser

- One script, `static/js/pyhx.document-viewer.js`, loaded by `Skeleton` like the other component scripts; it initialises every `[data-hx-document-viewer]` on load and on `htmx:load`, and handles the document-wide activation attributes by event delegation (so swapped-in sidebar content works without re-initialising).
- State lives in the DOM: zoom in a custom property, the current page in `aria-current` and the counter, the selection in `aria-pressed`, hover in `data-hover`. The server keeps nothing.
- Current page: a scroll listener (once per animation frame) finds the page under the middle of the column; while a scroll started by the viewer runs, it is paused until `scrollend` (with a time limit).
- Pinch zoom: `touchstart`/`touchmove` with two touches scale the zoom; the column has `touch-action: pan-x pan-y`, so one finger scrolls natively.

### CSS

- `static/css/pyhx/components/layout/document-viewer.css`, imported in `pyhx.css` in the `pyhx` layer, following the CSS decision: BEM classes `hx-document-viewer__*`, component-local custom properties `--document-viewer--*`, state by attributes and `:has()` (the spotlight is `.hx-document-viewer:has([aria-pressed="true"]) .hx-document-viewer__mark:not([aria-pressed="true"])`), design tokens with fallbacks.
- A mark's colour arrives as one custom property; `color-mix` derives tint, border and ring, and `mix-blend-mode: multiply` makes the tint behave like a text marker. The canvas design is the reference; the default design gets the same rules (they use only tokens).

### Files

```text
src/pyhx/components/view_model/document_viewer.py # Document, DocumentPage, PageBadge, Mark, MarkStyle, Note, BoundingBox, Point
src/pyhx/components/layouts/document_viewer.py    # c.document_viewer: root, parts, controls; .view_model points to the module above
src/pyhx/static/css/pyhx/components/layout/document-viewer.css
src/pyhx/static/js/pyhx.document-viewer.js
samples/document_viewer/ (main, pages/, sample_document, static/css/sample.css)
docs/guides/document-viewer.md
tests/pyhx/components/test_document_viewer.py, tests/samples/document_viewer/
```

## Alternatives considered

- **An object with methods (`viewer = DocumentViewer(...); viewer.toolbar()`):** the first draft; it works, but differs from how pyhx composes components with parts (`c.card[c.card.header[...]]`), and passing the viewer object around is needed only because the parts can't find the documents otherwise, which the context solves.
- **One document at a time, switched by the thumbnail groups:** needs a request or hidden pages per switch, and a note or value in another document can't be scrolled to directly; the developer chose documents one after another (intent Q7).
- **`@panzoom/panzoom` for zoom and pinch:** MIT and small, but it zooms with CSS transforms on one element, which fights the native scrolling of the page column and the width-based zoom that keeps boxes in place; pinch on top of the existing zoom is a few lines of plain JavaScript.
- **pdf.js and a text layer:** out of scope; pages are images rendered by the app (intent).
- **A popover with the note's text in the document:** out of scope (intent Q8); the sidebar shows it, linked by `aria-pressed`.
- **Pages without any size, always measured from the image:** simpler data, but a page has no height before its image loads, so lazy loading would load every page at once and scrolling to page 9 would land in the wrong place while the pages above it load; the optional size with an A4 fallback (developer's decision) keeps both working.
- **Pydantic models for the data:** would allow parsing JSON directly, but pyhx's view values (`Color`) are dataclasses, apps map their domain to view types anyway, and dataclasses validate the few rules needed.
- **A configurable spotlight (on/off, strength):** not asked for; the selected annotation must stand out among many (developer), so it is always on.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Public addition on `versions/1`, no breaking change (`feat:`) | R1, R5; new names only: `c.document_viewer` and the module `view_model.document_viewer` |
| htpy, HTMX, CSS conventions, design tokens, `Appearance`/`Variant`/`Color`; plain JavaScript; small library only where it clearly helps, with a licence for sold products | Design (Rendering, CSS, Browser); R13 uses `c.button`; R19 `Appearance`/`Color`; no library needed (Alternatives: panzoom) |
| Canvas design first, `AppShell` must not break | Design (CSS: tokens only, own BEM namespace); R4 |
| Accessible (buttons with names, readable counter and zoom, thumbnails by keyboard, annotations by keyboard with a text alternative) | R13, R11, R12 (`aria-live`), R17, R18, R20, R21, R22 (Esc), R25 |
| Usable at 390 px without horizontal scroll | R28 |
| Texts translated to de, it, fr | R30 |
| A few dozen pages stay fast; space reserved, images lazy | R7, R15, R16 |
| No viewer state on the server | Design (Browser: state in the DOM) |
| Sidebar container part of the viewer, mobile friendly; content the app's | R27, R28 |
| Toolbar from one sub-component per control, standard composition, custom controls | R8, R9, R14 |

## Open questions

Answer below each question; leave **Answer** empty to accept the proposal.

### Q1 Composition like `c.card`

**Proposal:** `c.document_viewer(id=, documents=)[c.document_viewer.toolbar(), ...]` with the parts reading the documents through an htpy context (R1, Design), instead of the object with methods of the first draft. It is how pyhx composes components with parts, and apps write `dv = c.document_viewer` for short. See every page of the sample.

**Answer:** Yes.

### Q2 Names of the data types

**Proposal:** Export them under their plain names in `pyhx.components`: `c.Document`, `c.DocumentPage`, `c.PageBadge`, `c.Mark`, `c.MarkStyle`, `c.Note`, `c.BoundingBox`, `c.Point` (none is taken). The alternative, a namespace (`c.document_viewer.Mark`), avoids future clashes of generic names like `Note` and `Point` but makes every annotation longer to write.

**Answer:** probably the document_viewer namesapce would be smarter. As some of these classes are very generic. Maybe document_viewer.view_model?

### Q3 Where the documentation lives

**Proposal:** `samples/document_viewer` is the documentation by example (R31, kept and tested), `docs/guides/document-viewer.md` the short guide that links to it (R32), and `/full` of `samples/canvas_layout` shows the viewer in the canvas sample (R33). `samples/components` (AppShell, default design) gets no page, since the viewer needs a full-height canvas layout.

**Answer:** Yes, ok.

### Q4 Pinch zoom without a library

**Proposal:** Pinch zoom in plain JavaScript on top of the toolbar zoom (R29, Design), no `@panzoom/panzoom` (Alternatives). It is in the draft but untested on real devices; the plan includes a test on an iPhone and an Android tablet.

**Answer:** Ok, for now.

### Q5 Keyboard with many annotations

**Proposal:** Marks and pins are buttons in document order, so Tab reaches each of them (R21). With dozens of marks this means many tab stops; keep it for the first version (simple and fully accessible), and decide a roving tab index (one stop per page, arrow keys inside) when CaseSight shows real documents.

**Answer:** Yes. 

## Areas of concern

1. **Rendering the default toolbar within the context** (R8, R1): relies on htpy calling `iter_chunks(context)` before `__html__`; covered by the test of the standard toolbar inside a viewer, and the async variant (`aiter_chunks`) by a test with htpy's async rendering. Owner: Michael Wellner.
2. **Pages that are not A4 without a size** (R7): until its image loads, such a page has the A4 height, so the column shifts once when it loads (e.g. a landscape page); apps that know the sizes (CaseSight renders the PNGs) give them and avoid it. Owner: Michael Wellner.
3. **Performance with long documents** (R15, R16): the current-page check walks all pages once per frame while scrolling, and every mark is a blended element; fine for a few dozen pages in the sample, to be measured with CaseSight's largest documents. Owner: Michael Wellner.
4. **Pinch zoom on real devices** (R29): only simulated; the plan tests it on iOS Safari and Android Chrome. Owner: Michael Wellner.
5. **Blend mode and `:has()`** (R19, R22): supported by all current browsers; older browsers show the tint without blending and no spotlight, which stays usable. Owner: Michael Wellner.
6. **Data model of CaseSight** (R5, R6): not settled yet; the viewer's types are view types, so CaseSight maps its model to them in its own change. Owner: Michael Wellner.

## Out of scope

- The controls of the demo's sidebar (extracted values, search, categories, confirm or correct): app content.
- Rendering PDFs to images, a text layer, text selection, full-text search.
- Drawing or editing annotations by the user; a popover with a note's content.
- Rotation, a single-page mode, opening a document at a page through the URL, documents side by side, keyboard shortcuts beyond the focused controls and Esc.
- A page of `samples/components` (Q3).

## Outcome

Implemented as specified, with these deviations and findings (from the plan, removed at close-out):

- **D1** The examples and the guide import the data types as a module, `from pyhx.components.view_model import document_viewer as vm`: mypy accepts a variable bound to a module (`vm = c.document_viewer.view_model`) for attribute access but not in type annotations. `c.document_viewer.view_model` stays as a shortcut (R5 unchanged).
- **F1** The data types live in `pyhx.components.view_model.document_viewer` (Q2), next to `Color`; the package stays neutral (it imports only htpy, `Color` and the variants). A package named `document_viewer` was avoided, since importing it would shadow the singleton `c.document_viewer`.
- **F2** `toolbar()` without children must render within the viewer's htpy context: it implements `iter_chunks`/`aiter_chunks` (htpy calls them before `__html__`); tested for sync and async rendering.
- **F3** `poe check` lints and formats only `src/pyhx`; the samples keep their own style, so only the files of this change were formatted.
- **F4** A thumbnail jump with smooth scrolling used to pass the current page through every page on the way; the viewer now selects the target at once and pauses the scroll tracking until `scrollend` (R16).

Screenshots (from the samples): [overview](screenshots/document-viewer--overview--desktop.png), [basic example](screenshots/document-viewer--basic-example--desktop.png), [several documents](screenshots/document-viewer--several-documents--desktop.png), [marks and spotlight](screenshots/document-viewer--marks-spotlight--desktop.png), [notes](screenshots/document-viewer--notes--desktop.png), [custom toolbar](screenshots/document-viewer--custom-toolbar--desktop.png), [case page](screenshots/document-viewer--case--desktop.png), [case page at phone width](screenshots/document-viewer--case--phone.png); `/full` of the canvas sample [before](screenshots/canvas-shell--full--before.png), [after](screenshots/canvas-shell--full--desktop.png) and [at phone width](screenshots/canvas-shell--full--phone.png).

Rollout: pull request #42 (`feat: add a document viewer with annotations`); released with the next pyhx release on `versions/1` by release-please.

Open after this change:

- Pinch zoom tested only with simulated touch events; test it on iOS Safari and Android Chrome (Michael Wellner).
- Measure scrolling and blending with CaseSight's largest documents; decide a roving tab index for pages with many marks then (Q5) (Michael Wellner).
- Use the viewer in CaseSight once its data model for marks and notes is settled: a change of CaseSight (Michael Wellner).
- The top bar of the canvas design at phone width stays T-009.
