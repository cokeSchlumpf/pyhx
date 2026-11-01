# T-006 DataPage and drawer in the canvas design

## Problem

A `DataPage` works inside `CanvasShell`, but it looks and partly behaves like the default design. Tried in `samples/canvas_layout` (branch `feature/canvas-data-page-sample`, pages `/data-page` and `/data-page-detail`):

- When the edit drawer is open, the page header (title, "Filter & Sort", create button) and the table header are drawn above the drawer and its backdrop and cover the first form fields. Editing the first fields is hard; it looks broken.
- The page header is the grey band of `AppShell` instead of a title on the canvas, and the table stands on the canvas without a card, unlike every other content of the canvas design.
- The drawer keeps Pico's layout: buttons at full width stacked under the form, a full-width red delete button, no fixed footer, so in a long form the actions scroll away.
- Drawers and asides are narrow, but there is only one size of fields and buttons. T-005 left the compact size (32 px fields, 28 px buttons, label to the left) out of scope as "a later change if needed"; the design for drawers and asides needs it.

Apps on the canvas design (case-sight first) can't use `DataPage` for their lists and record forms without these gaps showing.

The target look is drafted on the design canvas "DataPage im CanvasShell" (https://claude.ai/artifact/5FmCxN9D8dG5cQVoLxqeE6): the list, the compact edit drawer, and when to use drawer, detail page or inline editing. It builds on the form controls of T-005 (design canvas "Casesight Form Controls").

## Proposed outcome

- An open drawer and its backdrop are above everything on the page except the top bar; nothing of the page shows through or covers the drawer, in both designs.
- In the canvas design, a `DataPage` shows its breadcrumbs, title and actions on the canvas and its table in a card, without code changes in apps.
- In the canvas design, the edit and create drawers of `DataPage`/`DataSection` (and `DataFormDrawer` used on its own) have a header with title and close button, a scrolling body, and a fixed footer: delete as a quiet danger action on the left, cancel and submit on the right.
- Fields and buttons have a compact size for narrow areas (drawers, asides) as drafted: 32 px fields, 28 px buttons, label to the left of the field with a fixed width, stacking on narrow screens.
- Accessibility as in T-005: contrast of borders and text, visible focus; focus moves into the drawer when it opens and back when it closes; Esc closes the drawer.
- `samples/canvas_layout` shows it on its DataPage pages; the pull request shows screenshots before and after.
- Not part of this change: inline editing of single values (T-007), quick filters and search (T-008), new table features.

## Affected users and systems

- **PyHX (library):** canvas styles of the page header, data table, drawer and form; possibly a size option on form components and the drawer's markup (footer).
- **Samples:** `samples/canvas_layout` (DataPage pages from the sample branch), tests in `tests/samples`.
- **Documentation:** `docs/guides/layouts.md` (canvas design).
- **Apps on the canvas design** (case-sight): lists and drawers change their look with the next pyhx release.
- **Apps on the default design** (beleglotse, cross-border-rules): only the stacking fix reaches them.

## Constraints

- The default design (`AppShell`) doesn't change, except for the stacking fix.
- The Python API of `DataPage`, `DataSection`, `DataForm` and `DataFormDrawer` stays compatible; new options only with defaults that keep today's behaviour.
- Builds on T-005 (tokens, form controls, button sizes); this branch is stacked on `feature/canvas-form-controls` until T-005 is merged.
- CSS follows the decision on CSS authoring conventions (`docs/decisions/2026-05-27-1436--css-authoring-conventions.md`).
- Accessibility: WCAG 2.2 AA as in T-005.

## Open questions

Answer below each question; leave **Answer** empty to accept the proposal.

### Q1 How does a form become compact?

**Proposal:** Through its place, not a parameter: forms inside a drawer or in the aside of a `split_layout` are compact in the canvas design; a size option (`size="sm"`) on `form_field` and `DataForm` lets a form elsewhere opt in or a drawer form opt out. Apps get the drafted look without code changes.

**Answer:** Ys.

### Q2 Label to the left in compact forms?

**Proposal:** Yes, as drafted: label to the left in a fixed column (about 128 px) where the form is at least about 360 px wide, above the field when narrower. Full-size forms keep the label above (T-005).

**Answer:** yes.

### Q3 Delete in the drawer footer

**Proposal:** Delete moves into the footer as a quiet danger action (text button) on the left and keeps today's confirmation; no full-width red button.

**Answer:** Yes.
