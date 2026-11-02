# T-010 Document viewer with annotations

## Problem

Apps on the canvas design need to show a document page by page next to what was read from it, as in the GILAI design template (`https://gilai-demo-refine.vercel.app/dossier/IV-2026-0142/dokument/dok-001`, screenshots in [screenshots/](screenshots/)). The first app is CaseSight, which already renders the pages of every uploaded file as PNG images (`/case-pages/<case_id>/<file_id>/<page>.png`) but has no way to show them.

pyhx has only the frame for it: `CanvasShell(mode="full")` and the `/full` page of `samples/canvas_layout`, whose three panes ("Thumbnails", the document, "Extracted values") are plain `<article>` placeholders. Everything a viewer needs is missing:

- a toolbar with the document's title, the page counter with previous and next ("1 / 12"), and zoom ("−", "125 %", "+");
- the pages one below the other in a scrolling column, with the counter following the scroll;
- a thumbnail rail that marks the current page, shows a badge per page and jumps to a page on click;
- several documents of a case in one viewer (a registration and the medical report that followed), grouped in the thumbnail rail;
- marks on the page images, like a text marker: transparent boxes over the areas something was read from, in different looks (a tint per category; a stronger border when the mark is the active one; orange tint and border for a value read with low confidence; a border without tint);
- notes of the case workers at a place on a page, shown as a pin, with their content in the sidebar;
- a way for the content next to the viewer (the extracted values in the right pane) to point at an annotation: selecting a value scrolls its page into view and marks its box as active.

A first design draft (canvas: assembled viewer, phone width, anatomy and API, annotation styles) is at `https://claude.ai/artifact/1TRn96YD9dnBLUqFsvrLwT`, and a working prototype in `samples/document_viewer` (draft component in `document_viewer.py`, run with `poetry run fastapi dev samples/document_viewer/main.py`); both are input for the spec, not decisions.

Every app would build this itself today, with its own JavaScript for scrolling, zoom and overlays, and none of it would follow the canvas design or be accessible.

## Proposed outcome

- pyhx offers a document viewer made of a few sub-components (toolbar, page column, thumbnail rail, annotation overlay, sidebar) that an app puts together in a few lines, inside the panes of `CanvasShell(mode="full")` or anywhere else.
- The viewer shows page images (any URL an `<img>` can load) with their width and height; how they are produced is the app's business.
- The toolbar is composed of one sub-component per control (back link, title, pager, zoom, fit to width) with a standard composition for the common case; an app can leave controls out, reorder them and add its own controls.
- The sidebar container is part of the viewer: a pane beside the pages, usable at phone width (below the pages, scrolling on its own); what it contains is the app's.
- The viewer shows one or more documents; each document has a title and a list of page images with their sizes. With several documents, the thumbnail rail groups the pages per document; whether the groups have headings is up to the composition (by default only with more than one document), and the toolbar shows the title of the document in view and counts its pages.
- A page has two kinds of annotations, each with an id and a label as its accessible name; their positions are fractions (0–1) of the page's width and height, origin top left, with helpers to convert from pixels of the page image:
  - a **mark** highlights an area like a text marker: a bounding box, transparent so the text below stays readable, in a style (colour: an `Appearance` or any `Color`; look: `fill`, `outline` or `fill-outline`) with the states hover and selected drawn by pyhx; an app picks a style per mark and maps its own categories and confidence to them (no app-specific style like "uncertain" in pyhx), and shows all marks of a kind while the user navigates from one instance to the next;
  - a **note** is a point on the page, shown as a pin (a circle with a lighter outer ring) in a colour; the viewer shows only the pin, the note's content is shown by the app beside the viewer, e.g. in the sidebar while the note is selected (no popover in the document);
  - marks and pins take further attributes of the app (e.g. `hx-get`, `hx-target`), so a click can also load content with HTMX.
- One annotation is selected at a time: it stands out, and while one is selected the other marks recede, so the selected instance is the most visible even among many of the same kind; selecting it again or Esc clears the selection.
- The badge of a page's thumbnail is the app's choice (text, meaning for screen readers, appearance), not derived by the viewer; a page without one shows none.
- The content beside the viewer can activate an annotation by its id, declaratively by an attribute or through a small JavaScript function (scroll into view, select), and clicking a mark or a pin dispatches a DOM event with its id and kind, so a sidebar like the one of the demo, with the notes' content, can be built on top without the viewer knowing it.
- Several documents are shown one after another in the page column, each starting with its title; previous and next run across documents.
- At phone width the thumbnail rail is hidden, the toolbar is compact and the pages start at fit to width.
- Zoom (steps, fit to width; pinch zoom on touch devices if the spec takes it in), current page and scrolling stay in the browser; the server only renders the document.
- `samples/canvas_layout` gets a working document page instead of the placeholders, and the components are documented with an example.
- Deliberately not part of it: the controls of the right sidebar (extracted values, search, categories, confirm or correct, as in the demo); rendering PDFs or other formats to images (the app does that, CaseSight already does); a text layer, text selection or full-text search in the document; drawing or editing annotations by the user; showing a note's content inside the viewer (popover); rotation, a single-page mode, opening a document at a given page through the URL, keyboard shortcuts beyond the focused controls and Esc, and documents side by side.

## Affected users and systems

- **App developers (CaseSight first):** get the components to build their document page; CaseSight uses them in a later change of its own, once its data model for marks and notes is settled.
- **Users of these apps (case managers):** read documents in the browser and find the place a value was read from.
- **pyhx:** new components, CSS and a small script in `static/`, translated texts (labels of the toolbar), a sample page, docs and tests; existing components and the `/full` page layout of `CanvasShell` must keep working.

## Constraints

- A public addition to `pyhx.components` on `versions/1`, no breaking change (`feat:`).
- Built with what pyhx uses already: htpy, HTMX, the existing CSS conventions (`docs/decisions/2026-05-27-1436--css-authoring-conventions.md`) and design tokens, the shared variant vocabulary (`Appearance`, `Variant`, `Color`); plain JavaScript like the other `pyhx.*.js` files; a small JavaScript library is fine where it clearly helps (vendored into `static/` like htmx, see Q9), but no PDF renderer such as pdf.js, since pages are images. A library must have a license that allows its use in a product that is sold (MIT, BSD, Apache 2.0), and its license notice is kept with the vendored file.
- Works in the canvas design first; the default design (`AppShell`) must not break.
- Accessible: the toolbar buttons are real buttons with labels, the page counter and zoom are readable by screen readers, thumbnails are reachable by keyboard, an annotation can be activated by keyboard and has a text alternative (its label).
- Usable at phone width (390 px), with no horizontal scroll of the page outside the zoomed document.
- Texts users see (toolbar labels, "Page 3", counts) are translated to de, it and fr in the same change.
- Documents of a few dozen pages must stay fast: page images load when they come near the viewport, and their space is reserved from the known sizes so scrolling doesn't jump.
- The server keeps no viewer state between requests.

## Open questions

None.
