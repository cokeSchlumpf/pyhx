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

## Outcome

Implemented as specified, with these deviations and findings (from the plan, removed at close-out):

- **D1** R5's sticky header: a `DataPage` table has its own scroll container (`table_scrollable=True`), so its header sticks inside that container, not below the top bar; on the canvas the container isn't height-limited, so the header scrolls with the page. Unchanged from before; not part of the look.
- **D2** The hidden table toolbar sits above the table, and with the page header tighter on the canvas it covered the create button and took its clicks. In the canvas card it takes pointer events only while the pointer is on the table.
- **D3** The canvas theme sets the drawer backdrop to the text colour at 32 % (`--hx-color-overlay-dark`), as the draft; the default theme keeps its value.
- **D4** Compact labels wrap balanced (`text-wrap: balance`) with the first line centred on the control, so a long label ("Versicherte Person *") wraps to two even lines instead of leaving the marker alone.
- **F1** Root cause of the stacking bug: the open drawer is `position: fixed` without a `z-index`, a stacking context at level 0, so the sticky page header (90), table header (70) and top bar (70) were drawn above it. `AppShell` hid it only because its `main > .hx-sticky` wrapper is a sticky stacking context at level 0, earlier in the DOM.
- **F2** The 360 px of R11 are measured on the place (the drawer panel), so a drawer on a 390 px phone keeps the label on the left (342 px for the form, enough for the 128 px column).
- **F3** `AppShell` renders as before: screenshots of the DataPage and its drawer differ only by the removed shadow strip at the right edge (R2) and by compositing noise of at most 3/255 in the header gradient.
- **F5** The screenshots are kept in `screenshots/` next to this spec, named `<template>--<page>--<variant>.png`; `-before` is `main` with the sample pages, the others are after the change (and its amendment): [list before](screenshots/canvas-shell--data-page--before.png) and [after](screenshots/canvas-shell--data-page--desktop.png), [edit drawer before](screenshots/canvas-shell--data-page--edit-before.png) and [after](screenshots/canvas-shell--data-page--edit.png), [create drawer](screenshots/canvas-shell--data-page--create.png), [validation error before](screenshots/canvas-shell--data-page--error-before.png) and [after](screenshots/canvas-shell--data-page--error.png), [short viewport](screenshots/canvas-shell--data-page--edit-short.png), [delete confirmation](screenshots/canvas-shell--data-page--delete-confirm.png), [phone drawer before](screenshots/canvas-shell--data-page--edit-phone-before.png) and [after](screenshots/canvas-shell--data-page--edit-phone.png), [phone list](screenshots/canvas-shell--data-page--phone.png), [aside before](screenshots/canvas-shell--forms--aside-before.png) and [after](screenshots/canvas-shell--forms--aside.png); for the amendment see A-F3.
- **F4** Not part of this change, seen while testing: `DataForm` renders a `DateField` only for `datetime` values, so the sample's `date` field "Eingang" is missing from the form; dates in the table show as `3/15/26` in a `de-CH` browser (the i18n stream).

