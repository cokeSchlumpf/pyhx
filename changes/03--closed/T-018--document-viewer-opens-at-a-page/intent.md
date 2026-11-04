# T-018 Document viewer opens at a page

## Problem

A link to a place in a document (a value read from page 3, the source of a finding) can't open the document viewer there: it always starts at the first page of the first document, and going to a page or selecting a mark is only possible from the app's own JavaScript (`pyhx.documentViewer(id).goTo(…)`, `.activate(…)`), after the viewer showed page 1. Apps with many documents also can't put all of them into one viewer (thousands of pages in the DOM), and the viewer has no way to switch between documents shown one at a time.

## Proposed outcome

- `c.document_viewer(id=…, documents=…, start="<document id>:<page>", selected="<annotation id>")`: both optional. The server renders pager, title and current thumbnail for the start page and loads its image eagerly; on load the viewer shows that page without smooth scrolling, or selects the annotation and scrolls it to the centre (`selected` wins). Without them nothing changes.
- `dv.files(entries=[vm.DocumentLink(title, href, group, detail, current)])`: a toolbar control that shows the current document on a button and opens a dropdown directly below it (left edges aligned, at least as wide): a search field, the entries grouped, the current one marked, entries without a link greyed out, a footer with the number of matches; typing filters in the browser, ↑/↓ and Enter choose, a click outside or Esc closes it. Beside it previous and next document and the position ("4 of 37 documents"). At phone width it is as wide as the toolbar with entries of at least 44 px.
- Guide and sample show both; texts in en, de, it, fr.

## Affected users and systems

- **Apps with the document viewer:** first user app--casesight T-014 ("Open page" of a finding's source; one file of a case at a time with a file switcher, design draft A of 3 November 2026).

## Constraints

- Non-breaking, released as a minor version on `versions/1`.
- pyhx's components and patterns: the dropdown closes like the tab groups of `CanvasShell` (`pyhx.canvas-shell.js`); no new dependency.

## Open questions

None.
