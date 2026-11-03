# T-016 Page sections in the canvas design: spec

## Requirements

- **R1** In the canvas design, a `page_section`'s header has no background, no backdrop blur, no bottom line and doesn't stick; its title is one step smaller than the page title, its actions are small secondary text or controls on the right.
- **R2** In the canvas design, stacked sections have a plain gap and no glow between them, and the section spans the page's content column (no gutter, no max width of its own).
- **R3** A `DataTable` rendered directly in a section's content gets the card of a `DataPage`'s table (border, 12 px radius, white background; search bar and footer as top and bottom rows of the card).
- **R4** A table's sticky header sticks below the top bar inside a canvas section, as on a `DataPage`.
- **R5** The default design (`AppShell`) is unchanged.
- **R6** `samples/canvas_layout` has a page `/page-sections` (page header, two sections with a `DataTable` each), linked from the overview and tested; the layouts guide describes the pattern.

## Design

- `page-section.css`: a block `[data-hx-design="canvas"] .hx-page-section…` after the default rules, as `page-header.css` does for the page header (T-006): gutter 0, no max width, `--hx-table--sticky-top: var(--hx-sticky-top)`, static header without band and line, title `--hx-text-lg`, actions 13 px neutral-600, content without inset.
- `canvas-shell.css`: the selector of the table card gets a second selector, `.hx-page-section__content > .hx-table__wrapper`, so both places share one rule set.

## Alternatives considered

- **Cards in the app's CSS:** duplicates the canvas card per app and drifts from pyhx.
- **One `DataPage` per table:** spreads an overview over several pages.
- **A new component for a titled table:** `page_section` already is the titled block below a page header; only its canvas look was missing.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Non-breaking, styles only | Design (CSS only) |
| Default design unchanged | R5, rules scoped to `[data-hx-design="canvas"]` |

## Open questions

None.

## Areas of concern

1. **Sections with other content than a table** (R1): text or cards in a section sit on the canvas without inset, as on a canvas page. Owner: developer.

## Out of scope

- Sticky section headers in the canvas design; the default design's sections.

## Outcome

Implemented as specified.

- **F1** `DataTable.render()` returns the `.hx-table__wrapper` itself, so the card rule matches a table passed directly as a section's `content`; a table wrapped in another element keeps the plain look.

| Page | Before | After |
| --- | --- | --- |
| `/page-sections` | [desktop](screenshots/before-page-sections-desktop.png), [phone](screenshots/before-page-sections-phone.png) | [desktop](screenshots/after-page-sections-desktop.png), [phone](screenshots/after-page-sections-phone.png) |

Rollout: the PR of this change, then a minor release; case-sight's T-016 updates to it.

Open after this change: nothing.
