# T-006 DataPage and drawer in the canvas design: plan

## Findings while planning

- **F1** The canvas sample's DataPage form has no "Eingang" field: `DataForm._render_field` renders a `DateField` only when the value is a `datetime`, so a `date` field is skipped. Not part of this change; noted for the developer.
- **F2** The table shows dates as `3/15/26` in a `de-CH` browser; date formatting by locale belongs to the i18n stream (`feature/i18n`), not to this change.
- **F3** `AppShell` hides the stacking bug only because `main > .hx-sticky` is `position: sticky` (a stacking context at level 0, before the drawer in the DOM); any page header or sticky table outside it would show the bug there too.
- **F4** `pyhx.drawer.js` only closes a drawer on a backdrop click; there is no focus handling and no Esc yet (R3 is new code, not a fix).

Deviations from the spec:

- none yet

## Branching

Branch `feature/canvas-data-page-look`, stacked on `feature/canvas-form-controls` (T-005, PR #23, not merged yet); the sample commit 8f68de9 of `feature/canvas-data-page-sample` is cherry-picked. The developer asked for all steps without a review pause; each step is committed and pushed, and the pull request is prepared (not opened) at close-out.

## Steps

### 1. Drawer stacking, closed state, focus and Esc

- `drawer.css`: `z-index` on the open drawer (popup one step above), backdrop limited to the drawer's top and bottom offsets, closed panel moved out by its width plus shadow. **R1, R2**
- `drawer_content`: `tabindex="-1"` on the panel; `pyhx.drawer.js`: focus into the panel on open, back on close, Esc closes the topmost open drawer. **R3**
- Proof: unit test of the panel's `tabindex`; screenshots of the canvas and `AppShell` drawers (page header and table header below the backdrop, top bar and footer undimmed, no strip at the right edge when closed); a Playwright check of focus and Esc.

### 2. Page header and table card on the canvas

- `page-header.css` canvas rules; `canvas-shell.css` card and cell rules for a table directly in the content column, container padding 0 there; white secondary buttons in the page header actions. **R4, R5, R6**
- Proof: screenshot of `/data-page` against the draft; `samples/app_shell_layout` `/data-page` unchanged.

### 3. Drawer header and footer on the canvas

- `DataFormDrawer.render_drawer`: BEM classes on wrapper, cancel and delete slots; `drawer.css` canvas header and close button; `data_form.css` canvas footer grid, delete as text button, 28 px buttons, white cancel. **R6, R7, R8, R9, R13**
- Proof: test of the drawer markup (classes, delete slot); screenshots of edit, create and error drawers, a long form scrolled with the footer visible; delete confirmation still opens; keyboard focus visible on the delete text button.

### 4. Compact form size

- `form_field`: label text in `span.hx-form-field__label`, `size` → `data-hx-size`; `DataForm(size=)` → `data-hx-size` on the form; `DataFormDrawer(size=)` passed through. **R12, R14**
- `form_field.css`, `data_form.css`, `drawer.css`/`split-layout.css`: compact controls, label column by container query, one column for compact `DataForm`s. **R10, R11**
- Proof: tests of `size` and the label span; screenshots of the drawer (label left), the phone drawer (label above) and the `/forms` aside.

### 5. Sample, documentation

- Sample test extended (drawer footer classes in the edit drawer); `docs/guides/layouts.md` canvas section. **R16, R17**
- Proof: `pytest`, `ruff`, `mypy`; docs read through.

Screenshots (R18) are taken at close-out, before and after, and pushed to `design/canvas-data-page-look-screenshots`.

## Risks

- **Grid with `display: contents` in the footer:** checked in Chromium screenshots; Firefox and Safari support `display: contents` on these elements since years; buttons keep their roles.
- **Container queries on the drawer section and aside:** `container-type: inline-size` needs a width that doesn't depend on content; both get theirs from the layout (drawer max 480 px, aside 22 rem).
- **Shared drawer CSS reaches `AppShell`:** only the stacking, closed-state and focus changes are unscoped; checked by the `AppShell` screenshot.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 1 screenshots, both designs |
| R2 | Step 1 screenshots of the closed list |
| R3 | Step 1 test and Playwright check |
| R4 | Step 2 screenshot |
| R5 | Step 2 screenshot |
| R6 | Steps 2 and 3 screenshots |
| R7 | Step 3 screenshot |
| R8 | Step 3 test and screenshots |
| R9 | Step 3 screenshots, delete confirmation |
| R10 | Step 4 screenshots |
| R11 | Step 4 screenshots (desktop, phone, aside) |
| R12 | Step 4 tests |
| R13 | Step 3 focus check, contrast values in the spec |
| R14 | Steps 3–4 tests, full test suite |
| R15 | `AppShell` screenshots before and after |
| R16 | Step 5 tests |
| R17 | Step 5 docs |
| R18 | Close-out screenshots |
