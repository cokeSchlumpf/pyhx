# T-007 Inline editing of single values: plan

## Findings while planning

- **F1** `HeadlessForm`'s submit fragment wraps both `model_validate` and the submit handler in one `try … except ValidationError`, so a `ValidationError` raised by `save` is already shown at the field (R7) without a change to `HeadlessForm`.
- **F2** The form id of a `HeadlessForm` layout is the layout's choice (`wrapper_div_id` is only a suggestion), so the inline form can carry a per-item id and still be morphed out of band.
- **F3** Fragment handlers run with a `RequestContext`, so `RequestContext.get_request()` gives the layout callback and the submit handler the `key` of the query string.
- **F4** The pyhx scripts are loaded by `Skeleton` (`core/templates/skeleton.py`), the bundled htmx is 2.0.4 with the morph extension; component CSS is imported from `static/css/pyhx.css` into the `pyhx` layer.
- **F5** `form_field` forwards extra keyword arguments to the control, so `aria_labelledby` can point a single control at the item's label (R5).

Deviations from the spec:

- None so far.

## Branching

Branch `feature/inline-edit` from `main`, one pull request. The developer asked for the steps to be implemented without a review between them; the pull request is opened only after the developer has seen the result.

## Steps

### 1. Component

- `src/pyhx/components/data/inline_edit.py` with `InlineEdit[T]`, exported from `pyhx.components.data` and `pyhx.components`: display render, edit fragment, form layout on `HeadlessForm`, submit handler, key in the query, item ids. **R1, R2, R3, R4, R5, R6, R7, R8, R9, R13**
- Proof: `tests/pyhx/components/test_inline_edit.py` through a `TestClient` of a small `WebApp`: display markup and button, edit fragment, valid save (out-of-band display with the saved value), invalid save (form with the error at the field and the input kept), `ValidationError` from `save`, key escaping and round trip, no cancel fragment.

### 2. Script and styles

- `static/js/pyhx.inline-edit.js` (open, cancel, groups, keys, focus), loaded by `Skeleton`; `static/css/pyhx/components/data/inline_edit.css` imported in `pyhx.css`. **R10, R11, R12, R14, R15**
- Proof: a test that the skeleton loads the script and that `pyhx.css` imports the styles; the keyboard, focus and group behaviour is checked in Chromium with a Playwright script (step 4).

### 3. Samples

- `samples/canvas_layout`: in-memory store and four `InlineEdit` values in "Extrahierte Angaben" (group per card), an editable value with a hint in the aside. `samples/components/pages/inline_edit.py` (AppShell), linked from the home page. **R16, R17**
- Proof: `tests/samples/canvas_layout/test_dossier.py` (the dossier renders the editable values, a save changes the store and the page); `tests/samples/components/test_inline_edit_page.py` (page renders).

### 4. Browser check and screenshots

- Playwright script against both samples: screenshots (before, display, edit, error, saved, aside, 390px, AppShell) and the keyboard checks (Enter saves, Esc cancels, opening a second item closes the first, focus returns). Screenshots on the orphan branch `design/inline-edit-screenshots`. **R10, R11, R12, R14**
- Proof: the script's assertions pass; every screenshot looked at.

### 5. Guide

- `docs/guides/editing.md`: edit drawer, detail page, inline, with the `InlineEdit` API; in the mkdocs navigation. **R18**
- Proof: `mkdocs build --strict` passes.

## Risks

- **htmx events after out-of-band swaps:** focus after save relies on `htmx:load` for the swapped item; checked in step 4, fallback is `htmx:afterSettle` on the document.
- **Duplicate ids of `form_field` help texts:** two open forms with the same field name; one per page by default (spec, concern 1).

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 1, construction and route tests |
| R2 | Step 1, display tests |
| R3 | Step 1, button test |
| R4 | Step 1, edit fragment test; step 4 screenshot |
| R5 | Step 1, form tests |
| R6 | Step 1, valid save test |
| R7 | Step 1, invalid save and `save` error tests; step 4 screenshot |
| R8 | Step 1, no cancel route; step 4 Esc check |
| R9 | Step 1, key round trip test |
| R10 | Step 4 focus checks |
| R11 | Step 4 key checks |
| R12 | Step 4 group check |
| R13 | Step 1, tests without drawer; step 3 samples |
| R14 | Step 4 screenshots incl. 390px |
| R15 | Step 2 review of the CSS (no sizes) |
| R16 | Step 3 sample test; step 4 screenshots |
| R17 | Step 3 sample test; step 4 screenshot |
| R18 | Step 5 docs build |
| R19 | Steps 1 and 3 |
