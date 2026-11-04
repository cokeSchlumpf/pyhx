# T-021 Source picker

## Problem

An app that lets users write a statement about documents can't let them say where it comes from: pick a document, a page, and optionally an area on that page. The document viewer (T-010, T-018) shows pages, thumbnails and marks, but nobody can draw a box on a page, and nothing it shows can be posted with a form. Each app would have to build its own drawing on top of the viewer's markup.

## Proposed outcome

- A component `c.source_picker(...)` usable inside a form or a dialog (`c.dialog_content`): it shows a set of documents (the `Document`/`DocumentPage` view models of the document viewer), lets the user switch documents and pages by thumbnails and the pager, and choose a page.
- On the chosen page the user may draw one rectangle by pointer drag (mouse, touch, pen), then move and resize it with handles; Escape or "Clear area" removes it. Without a box the whole page is the choice. Choosing a page without a box works by keyboard alone.
- The choice (document id, page number, box as fractions of the page, or none) is in hidden inputs with a name prefix given by the app, so a plain form or htmx post carries it; a DOM event is dispatched on every change. A preselected choice (document, page, box) opens the picker there, to edit an existing source.
- Marks of the pages are shown read-only.
- Works at phone width; texts in en, de, it, fr; a sample page with a dialog that echoes the posted choice; a guide section; tests.
- Doesn't: several boxes, boxes on several pages, text selection, polygons.

## Affected users and systems

- **Apps with documents:** first user app--casesight T-013 (R11: "Add source" for a sentence the user writes).
- **pyhx document viewer:** its parts are reused; its behaviour and markup stay as they are for existing viewers.

## Constraints

- Non-breaking, released as a minor version on `versions/1`.
- Plain JavaScript as the viewer's, no build chain, no new dependency; CSS after the CSS authoring conventions; pyhx i18n.
- pyhx is public: neutral sample documents, no client names.

## Open questions

None.
