# T-018 Document viewer opens at a page: spec

## Requirements

### Start position

- **R1** `document_viewer(...)` takes `start: str | None` and `selected: str | None`; without them the markup is the same as before.
- **R2** With `start` (`"<document id>:<page>"` of the viewer), the pager's current page and count, the title and subtitle, the thumbnail with `aria-current="page"`, the disabled state of previous/next and the eagerly loaded page images (that page and the next) are those of the start page; an unknown `start` falls back to the first page.
- **R3** On load the script shows the start page at the top of the page column, without smooth scrolling.
- **R4** With `selected`, the annotation is selected on load (as by `activate`) and scrolled to the centre without smooth scrolling; it wins over `start`; an unknown id selects nothing.

### Document switcher

- **R5** `dv.files(entries)` with `vm.DocumentLink(title, href=None, group=None, detail=None, current=False)` renders a button with the current entry's title and group that opens a dropdown below it, left edges aligned, at least as wide as the button.
- **R6** The dropdown: a labelled search field; the entries under their group headings in the order given; title and detail per entry; the current entry marked (`aria-current="true"`); an entry without `href` greyed out and not a link; a footer with the number of entries matching and the keys.
- **R7** Typing filters by title and group, case-insensitive and ignoring accents, in the browser; empty groups are hidden; ↑/↓ move the active entry, Enter opens it; a click outside or Esc closes the dropdown and returns the focus to its button.
- **R8** Previous and next document (the neighbouring entries with `href`, disabled at the ends) and the position "{n} of {total} documents" are rendered beside the button.
- **R9** Below 40rem the dropdown spans the toolbar's width and its entries are at least 44 px high.
- **R10** The guide `docs/guides/document-viewer.md` and the sample (a new page "Open at a page") show `start`, `selected` and `dv.files`; new texts translated into de, it, fr; `poe check` green.

## Design

- `_Viewer(id, documents, start, selected)`; `_start(state) -> (Document, int)` resolves `start`. `_pager`, `_title`, `_thumbnail_group` and `_document` use it instead of `documents[0]` / page 1. `_Root` renders `data-hx-document-start` and `data-hx-document-selected`.
- Script: `viewer(root)` (created once per root) reads both attributes after wiring the listeners: `selected` → `activate(id, {behavior: "auto"})`, else `start` → `scrollTo(page, index, "start", "auto")`. `scrollTo` and `activate` take an optional `behavior`.
- `dv.files(entries)`: `<div class="hx-document-viewer__files">` with a `<details>` (summary = button; panel = search, list, footer) and the prev/next links (`button(icon=…, href=…, variant="ghost", size="sm")`, disabled as buttons without href) and the position. Script: delegated `input` and `keydown` on `.hx-document-viewer__files`, outside click and Esc as in `pyhx.canvas-shell.js`; the list items carry `data-hx-document-search` (normalized title and group).
- CSS in `components/layout/document-viewer.css`.

## Alternatives considered

- **App JavaScript calling `goTo`/`activate`:** visible jump from page 1, and every app writes the same lines.
- **Using `c.dropdown`:** a form control of radios or checkboxes without search or links.

## Constraint mapping

| Constraint | Met by |
| --- | --- |
| Non-breaking minor | R1, all parameters optional, new part |
| Closes like CanvasShell's groups | R7 |

## Open questions

None.

## Areas of concern

1. **Position shifts while images load** (R3, R4): pages without size reserve A4 until loaded; pages above the start aren't loaded and keep their reserved ratio. Checked in the browser. Owner: Claude.

## Out of scope

- Loading the entries lazily from the server (an app with thousands of documents).

## Outcome

Built as specified. Proof: `tests/pyhx/components/test_document_viewer_start_and_files.py` (start page in pager, title, thumbnail and eager images; fallbacks; `selected`; switcher entries, groups, greyed-out entries, previous/next, position) and the sample page "Open at a page", checked in a browser at 1280 px and 390 px: opens at page 9 with the mark selected and in view; typing filters; ↑/↓ move; Esc closes, returns the focus to the button and keeps the mark selected; a click outside closes; at phone width the dropdown spans the toolbar with 44 px entries.

Deviation: opening at a page, and keeping the current thumbnail in view, now scroll only inside the viewer (page column, thumbnail rail); before, `scrollIntoView` also scrolled the page around a viewer embedded in a longer page. Smooth scrolling from the pager, thumbnails and linked content is unchanged.

Open: the entries are rendered all at once; loading them from the server is left for an app with thousands of documents.
