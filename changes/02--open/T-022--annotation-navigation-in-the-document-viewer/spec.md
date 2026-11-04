# T-022 Annotation navigation in the document viewer: spec

## Requirements

### One annotation, several marks

- **R1** `vm.Mark` takes `annotation: str | None = None`: the annotation the mark belongs to. Marks with the same `annotation` are one annotation; without it a mark is an annotation of its own, named by its `id` (as before).
- **R2** Selecting an annotation (a click on one of its marks, a linked element, `activate(id)`, `selected=`, previous/next) presses all its marks (`aria-pressed="true"`), and scrolls to its first mark in document order; the other marks recede as before. A click on a pressed mark clears the selection.
- **R3** Hovering or focusing a mark, or an element linked to its annotation, highlights all marks of the annotation.
- **R4** `data-hx-document-annotation="<viewer>:<id>"`, `selected=`, `activate(id)` and `hx-document:annotation-select` (`detail.id`) use the annotation's id. Viewers whose marks have no `annotation` render and behave as before.

### Previous and next annotation

- **R5** `dv.annotation_pager(previous_label=None, next_label=None)` renders previous and next buttons with the position between them: "{n} / {total}" while an annotation is selected, "– / {total}" otherwise; usable anywhere inside the viewer (toolbar, sidebar). Default labels "Previous annotation" and "Next annotation".
- **R6** The order is by document, page, and the top then left of the annotation's first mark or note; notes count as annotations. Hidden annotations (R9) are skipped and not counted.
- **R7** Next without a selection selects the first annotation, previous the last; from the last, next goes to the first, and the other way round. With no annotation shown both buttons are disabled.
- **R8** The position follows every selection change, also from marks, linked elements and `activate`, and every change of the hidden categories.

### Categories

- **R9** `vm.Mark` and `vm.Note` take `category: str | None = None`. `document_viewer(..., hidden_categories=())` renders the marks and notes of those categories hidden.
- **R10** An element with `data-hx-document-category-toggle="<viewer>:<category>"` shows and hides the category on a click and has `aria-pressed="true"` while the category is shown. Any element with `data-hx-document-category="<viewer>:<category>"` (e.g. the entries and headings of a list) is hidden with it. Both work for content swapped in by htmx later.
- **R11** Hiding the category of the selected annotation clears the selection. Every change dispatches `hx-document:categories` on the viewer with `detail.viewer` and `detail.hidden` (the hidden categories).
- **R12** `pyhx.documentViewer(id)` also returns `showCategory(category, shown)`, `next()` and `previous()`.

### Linked elements in view

- **R13** When an annotation is selected by a click on a mark, by previous/next or on load, each linked element outside the visible part of its nearest scrolling container is scrolled into view inside that container; the page around the viewer doesn't move. Selection by a click on the linked element itself doesn't scroll it.

### Sample and guide

- **R14** The sample `samples/document_viewer` gets a page "Annotation list": a document with marks of several categories, one annotation over two lines and one over two pages, a sidebar with category toggles and a list of the annotations grouped by category, and the annotation pager.
- **R15** The guide `docs/guides/document-viewer.md` describes R1–R13; new texts are translated into de, it and fr; `poe check` is green.

## Design

- **View model.** `Mark(id, box, label, style, attrs, annotation=None, category=None)`, `Note(..., category=None)`; a property `Mark.annotation_id` (`annotation or id`). Annotation ids stay unique within a viewer; mark ids too.
- **Markup.** `_mark` renders `data-hx-document-annotation-id` with `annotation_id` (shared by the marks of one annotation), `data-hx-document-category` (`<viewer>:<category>` is not needed inside the viewer: the bare category) and `hidden` when the category is in `hidden_categories`. `_Root` renders `data-hx-document-hidden` (space separated, categories may not contain spaces: validated). `_Viewer` gets `hidden_categories: frozenset[str]`.
- **`dv.annotation_pager`.** A `div.hx-document-viewer__group` with two `_tool`s (`chevron-up`, `chevron-down`; actions `annotation-prev`, `annotation-next`) and a counter `span[data-hx-document-annotation-position]` (`aria-live="polite"`); the server renders "– / {total}" (total = shown annotations) and the script keeps it up to date.
- **Script.** `find(id)` becomes `marks(id)` (all elements with that annotation id); `select` presses all; `activate` scrolls to the first in document order. A function `annotations()` lists the shown annotation ids in order (DOM order of pages, then top/left of the first element, from the inline `left`/`top`), computed when needed. `updatePosition()` after each `select` and category change. Hover: a delegated `mouseover`/`mouseout` on marks inside the root calls `hover(id)`, which sets `data-hover` on all marks of the annotation. Categories: `hidden` set from `data-hx-document-hidden`; `showCategory(c, shown)` toggles `hidden` on the root's marks/notes with that category and on `document` elements with `data-hx-document-category="<viewer>:<c>"`, `aria-pressed` on the toggles, clears a selection that became hidden, dispatches the event; a delegated click on `[data-hx-document-category-toggle]`; on init the hidden state is applied to linked elements already on the page, and an `htmx:afterSwap` listener applies it to swapped content. Linked elements: `reveal(link)` finds the nearest ancestor with `overflow-y` `auto`/`scroll` and a scroll height above its client height, and moves its `scrollTop` only if the element is outside; never `scrollIntoView`.
- **CSS.** `.hx-document-viewer__mark[hidden], .hx-document-viewer__note[hidden] { display: none; }` (the buttons set `display`), the counter like `__counter` with `min-width` and tabular numbers.
- **Source picker.** Its annotations stay `inert`; the pager isn't part of it.

## Alternatives considered

- **A `group` of marks as its own type (`vm.Annotation(marks=[...])`):** clearer data, but a new container in `DocumentPage.annotations`, which holds the areas of one page; an annotation over two pages would have to be split again. A shared id on the marks fits the per-page model.
- **Hiding marks by re-rendering the viewer on the server (htmx):** works without pyhx changes, but loses zoom and scroll position and costs a round trip per click.
- **A toggle component (`dv.category_toggle(...)`) instead of an attribute:** apps style their chips themselves (colour, count); the attribute links any element, as `data-hx-document-annotation` does.
- **Linked list entries hidden by deriving the category from their annotation:** annotations without a mark (no box) have no category in the viewer; an explicit `data-hx-document-category` covers them and headings.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Backwards compatible | R1, R4, R9 (all optional), Design: unchanged markup without the new parameters |
| No new dependency | Design: viewer script and CSS only |
| Accessible, keyboard usable, translated | R5 (buttons with labels, `aria-live`), R10 (`aria-pressed`), R15 |
| Works for htmx-swapped content | R10, Design (delegated listeners, `htmx:afterSwap`) |
| No client names | R14 (generic sample document) |

## Open questions

None.

## Areas of concern

1. **Order of annotations by position** (R6): marks carry their position only as inline percentages; reading them from `style` is cheap and exact. Tested in the browser with the sample (two-line and two-page annotations). Owner: Claude.
2. **Scrolling the sidebar** (R13): with a selected entry that grows (details shown by CSS on `aria-pressed`), the measurement runs in the next animation frame. Checked in the browser at 1280 px and 390 px (sidebar below the pages: the page column is not a scrolling container of the entry, the page doesn't move). Owner: Claude.
3. **Many annotations** (R6, R8): ordering on every selection is O(n log n) over the marks of the viewer; fine for hundreds per document. Owner: Claude.

## Out of scope

- The list of annotations itself (the app builds it, as in the sample).
- Annotations without a mark (no position): the pager doesn't know them; the app lists them.
- Keyboard shortcuts for previous/next beyond the buttons.
