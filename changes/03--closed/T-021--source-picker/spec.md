# T-021 Source picker: spec

## Requirements

### Component

- **R1** `c.source_picker(id=…, documents=…, name="source", value=None, **attrs)` renders a document viewer (the parts of `c.document_viewer`: toolbar with title, pager, zoom and fit, thumbnails, pages) with a footer that shows the choice, "Clear area" and the hidden inputs. `documents` are `Document`s of the viewer's view model; at least one is required.
- **R2** It shows one page at a time: the chosen page. Thumbnails and previous/next choose a page (all pages of all documents in order); thumbnails, pager and zoom are the viewer's, so all of them work by keyboard. Without `value` the first page of the first document is chosen.
- **R3** The hidden inputs `<name>_document` (document id), `<name>_page` (1-based page number) and `<name>_box` (`"x,y,width,height"`, fractions of the page with four decimals, origin top left; empty for the whole page) always hold the current choice, so a plain form or htmx post carries it.
- **R4** `value=vm.SourceChoice(document_id, page, box=None)` opens the picker at that page with that box drawn; a value whose document or page isn't among `documents` falls back to the first page, without box.
- **R5** `vm.SourceChoice.from_form(form, name="source")` reads the posted inputs: `None` when `<name>_document` is missing or empty, a `SourceChoice` otherwise; a page that isn't a positive integer or a box that isn't four fractions within the page raises `ValueError`. Whether the document and page exist is the app's check.
- **R6** Marks and notes of the pages are shown but can't be selected or focused (read-only).

### Many documents (added after the demo)

- **R15** `files: Sequence[DocumentLink] | None = None`: with two or more entries the toolbar shows the document switcher of `document_viewer.files` (search, groups, previous/next, "n of total documents") instead of the title, and `documents` may hold only the current document. With no `files`, or fewer than two entries, the picker is as before (one document or several in `documents`).
- **R16** Inside the picker, choosing an entry or previous/next document doesn't navigate: the script fetches the entry's `href` with htmx and swaps the picker root (`outerHTML`), so it works inside `c.dialog_content`; the app's route returns the picker for that document, whose inputs then hold its choice. The focus returns to the switcher's button (or the page column after previous/next).
- **R17** The sample has a dialog with one document, with two documents and with 30 documents in three folders.

### Drawing

- **R7** A pointer drag (mouse, touch, pen) on the page draws one box, replacing the previous one; a drag shorter than 1 % of the page in width or height keeps the previous box. A drag on the box moves it, a drag on one of its four corner handles resizes it; the box always stays within the page.
- **R8** The box is focusable ("Marked area"): arrow keys move it by 1 % of the page, Shift + arrow keys resize it, Delete, Backspace and Escape remove it. Escape inside the picker removes the box without closing a surrounding dialog; without a box, Escape works as before (closes the dialog).
- **R9** "Clear area" in the footer removes the box; it is disabled without one. Choosing another page removes the box.
- **R10** Every change of the choice updates the hidden inputs and the footer's text ("Registration, page 3: whole page" / "…: marked area", read by screen readers) and dispatches `hx-source-picker:change` on the picker (bubbling) with `detail = {picker, document, page, box}` (`box` `{x, y, width, height}` or `null`).
- **R11** The page fits the picker's height and width when it opens and on "Fit"; one finger on the page draws (no scrolling), so the page is never larger than the picker unless the user zooms in.

### Layout

- **R12** Inside `c.dialog_content` the dialog widens to fit the picker (at most 64rem), and the picker has a fixed height (min of 36rem and 70 % of the window height).
- **R13** Below 40rem the thumbnails are a horizontal strip between toolbar and page, the handles are at least 1.5rem, and the footer wraps.

### Delivery

- **R14** Texts translated into de, it, fr; a section "Source picker" in `docs/guides/document-viewer.md`; a sample page "Source picker" in `samples/document_viewer` that opens the picker in a dialog (empty, and preset with a box) and shows the posted choice; tests of rendering, `SourceChoice` and the sample; `poe check` and `poe docs-build` green.

## Design

- **Python** (`components/layouts/source_picker.py`): `source_picker(...)` builds `document_viewer(id, documents, start=f"{doc}:{page}")` with `class_="hx-source-picker"`, `data_hx_source_picker=name` and the internal flag `paged=True` of `_Root`, and the parts `toolbar[title(), pager(), zoom(), fit()]`, `thumbnails()`, `pages()`, plus the footer (`hx-source-picker__footer`: status text, clear button, three hidden inputs). Exported as `pyhx.components.source_picker`.
- **Viewer, paged** (internal, no public parameter): `_Viewer.paged` renders `hidden` on every page but the start page and `inert` on the annotations layers; `_Root` renders `data-hx-document-paged`. The viewer script, when paged, shows a page by toggling `hidden` instead of scrolling to it, doesn't follow the scroll position, and fits the page into width and height. `setCurrent` dispatches `hx-document:page` (`detail = {viewer, page: "<document>:<page>"}`) on the viewer, for every viewer (an addition).
- **Script** (in `pyhx.document-viewer.js`, a section "source picker", so no new script tag): per `[data-hx-source-picker]` root: reads the box from the input on load and draws it, listens to `hx-document:page` (new page: clear box, update), pointer events on the shown page (`setPointerCapture`; draw, move, resize by handle), keys on the box and Escape on the picker, the clear button. The box is a `div.hx-source-picker__area` (`tabindex=0`, `role="group"`, `aria-label` "Marked area" and the keys as its title) with four `span[data-handle]` placed in percent of the page, so zoom needs no recalculation.
- **View model:** `SourceChoice` in `view_model/document_viewer.py` (exported with the others).
- **CSS:** `components/layout/source-picker.css`, imported after `document-viewer.css`: footer, area and handles, `touch-action: none` on the page, read-only marks, dialog width via `.hx-dialog > dialog:has(.hx-source-picker)`, phone layout.

