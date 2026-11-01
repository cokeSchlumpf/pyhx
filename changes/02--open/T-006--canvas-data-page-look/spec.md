# T-006 DataPage and drawer in the canvas design: spec

## Requirements

### Drawer stacking and behaviour (both designs)

- **R1** An open drawer (panel and backdrop) is drawn above all page content: the page header, sticky table headers, sticky section headers and the content itself. The top bar (and the footer of `AppShell`) stay visible above or beside it and are not dimmed; the backdrop covers exactly the area between them, as in the design draft. The popup drawer (`drawer_select`, `drawer_radio`, delete confirmation) stays above the primary drawer, and dropdowns inside a drawer above its content.
- **R2** A closed drawer leaves no trace on the page (today its shadow shows as a grey strip at the right edge of the viewport).
- **R3** When a drawer opens, keyboard focus moves into its panel; when it closes, focus returns to the element that opened it if that element is still on the page. Esc closes the topmost open drawer.

### Page header and table on the canvas

All requirements of this group and the next two apply to the canvas design (`data-hx-design="canvas"`) only.

- **R4** The page header of a `DataPage` (`page_header`) sits on the canvas: no band, background, bottom border or sticky position; breadcrumbs 13 px `neutral-600`; title in the page title role (32 px, semibold); actions at the end, aligned with the bottom of the title; left edge aligned with the content column; 16 px to the content below.
- **R5** A table that stands directly in the content column (the table of a `DataPage`) is shown in a white card: 12 px radius, 1 px `neutral-200` border. Header cells are 12 px, medium, `neutral-600` on white with a `neutral-200` line below and no column separators; body rows are separated by `neutral-150` lines. The table header stays sticky below the top bar.
- **R6** Neutral solid buttons in the page header actions (e.g. "Filter & Sort") and in drawers (e.g. "Cancel", the close button) are white with a `neutral-200` border in the drawer header and the 3:1 control border (`#878787`) elsewhere, like the secondary buttons of the design draft.

### Drawer on the canvas

- **R7** The drawer header has 20 px / 24 px / 16 px padding and a line below; the title is 17 px, semibold; the close button is a 32 px square icon button.
- **R8** The edit and create drawers of `DataPage` and `DataSection`, and `DataFormDrawer` used on its own, have a scrolling body (24 px inline padding) and a footer fixed at the bottom of the panel with a line above: the delete action (when present) on the left, cancel and submit on the right, 28 px buttons. However long the form, the footer stays visible.
- **R9** Delete is a quiet danger action: an underlined text button in `danger-700` (5.22:1 on white), no fill or border; it keeps today's confirmation in the popup drawer.

### Compact form size

- **R10** Form fields in a compact place are compact: 32 px single-line controls (inputs, selects, dropdowns), text 14 px, label 13 px medium `neutral-700`, help text 12 px 4 px below the control; fields 12 px apart. Compact places are a drawer and the aside of `split_layout`.
- **R11** In a compact place at least 360 px wide, the label sits left of the control in a 128 px column (12 px gap), help text below the control; narrower, the label sits above. A compact `DataForm` lays out one field per row, unless its model defines grid template areas.
- **R12** `form_field(..., size=...)`, `DataForm(..., size=...)` and `DataFormDrawer(..., size=...)` take `"sm"` or `"md"`, default `None`: `None` sizes by place (R10), `"sm"` makes the field or form compact anywhere, `"md"` keeps the full size in a compact place. In the default design the option has no visible effect.

### Compatibility, accessibility, sample, documentation

- **R13** Focus stays visible on every control and button of the drawer (focus ring of T-005; the delete text button gets an outline in the text colour); text and borders keep the contrasts of T-005 (WCAG 2.2 AA).
- **R14** The Python API of `DataPage`, `DataSection`, `DataForm`, `DataFormDrawer`, `drawer_content` and `form_field` stays compatible; new parameters have defaults that keep today's behaviour.
- **R15** Pages in the default design (`AppShell`) render as before, except R1–R3.
- **R16** `samples/canvas_layout` shows R4–R11 on its pages `/data-page` and `/data-page-detail` (from the sample branch) and on the aside of `/forms`; tests in `tests/samples` render them.
- **R17** The canvas section of `docs/guides/layouts.md` describes the DataPage look, the drawer footer and the compact size (by place, `size`).
- **R18** The pull request shows screenshots before and after: list, edit drawer, create drawer, drawer with a validation error, phone width, the forms aside, and the `AppShell` drawer.

