# T-022 Annotation navigation in the document viewer: plan

## Findings while planning

- **F1** The script already initialises viewers in content swapped in by htmx on `htmx:load` (`init(scope)`); the hidden categories are applied to linked elements there too.
- **F2** Marks and notes are `<button>`s with author CSS; `[hidden]` of the browser's style sheet loses against it, so `document-viewer.css` needs `[hidden] { display: none }` for both.
- **F3** The sample page "Marks" steps through marks of a kind with its own script (`activate`); it stays as the example of the JavaScript API. The new page shows the built-in pager.
- **F4** The sample's page images have filler lines (grey bars every 44 px from below the fields to y 1560); annotations over two lines and over two pages are drawn on them.
- **F5** In this shell `VIRTUAL_ENV` points to another project's venv; every `poetry` command for pyhx runs with `VIRTUAL_ENV` unset (`poetry env info -p` must print `pyhx/.venv`).

Deviations from the spec:

- **D1** Linked elements swapped in later get the hidden state on `htmx:load` (F1), not on `htmx:afterSwap`.
- **D2** Added while specifying the first user (CaseSight T-022, types in the URL as on its Timeline): `document_viewer(..., category_query=None)`; with a parameter name the browser writes the shown categories there (comma separated) after every change, like `TimelineQuery` of `c.timeline`. Without it nothing changes. Proven in step 2 (sample reads `?types=`, browser: written on toggle, restored on reload).
- **D3** Selecting an annotation by the pager scrolls the pages with `scrollIntoView` as before (T-018); in a viewer embedded in a longer page this also moves the page around it. Unchanged here; in a viewer that fills the window (`CanvasShell(mode="full")`) nothing else moves.

## Branching

Branch `feature/annotation-navigation`, draft PR #73. The developer waived the review stop after each step for this change (4 November 2026); each step is committed and pushed when its checks pass.

## Steps

### 1. View model and markup

- `Mark.annotation`, `Mark.category`, `Note.category`, `Mark.annotation_id`; categories without whitespace (validated). `_mark`/`_note` render the annotation id, `data-hx-document-category` and `hidden`; `document_viewer(..., hidden_categories=())` renders `data-hx-document-hidden`. `dv.annotation_pager(previous_label=None, next_label=None)` renders the buttons and "– / {total}" with the shown annotations counted on the server. **R1, R4, R5 (markup), R9**
- Proof: unit tests in `tests/pyhx/components/test_document_viewer_navigation.py` (shared annotation id, unchanged markup without the new parameters, hidden marks and notes, the root attribute, invalid categories, pager markup and total).

### 2. Script, CSS and the sample page

- Script: annotations of several marks (select, toggle, hover, scroll to the first), the order of annotations, previous/next and the position, categories (toggles, linked elements, event, `showCategory`, `next`, `previous`), revealing linked elements in their scrolling container. CSS for hidden marks and the position. **R2, R3, R5–R8, R10–R13**
- The sample page "Annotation list" (`samples/document_viewer/pages/annotation_list.py`) with a list grouped by category, toggles, the pager, an annotation over two lines and one over two pages. **R14**
- Proof: sample test (page renders, linked entries and toggles, shared ids); in a browser (Playwright) at 1280 px and 390 px: a click on a two-line annotation presses both marks; hover highlights both; next/previous run through in order with wrap and update "n / total"; a two-page annotation scrolls to its first mark; hiding a category hides marks and entries, skips them in the pager and clears a hidden selection; a click on a mark far down scrolls its entry into view in the sidebar without moving the page; the pages "Marks", "Notes", "Open at a page" and "Source picker" behave as before.

### 3. Guide and translations

- `docs/guides/document-viewer.md`: a section "Navigating annotations" (several marks, pager, categories, linked elements in view, the new API functions and event); the module docstring. New texts in de, it, fr. **R15**
- Proof: `poetry run poe check` green (ruff, mypy, tests, translations); the guide's code matches the sample.

## Risks

- **Ordering by inline position** (R6): the script reads `left`/`top` from the marks' style; the browser check covers it.
- **Scrolling in the sidebar** (R13): measured in the next animation frame, checked at both widths.
- **Source picker** shares the script: its annotations stay `inert`; checked in the browser.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 1, unit tests |
| R2 | Step 2, browser |
| R3 | Step 2, browser |
| R4 | Step 1, unit tests (markup unchanged); step 2, browser (other sample pages) |
| R5 | Step 1, unit tests; step 2, browser |
| R6 | Step 2, browser |
| R7 | Step 2, browser |
| R8 | Step 2, browser |
| R9 | Step 1, unit tests |
| R10 | Step 2, sample test and browser |
| R11 | Step 2, browser |
| R12 | Step 2, browser (console) |
| R13 | Step 2, browser at 1280 px and 390 px |
| R14 | Step 2, sample test |
| R15 | Step 3, `poe check` |
