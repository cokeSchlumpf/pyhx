# T-005 Form controls for the canvas design: plan

## Findings while planning

- **F1** `tests/samples` has no folder for `canvas_layout`; its tests are unit tests of sample models. Rendering tests with FastAPI's `TestClient` exist under `tests/pyhx/core` (e.g. `templates/test_design.py`); the forms page test follows them.
- **F2** Pico sets some of the variables the design needs on the element, not on `:root`: `--pico-outline-width` on text controls (focus ring 1 px), `--pico-border-width` on checkboxes and radios (2 px) and switches (3 px). Tokens on `:root` don't reach them; `pyhx/elements/form.css` sets them in the canvas scope (R3, R6).
- **F3** The worktree needs its own virtual environment (`virtualenvs.in-project = true`): the environment of the main checkout imports `pyhx` from the main checkout's `src`.
- **F4** The pages of `samples/canvas_layout` are in German (dossier, navigation); the forms page is too.
- **F5** "Before" screenshots of the forms page can only be taken once the page exists; step 1 adds the page with today's styles and takes them then.

Deviations from the spec:

- None.

## Branching

Branch `feature/canvas-form-controls`, draft PR #23. The developer asked to take the change to the final pull request without pausing; each step is committed and pushed on its own, and the PR description lists the steps done.

## Steps

### 1. Forms page in the canvas sample, before screenshots

- `samples/canvas_layout/forms.py`: case form (`DataForm`) in a card, states grid, compact correction form in the aside of a `split_layout`; router included in `main.py`, link in `_modes()`. **R15**
- `tests/samples/canvas_layout/test_forms.py`: the page renders with status 200 and contains the case form, controls with `aria-invalid`, `readonly`, `disabled`, a switch and the aside form. **R15**
- Before screenshots (today's styles) of the forms page and of the forms page of `samples/components` (`AppShell`). **R17, R14**
- Proof: `poetry run poe check`; screenshots.

### 2. Controls

- `themes/canvas.css`: Pico form and primary tokens, switch colours, `--hx-color-danger-700`; `pyhx/theme.css`: `--hx-color-danger-700`. **R1–R6**
- `pyhx/elements/form.css` (new, imported in `pyhx.css`): text size, hover, focus ring width, read-only, disabled, checkbox and radio size and border width, all in `[data-hx-design="canvas"]`; error state restated. **R1–R6, R13**
- Proof: states grid of the forms page in the browser, every state checked against the spec; contrasts measured with computed styles; `poe check`.

### 3. Fields, buttons, segment control

- `form_field.css`: label and help text typography, error colour, spacing in the canvas scope. **R7–R9**
- `button.css`: radius, heights of `md` and `sm`, primary colour in the canvas scope. **R10, R11**
- `segment-control.css`: checked fill and focus outline in the canvas scope. **R12**
- Proof: forms page in the browser (computed heights, colours, spacing); `poe check`.

### 4. Documentation, after screenshots, checks

- `docs/guides/layouts.md`: form controls in the canvas section. **R16**
- After screenshots of the same pages; the `AppShell` screenshot compared pixel by pixel with the one of step 1. **R14, R17**
- Screenshots committed to `design/canvas-form-controls-screenshots`, linked in the PR. **R17**
- Proof: `poetry run poe check`, `poetry run poe docs-build`; image comparison.

## Risks

- **Pico state rules hidden by the `pyhx` layer:** each state of the grid is checked in step 2 (error border on hover and focus, validation icons).
- **Unscoped rule reaches the default design:** every rule sits under `[data-hx-design="canvas"]`; the pixel comparison of step 4 catches a leak.
- **Screenshots differ for reasons outside the change (fonts, animation):** same viewport, same browser, fonts loaded before the shot.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 2, states grid, computed styles |
| R2 | Step 2, contrast of the computed border colour against white, `#FAFAFA`, `#EEEEEE` |
| R3 | Step 2, focused control in the grid |
| R4 | Step 2, error controls in the grid (rest, focus) |
| R5 | Step 2, read-only and disabled controls in the grid |
| R6 | Step 2, checkboxes, radios, switches in the grid |
| R7 | Step 3, computed label styles |
| R8 | Step 3, help texts in the grid, contrast of the error colour |
| R9 | Step 3, measured distances in the case form |
| R10 | Step 3, computed button heights next to a control |
| R11 | Step 3, primary buttons in the grid |
| R12 | Step 3, segment control in the grid |
| R13 | Steps 2–3, case form (`DataForm`) and component controls on the forms page |
| R14 | Step 4, pixel comparison of the `AppShell` forms page |
| R15 | Step 1, `tests/samples/canvas_layout/test_forms.py` |
| R16 | Step 4, `poe docs-build` |
| R17 | Steps 1 and 4, screenshots in the PR |
