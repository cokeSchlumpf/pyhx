# T-012 Modal dialogs: plan

## Findings while planning

- **F1** Both page templates put `header`/`main` (and in `AppShell` the menu toggles, side panel, backdrop labels and footer) and then the two drawers, the notifications and the error template as direct children of `<body>`. `inert` can therefore be set per child of `<body>`, skipping `.hx-dialog`, `.hx-drawer`, `.hx-notifications`, `template` and `script`.
- **F2** `drawer_select` and `drawer_radio` open the popup drawer (`--hx-z-sidepanel` + 10/20), so they are above a dialog at `--hx-z-dialog` (100) without any change.
- **F3** `pyhx.drawer.js` handles Escape on `document` and calls `preventDefault`; a drawer counts as open until the response of its close button arrives. The dialog's Escape handler checks for an open drawer itself and skips handled events, so the order of the two listeners doesn't matter.
- **F4** htmx 2.0.4 cancels the native submit when a `button` with `hx-post` inside a `form` is clicked. But Enter in a text field "clicks" the form's first submit button, and `c.button` renders `<button>` without `type`: the header's close button would be that first button. The close button gets `type="button"`, and `pyhx.dialog.js` cancels any native `submit` of the dialog's form, so Enter triggers the first action (htmx) and never a page navigation.
- **F5** There is no browser test runner; JS and CSS are tested by reading the sources (`test_drawer.py`). Behaviour is checked by hand in the samples with Playwright (MCP), as in T-010.
- **F6** `RequestContext.user` is `AnonymousUser` for anonymous requests, never `None`; the guide checks with `isinstance(user, AnonymousUser)` (fixed in the spec's guide draft).

Deviations from the spec:

- **D1** The translation of the close button's label (step 3) is done in step 1: `poe check` fails on a missing translation, and every step's commit keeps it green. Step 3 remains for texts added later.
- **D2** `dialog()` takes an optional `content` (spec R2: `dialog(*, id)`): the templates render the mount with the dialog the page is delivered with, and a custom template can do the same.

## Branching

Branch `feature/modal-dialogs`, draft PR #49. The developer waived the review after each step for this change: the steps are committed and pushed one by one, the PR description follows them, and the change ends with the published (not merged) PR with screenshots, samples and the guide.

## Steps

### 1. The dialog component

- `components/layouts/dialog.py`: `DIALOG_CONTENT_ID`, `dialog`, `dialog_content` (form with header, section, footer; `open`, `aria-modal`, `aria-labelledby`; close button `type="button"` with `_p("dialog", "Close")`, posting to `close_dialog` or `close_url`), `close_dialog` fragment, `open_dialog_htmx_attributes`; exported from `pyhx.components.layouts` and `pyhx.components`. **R1–R7, R10, R16**
- `static/css/pyhx/components/layout/dialog.css` (imported by `pyhx.css`): mount, backdrop at `--hx-z-dialog`, open state by `:has(> dialog[open])`, scroll lock, phone width; canvas look through tokens. **R8, R17, R18**
- `static/js/pyhx.dialog.js` (loaded by the skeleton): `inert` on the other children of `<body>`, focus in and back, Escape like the close button (only without an open drawer and with a close button), no backdrop click, `cancel` and native `submit` cancelled. **R8, R9, R11, R14, R15**
- Proof: `tests/pyhx/components/test_dialog.py` (rendering open/closed/closable/required, actions inside the form, close fragment, open attributes; CSS and JS rules read as text); `poe check`.

### 2. Page templates

- `CanvasShell` and `AppShell` take `dialog_content: SyncOrAsyncValue[y.Node | None] = None`, resolve it per full page load, and render `dialog(...)` after the drawers with the result. **R12, R13**
- Proof: tests in `tests/pyhx/page_templates/` (mount always rendered, empty by default; open when the callable returns a dialog; sync and async callables); existing template tests unchanged.

### 3. Translations

- `poetry run python -m pyhx.i18n update …`, translate the new entries (de, it, fr). **R19**
- Proof: the i18n check of `poe check`.

### 4. Samples

- `samples/canvas_layout/dialogs.py`: page "Dialogs" with "Show dialog" buttons for the required notice (error when the confirmation is missing, "Don't show this again", answer echoed in a notification), a confirmation, and a dialog with a `drawer_select`; linked from the index. **R20**
- `samples/components/pages/dialog.py`: page "Dialog" (AppShell) with a notice and a confirmation and their code (`# docs:` regions); linked from the home page. **R20**
- Proof: `tests/samples/canvas_layout/test_dialogs.py` and `tests/samples/components/test_dialog_page.py` (pages render without an open dialog, fragments open and close it, the error and the notification).

### 5. Guide

- `docs/guides/dialogs.md` from the spec's draft, final; nav entry under "Building Apps". **R21**
- Proof: `poe docs-build` (strict).

### 6. Check in the browser and screenshots

- Both samples by hand (Playwright): open, Tab stays in the dialog, Escape with and without a drawer, required dialog ignores Escape and backdrop clicks, error replaces content and keeps focus inside, focus returns, phone width. **R8–R11, R14, R15, R17, R18**
- Screenshots `screenshots/<template>--dialog-…--<desktop|phone>.png` in the change folder for the PR.

## Risks

- **`inert` misses something:** content an app appends to `<body>` after the dialog opened stays usable; noted in the guide; checked by hand.
- **Morph and focus:** when an action's response replaces the content, idiomorph may move focus to `body`; `pyhx.dialog.js` puts focus back into the dialog if it left it, checked in step 6.
- **Escape in browsers that close dialogs themselves:** a non-modal `<dialog>` gets no `cancel` on Escape; the handler on `document` decides alone, the `cancel` listener is a safety net.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1, R2, R4–R7, R10, R16 | Step 1, `test_dialog.py` |
| R3 | Step 1 (`hx-swap-oob`), step 4 sample tests, step 6 |
| R8, R9, R11, R14, R15 | Step 1 (JS/CSS rules), step 6 by hand |
| R12, R13 | Step 2, template tests |
| R17, R18 | Step 1 (CSS), step 6 screenshots |
| R19 | Step 3, i18n check |
| R20 | Step 4, sample tests |
| R21 | Step 5, `poe docs-build` |
| R22 | Steps 1, 2, 4 |
