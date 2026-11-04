# T-022 Annotation navigation in the document viewer

## Problem

Apps that list the annotations of a document beside `c.document_viewer` (in `dv.sidebar`, linked with `data-hx-document-annotation`) need four things the viewer doesn't offer, so each app would write its own script and CSS:

- One annotation, several areas: a quote that runs over two lines, or from one page to the next, is several boxes. The viewer selects one mark at a time, so selecting such an annotation lights up one line while the others recede with the rest. In the analysis results of the app that asked for this change, 43 % of the annotations have two or more areas, 45 of 1444 on two pages.
- Stepping through the annotations: previous and next with the position ("5 / 12"), across the pages of the documents in view. Today only `pyhx.documentViewer(id).activate(id)` exists, and the app has to know the order.
- Showing and hiding marks by a category (e.g. the type of a finding) without reloading the viewer. Marks have a style but no category, so an app can only render the viewer again without them.
- When a mark is clicked, the linked element beside the viewer gets `aria-pressed="true"`, but it isn't scrolled into view; in a long list it stays hidden.

## Proposed outcome

- Several marks can form one annotation: selecting, hovering, linking and previous/next treat them as one; selecting it scrolls to its first area and highlights all of them.
- A viewer part for previous and next annotation with the position, for the toolbar or the sidebar; ordered by document, page and position on the page; it follows the selection, also from clicks on marks and linked elements, and skips hidden marks.
- A category on marks (and notes), and toggle buttons beside the viewer that show and hide categories in the browser, with `aria-pressed`; hidden marks are neither drawn nor counted by previous and next. The server gives the initial state.
- A click on a mark scrolls the linked elements into view inside their scrolling container, only when they are outside it and without moving the page.
- A sample in `samples/document_viewer` with a list of annotations in the sidebar, filtered by category, with previous and next; the guide `docs/guides/document-viewer.md` describes it.
- Not part of it: the list itself (the app builds it), editing annotations, the source picker (its marks stay unselectable).

## Affected users and systems

- **Apps with `c.document_viewer`:** new, optional parameters and parts; existing viewers look and behave as before.
- **CaseSight (T-022 Document Reader):** the first user: the findings of a file in the sidebar, by type, with previous and next.
- **`c.source_picker`:** shares the viewer's script; must keep working unchanged.

## Constraints

- Backwards compatible (a `feat`, no breaking change): `vm.Mark`, `vm.Note`, `data-hx-document-annotation` and `pyhx.documentViewer(id)` keep their meaning.
- No new dependency; the viewer's own script and CSS (`pyhx.document-viewer.js`, `document-viewer.css`).
- Accessible: real buttons with `aria-pressed` and labels, keyboard usable, texts translated (en, de, it, fr).
- Works for content swapped in by htmx later, like the existing links.
- No client names or product screenshots in the repository.

## Open questions

None. Decided by the developer on 4 November 2026: the three additions go to pyhx; the fourth (one annotation, several marks) follows from the sample data and is added under the same authorization.