Rollout: pull request from `feature/canvas-data-page-look` against `main` (T-005, #23, and the i18n work, #20, were merged into the branch before close-out), released with the next minor version of `pyhx` (`feat:`); screenshots in `screenshots/` next to this spec (F5). Apps on the canvas design (case-sight) get the new look when they update `pyhx`; apps on the default design get the stacking fix, the closed-drawer fix and the focus handling.

Open after this change: F4 (owner: developer); the drawer subtitle and Esc hint of the draft (Q4) if wanted; checking case-sight's DataPages after its `pyhx` update (owner: developer).

## Amendment 1: label position, form size on DataPage, drawer footer in both designs

Added after the review of the pull request (#29), decided with the developer; implemented in the same pull request. It revises the intent's constraint "the default design doesn't change, except for the stacking fix": the drawer's footer, scrolling and scroll lock (R22, R23) reach `AppShell` too.

### Requirements

- **R19** `DataPage` and `DataSection` take `form_size` (`"sm" | "md" | None`) and `form_label_position` (`"top" | "left" | None`), default `None`, and pass them to the edit and the create drawer (`DataFormDrawer` → `DataForm`) as `size` and `label_position`.
- **R20** `form_field`, `DataForm` and `DataFormDrawer` take `label_position` (`"top" | "left" | None`, default `None`), in both designs: `"left"` puts the label in a 128 px column left of the control while the field's own cell is at least 360 px wide and above it in a narrower cell; `"top"` keeps it above; `None` keeps today's behaviour (above; in a compact form of the canvas design left where the cell has room). This replaces R11's measurement on the place (drawer panel, aside) by a measurement on the field's cell.
- **R21** A label position keeps the form's `columns` and grid template areas: only a compact form without a label position shows one field per row (R11). Fields placed by template areas follow the per-cell rule of R20.
- **R22** In both designs, the drawer of `DataFormDrawer` keeps its header on top and its footer at the bottom while the form body scrolls: delete on the left as an underlined text button in the design's `danger-700`, cancel and submit side by side on the right. The default design keeps its colours (blue primary button), labels on top and the form's columns.
- **R23** In both designs, the page behind an open drawer doesn't scroll: neither when the drawer's content reaches its end nor when it fits. A page with a scrollbar doesn't shift sideways when a drawer opens.
- **R24** Tests cover size × label position × columns, the drawer and a main form, and the forwarding through `DataPage` and `DataSection`; the guide describes the label position. `samples/canvas_layout` shows a drawer form with `form_label_position="top"` and two columns (`/data-page-detail`, create) and a main form with `label_position="left"` (`/forms`).

### Design

- `label_position` renders `data-hx-label-position` on the field's wrapper (`form_field`) or on the `<form>` (`DataForm`); `variants.LabelPosition` is the type.
- `form_field.css`: a field with the left layout (its own or its form's `"left"`, or a compact canvas field without a position) is a size container (`container-type: inline-size`) and a wrapping flex row; `@container (min-width: 360px)` gives the label a 128 px basis and the help text the same indent. Only fields that can have the label left become containers, so a field in a flex row elsewhere keeps its width.
- `data_form.css`: the drawer footer grid of the canvas design moves out of the canvas scope; the canvas keeps its own spacing and 28 px buttons. The compact one-field-per-row rule excludes forms with a label position.
- `drawer.css`: `overscroll-behavior: contain` on the scrolling bodies, and `html:has(open drawer) { overflow: hidden; scrollbar-gutter: stable }`. CSS rather than script: it follows the open state the drawer already has (section with content), also for the popup drawer.

### Outcome

Implemented as amended, with these deviations and findings:

- **A-D1** An older rule for forms in drawers (`.hx-drawer .hx-data-form__actions div`, stacking the actions) had the same specificity as the footer rules and won in the default design; it now leaves `DataFormDrawer` out.
- **A-F1** The scroll lock is proven in the browser at 1280 × 480: without it the wheel over an open drawer scrolled the canvas page by 119 px and the `AppShell` page by 210 px, with it by 0 (both designs).
- **A-F2** Label positions checked in the browser: canvas edit drawer (432 px cells) left; phone drawer (342 px) top; create drawer with `form_label_position="top"` and two columns top (210 px cells); `AppShell` drawer top; `/forms` with `label_position="left"` left at 1440 px (524 px cells) and top at 700 px (306 px cells); the aside (312 px) top. With R20 the phone drawer now shows labels on top (F2 no longer holds). In the default design a form with `label_position="left"` lays out the same way.
- **A-F3** Screenshots of the amendment in `screenshots/`: [create drawer with labels on top and two columns](screenshots/canvas-shell--data-page-detail--create-top.png), [main form with labels left](screenshots/canvas-shell--forms--label-left.png), and the `AppShell` drawer before and after: [edit](screenshots/app-shell--data-page--edit-before.png) / [after](screenshots/app-shell--data-page--edit.png), [1280 × 480](screenshots/app-shell--data-page--edit-short-before.png) / [after](screenshots/app-shell--data-page--edit-short.png), [scrolled](screenshots/app-shell--data-page--edit-short-scrolled-before.png) / [after](screenshots/app-shell--data-page--edit-short-scrolled.png).
- **A-F4** Checkbox fields of `DataForm` are rendered by `checkbox_fieldset`, not `form_field`; their label stays on top with `label_position="left"`.

Open after the amendment: A-F4 if wanted; the branch `design/canvas-data-page-look-screenshots` (first screenshots, before F5) can be deleted after the merge.