## Design

**Root cause of the stacking bug (R1).** The open `.hx-drawer` gets `position: fixed` without a `z-index`. A fixed element always forms a stacking context, so the backdrop (`--hx-z-backdrop`, 60) and the panel (`--hx-z-sidepanel`, 200) only compete inside it; the drawer as a whole is painted at level 0 of the page. Every positioned element with a positive `z-index` outside it is drawn above it: the sticky page header (90), the sticky table header (70), the canvas top bar (70). `AppShell` hides the bug by accident: its `main > .hx-sticky` wrapper is `position: sticky` and so a stacking context at level 0 too, earlier in the DOM than the drawer, which keeps the page header and table header inside it. `CanvasShell` has no such wrapper.

Fix in `pyhx/components/layout/drawer.css`: the open drawer gets `z-index: var(--hx-z-sidepanel)` (the popup drawer one step more), so it is above the page header and below dropdowns of the page. The backdrop no longer reaches `inset: 0` but the drawer's own `top` and `bottom` (`--hx--drawer--top`, `--hx--drawer-bottom`, already set by both shells), so the top bar and the `AppShell` footer stay undimmed, as they were by accident before and as the draft shows. The closed panel moves out by its width plus its shadow (R2).

**Focus and Esc (R3).** `pyhx.drawer.js` (loaded by the skeleton for every page) watches the drawer panels with a `MutationObserver`. On the change from empty to filled it remembers `document.activeElement` and focuses the panel (`tabindex="-1"` on the `aside` of `drawer_content`, no focus outline on the panel itself); on the change back it restores focus if the remembered element is still connected. Esc clicks the close button of the topmost open drawer (popup first), the same path the backdrop click takes.

**Page header and table (R4–R6).** `[data-hx-design="canvas"] .hx-page-header` rules at the end of `page-header.css`, like `card.css` does. The table card lives in `page-templates/canvas-shell.css` (`templates` layer), selected as a table wrapper that is a child of a container directly in the content column (`.hx-canvas-shell__content > .hx-container > .hx-table__wrapper`, and the same under `.hx-canvas-shell__page` with a sidebar): a table inside a card or section keeps its look. The cell rules for header and rows are scoped the same way. The container's inline padding is set to 0 in the canvas content column so title and card align with the content edge.

**Drawer markup (R7–R9).** `DataFormDrawer.render_drawer` keeps its structure and adds BEM classes: `hx-data-form-drawer` on the wrapper, `hx-data-form-drawer__cancel` and `hx-data-form-drawer__delete` on the slots. The canvas rules in `pyhx/components/data/data_form.css` lay the wrapper out as a grid of two rows (body `minmax(0, 1fr)`, footer `auto`) and three footer columns (delete, cancel, submit); the form, the action containers and the `<hr>`s get `display: contents` or are hidden, so the field grid becomes the scrolling body and the submit button (inside the form) and the cancel and delete buttons (outside it) share the footer row. This keeps the submit inside the `<form>`: the validate round-trip morphs the form including the submit's disabled state, unchanged. The panel's `section` drops its own padding and scrolling for this content (`:has(> .hx-data-form-drawer)`). The default design ignores the classes and renders as before.

Drawer header, close button and the white secondary buttons: canvas rules in `drawer.css`, `button.css`.

