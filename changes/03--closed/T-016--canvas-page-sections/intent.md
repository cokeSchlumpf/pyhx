# T-016 Page sections in the canvas design

## Problem

In the canvas design a `DataPage` has its title on the canvas and its table in a white card (T-006). A page with more than one table has no such pattern: `page_section` keeps the look of `AppShell` (a grey sticky band with a line, a glow between sections), and a `DataTable` inside a section gets no card, because the card rule only matches a table directly in the content column. An app page with several lists (case-sight's usage overview) then looks different from every `DataPage`, or the app copies the card styling into its own CSS.

## Proposed outcome

- In the canvas design, `page_section` is a heading on the canvas, like the canvas page header: title left, actions right, no band, no line, no glow, not sticky.
- A `DataTable` directly in a section's content is the same white card as the table of a `DataPage`, with its search bar and footer.
- Apps build pages with several tables from `page_header`, `page_section` and `DataTable`, without CSS of their own.
- `samples/canvas_layout` shows it on a new page `/page-sections`; the layouts guide describes the pattern.
- Not part of this change: the default design (`AppShell` keeps its sticky section bands), new components.

## Affected users and systems

- **PyHX (library):** `page-section.css` and `canvas-shell.css` (styles only, no API change).
- **Samples and docs:** `samples/canvas_layout`, `docs/guides/layouts.md`.
- **Apps:** case-sight's usage page (its T-016) uses the pattern.

## Constraints

- Non-breaking: markup and API stay; only the canvas design changes.
- The default design looks as before.

## Open questions

None. Decided by the developer in the review of case-sight's usage page ("we should be always using the same patterns", "Extend pyhx").