## Alternatives considered

- **A drawing part for any document viewer (`dv.area(...)`):** drawing in a scrolling column of all pages makes the choice ambiguous (scrolled away from the box's page), and a viewer page and a form control have different jobs; the picker reuses the parts instead.
- **Four hidden inputs for the box:** one input with four numbers is easier to keep consistent (all or nothing) and to read with `from_form`.
- **A separate script file:** a new `<script>` in the skeleton for a few dozen lines that depend on the viewer's script anyway.

## Constraint mapping

| Constraint | Met by |
| --- | --- |
| Non-breaking minor | new component and type; `paged` is internal; `hx-document:page` is an addition |
| Plain JS, no dependency | Design: script section in `pyhx.document-viewer.js` |
| i18n | R14 |
| Public repo, neutral content | R14: the sample's made-up documents of T-010 |

## Open questions

None.

## Areas of concern

1. **Touch on large zoom** (R11): one finger on the page draws, so a page zoomed beyond the picker scrolls only with two fingers, the scroll bars or the margins. Fit is the default. Owner: Claude.
2. **Escape in dialogs** (R8): the dialog's script ignores an Escape whose default was prevented; the picker prevents it only while a box exists. Checked in the browser. Owner: Claude.

## Out of scope

- Several boxes or pages per choice, text selection, polygons.
- Validating the posted document and page against the app's documents (the app's check, R5).

## Outcome

Built as specified. Proof: `tests/pyhx/components/test_source_picker.py` (inputs, start page, shown page, fallbacks, read-only annotations, the viewer unchanged; `SourceChoice.from_form` and its refusals) and `tests/samples/document_viewer/test_source_picker_sample.py`; the sample page "Source picker" checked in a browser at 1280 px and 390 px (touch emulated): drawing, moving, resizing by a corner beyond the page (clamped), arrow keys and Shift + arrow keys, Escape removes the area and keeps the dialog open, a second Escape closes it; a thumbnail chosen by keyboard (Enter) chooses the page; posting echoes the choice; "Edit this source" opens at the page with the area; a dialog sent again by the server (morph) takes the inputs' page and area and the pager follows; the existing viewer pages scroll and track the current page as before.

R15–R17 were added after the developer's review of the demo ("many documents: a document switcher as in the document reader"; "a single document stays supported"). Checked in the browser: in the 30-document dialog, typing in the switcher's search and Enter, a click on an entry (also by touch at 390 px) and "Next document" replace the picker without leaving the page or closing the dialog; the inputs hold the new document's page 1; drawing works in the swapped picker; posting echoes it. Tests: the switcher in place of the title, a single entry rendering exactly as without `files`, a single document without `files`, and the sample's routes.

Deviations:

- In paged mode the zoom may go below the smallest step (to 25 %), so a whole page fits a small picker; zooming out by the buttons still stops at 50 %.
- `hx-document:page` is dispatched by every viewer on each change of its current page (documented in the guide), not only by the picker.
- The picker has no `overflow: hidden`, so the switcher's dropdown isn't cut off; at phone width the switcher hides its position ("n of total documents"), the pager shows the place.

Findings: a picker sent again by the server keeps its root element (morph), so the script takes its state from the inputs again on `htmx:load` (`sync`), including the viewer's current page; otherwise previous/next continued from the old page. A picker swapped in with `outerHTML` is the target of `htmx:load` itself, so the script's `init` now includes the scope element (`within`), for viewers too.

Screenshots (sample `samples/document_viewer`, page "Source picker"):

- [An area drawn, desktop](screenshots/document-viewer--source-picker-area--desktop.png)
- [The posted choice, desktop](screenshots/document-viewer--source-picker-posted--desktop.png)
- [Whole page, phone](screenshots/document-viewer--source-picker-whole-page--phone.png)
- [Document switcher, desktop](screenshots/document-viewer--source-picker-switcher--desktop.png)
- [Document switcher, phone](screenshots/document-viewer--source-picker-switcher--phone.png)

No "before": the component is new.

Open: the page fits the picker on open and on "Fit page", not again when the window is resized; touch users zoomed in beyond the picker scroll with two fingers (concern 1). JavaScript has no automated tests in this repository. The switcher's entries are rendered all at once, as in the document viewer (T-018).