**Compact size (R10–R12).** CSS in `form_field.css` and `data_form.css`, scoped to the canvas design. A compact field is a `.hx-form-field` inside `.hx-drawer` or `.hx-split-layout__aside` or `[data-hx-size="sm"]`, and not inside or carrying `[data-hx-size="md"]`. Compact controls get `--pico-form-element-spacing-vertical: 0.1875rem` (Pico's height formula then gives 32 px). The label-left layout uses a container query on a named container (`hx-compact`): the drawer section, the aside, and a compact `DataForm`'s `<form>`. The field becomes a grid with the areas `label control` / `label help`; for that `form_field` wraps the label text and the required marker of the `label` wrapper in `<span class="hx-form-field__label">` (the `div` wrapper already has a `<label class="hx-form-field__label">`); inline, so the default design looks the same. A compact `DataForm` grid gets one column and its cells span it; forms with template areas keep their layout.

`size` renders `data-hx-size` on the field's wrapper (`form_field`) or on the `<form>` (`DataForm`, stored on the instance so validate round-trips keep it); `DataFormDrawer` passes it to its `DataForm`.

**Sample (R16).** Cherry-picked from `feature/canvas-data-page-sample` (8f68de9): `samples/canvas_layout/data_page.py` and its test. The test is extended to check the drawer footer classes; a test of `form_field`/`DataForm` covers `size`.

## Alternatives considered

- **Raise the backdrop and panel z-indices instead of the container's:** they live inside the drawer's stacking context, so their values never reach the page; only a `z-index` on the container (or dropping `position: fixed` from it) works. Dropping it would change the open/close mechanics, which rely on the container covering the viewport.
- **Move the submit button out of the form (`form="…"` attribute) into a real `<footer>`:** cleaner markup and a focus order that matches the visual order, but the validate round-trip only re-renders the form, so the button outside would keep a stale disabled state; it needs a new out-of-band contract in `DataForm`.
- **Pass cancel and delete into `DataForm.render(actions=...)`:** the validate round-trip re-renders the form without the slot, so they would vanish after the first input.
- **A `<footer>` slot in `drawer_content`:** the same problem as above for the submit button; a later change if `DataForm` gets an external-actions mode.
- **Compact as a parameter only (no place):** apps would have to change code for the drafted look; rejected in the intent (Q1).
- **Label left by the field's own width:** a container query cannot change the grid of the container itself, and fields of a two-column form would each be too narrow; the place's width is what the intent asked for (Q2).

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Default design unchanged except the stacking fix | R15; every look rule scoped to `data-hx-design="canvas"`; R1–R3 apply to both; screenshot of the `AppShell` drawer (R18) |
| Python API compatible, new options with defaults | R12, R14 |
| Builds on T-005, stacked on `feature/canvas-form-controls` | Design uses the T-005 tokens, control borders and button sizes; PR base noted in R18 |
| CSS authoring conventions | Design: component rules in the `pyhx` layer with `[data-hx-design="canvas"]`, template rules in `canvas-shell.css`, concentric property order, tokens over literals |
| WCAG 2.2 AA as in T-005 | R3, R9, R13 |

## Open questions

The developer asked to take the change to the final pull request without stopping; the proposals below were taken as decided and are listed in the pull request for review.

### Q1 Focus handling and Esc in the default design too?

**Proposal:** Yes. It is behaviour of the shared `drawer` (one script for both designs), not look, and the default design's drawers lack it as much; splitting the script by design would be code for no gain.

**Answer:** Proposal taken (see above).

### Q2 The closed drawer's shadow at the right edge

**Proposal:** Fixed in both designs (R2): it is the same layering bug of the shared drawer, visible as a grey strip on every page.

**Answer:** Proposal taken (see above).

### Q3 Focus order in the drawer footer

**Proposal:** Accept the DOM order Save → Cancel → Delete while the footer shows Delete … Cancel Save (see Alternatives: the submit has to stay in the form). Tab order still reaches every action, the primary one first.

**Answer:** Proposal taken (see above).

### Q4 Subtitle and "Esc" hint in the drawer header and footer

**Proposal:** Not now: the draft's subtitle (e.g. case number and name) needs a new parameter and data from each app, the Esc hint a translated text; both are additions for a later change if wanted.

**Answer:** Proposal taken (see above).

### Q5 Compact DataForm with two columns

**Proposal:** A compact `DataForm` shows one field per row (R11), even if its model asks for `columns=2`: a drawer or aside has no room for two columns with labels on the left. Forms with grid template areas keep their layout.

**Answer:** Proposal taken (see above).

## Areas of concern

1. **Stacking against other overlays** (R1): the drawer at `--hx-z-sidepanel` is now above the `AppShell` mobile side panel and equal to the notifications (which come later in the DOM and stay above). Checked in the samples at phone width. Owner: implementer.
2. **`display: contents` in the drawer footer** (R8): removes the boxes of the form and its action containers. The form has no accessible name and so no role to lose; buttons keep theirs. Checked with the keyboard and in the screenshots. Owner: implementer.
3. **Changed markup of `form_field`** (R11): the label text gets a `<span>`; apps that style or test the label's text node directly could notice. Inline span, same look in the default design. Owner: implementer.
4. **case-sight changes its look on update** (R4–R11): its DataPages and drawers change with the next pyhx release. Intended; checked when case-sight updates pyhx. Owner: developer.

## Out of scope

- Inline editing of single values (T-007), quick filters and search above the table (T-008), new table features, the row count in the card footer of the draft.
- A subtitle in the drawer header and the Esc hint (Q4).
- A focus trap in the drawer.
- The look of the default design, except R1–R3.
