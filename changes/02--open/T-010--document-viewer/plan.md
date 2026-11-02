# T-010 Document viewer with annotations: plan

## Findings while planning

- **F1** `pyhx.components.view_model` is a neutral package (it depends on nothing in `data`, `primitives` or `layouts`); the data types of the viewer fit there as `view_model/document_viewer.py` (Q2). They import only htpy (for the `Attribute` type of `attrs`) and `Color`/`Appearance`, which keeps the package neutral.
- **F2** Component scripts are loaded on every page by `Skeleton` (`core/templates/skeleton.py`, one `<script>` per `pyhx.*.js`); component styles are `@import`ed by `static/css/pyhx.css` into the `pyhx` layer. The viewer follows both, so apps need no extra `<link>` or `<script>` (the sample's own copies go away).
- **F3** `layouts/__init__.py` re-exports each layout component and `components/__init__.py` re-exports those; `c.document_viewer` is added in both, the data types only in `view_model/document_viewer.py` (not in `view_model/__init__.py`, so `c.Mark` etc. don't appear).
- **F4** The `/full` page of `samples/canvas_layout` has no test yet; R33 adds one.
- **F5** The sample's example pages reuse `samples.components._snippets.extract_region` for the code shown; it is plain source slicing and stays as is.
- **F6** New texts of the component are extracted from `src/pyhx` into `src/pyhx/locale` (`python -m pyhx.i18n update --package src/pyhx --catalogs src/pyhx/locale --domain pyhx --locales de,it,fr`); the check in `poe check` fails until de, it and fr are translated.

Deviations from the spec:

- **D1** The examples and the guide import the data types as a module, `from pyhx.components.view_model import document_viewer as vm`, instead of `vm = c.document_viewer.view_model`: mypy accepts a variable bound to a module for attribute access but not in type annotations (`list[vm.MarkStyle]` fails with `name-defined`). `c.document_viewer.view_model` stays as a shortcut for code without annotations (R5 unchanged).

## Branching

Branch `feature/document-viewer` in the developer's pyhx checkout; one pull request `feat: add a document viewer with annotations`, a draft until close-out, then published with screenshots. The developer waived the review stop after each step for this change (up to the published PR); each step is committed on its own.

## Steps

### 1. View model of the document viewer

- `src/pyhx/components/view_model/document_viewer.py` with `Document`, `DocumentPage` (optional `width`/`height`, `aspect_ratio`, A4 fallback), `PageBadge`, `Mark`, `MarkStyle`, `MarkLook`, `Note`, `Annotation`, `BoundingBox`, `Point` (frozen dataclasses, validation, `from_pixels`), taken from the draft of the sample. **R5, R6, R7**
- Proof: `tests/pyhx/components/view_model/test_document_viewer.py` (fractions, out-of-page boxes, `from_pixels`, sizes given/missing/one/not positive, immutability).

### 2. The component, its CSS and script

- `src/pyhx/components/layouts/document_viewer.py`: the singleton `document_viewer` (root with context, `toolbar`, `back`, `title`, `pager`, `zoom`, `fit`, `spacer`, `thumbnails`, `pages`, `sidebar`, `view_model`), exported as `c.document_viewer`. **R1, R2, R3, R8–R11, R13–R15, R17–R21, R27**
- `static/css/pyhx/components/layout/document-viewer.css` (imported in `pyhx.css`, layer `pyhx`, conventions of the CSS decision) and `static/js/pyhx.document-viewer.js` (loaded by `Skeleton`). **R4, R12, R16, R22–R26, R28, R29**
- Texts marked and translated (de, it, fr). **R30**
- Proof: `tests/pyhx/components/test_document_viewer.py` (composition, toolbar standard/custom, fixed/following title, groups, badges, marks/notes with `attrs` and order, sidebar, errors, sync and async rendering of `toolbar()`, `Skeleton` loads the script, `pyhx.css` imports the style); `poe check` incl. the i18n check.

### 3. The sample on the released API

- `samples/document_viewer` uses `c.document_viewer` and `c.document_viewer.view_model`; the draft module and the sample's copies of the viewer's CSS and script are removed; the code shown imports `pyhx.components`. **R31**
- Proof: `tests/samples/document_viewer` (every page, groups, badges, notes with `attrs`, page images and notes routes); a browser run through every page (no script errors; stepping through a kind, a pin's `hx-get`, thumbnail jump without flicker, A4 fallback corrected on load, phone width without horizontal scroll).

### 4. The viewer in the canvas sample

- `/full` of `samples/canvas_layout` shows a document viewer with thumbnails and a sidebar instead of the three placeholders; the module docstring is updated. **R33**
- Proof: a test in `tests/samples/canvas_layout` for `/full`; screenshot.

### 5. Guide

- `docs/guides/document-viewer.md` (composition, data, toolbar, marks and notes, linking, phone width; links the sample) in the mkdocs nav under "Building Apps". **R32**
- Proof: `poe docs-build` (strict).

### 6. Screenshots and the full check

- Screenshots from the samples in `screenshots/` (`document-viewer--<page or state>--<desktop|phone>.png`, plus the existing before shot of `/full`); full `poe check` and `poe docs-build`. **R16, R22, R28** (visual proof), all requirements (regression)
- Proof: the screenshots, linked from the Outcome of the spec and the PR.

## Risks

- **Rendering the standard toolbar within the context:** covered by tests for sync and async rendering (step 2).
- **Pinch zoom on real devices:** cannot be tested here (no device); simulated touch events in the browser run, and the Outcome lists the device test as open.
- **The sample's code drifting from the API:** the code shown is cut from the running pages, which are tested.
- **Visual differences in the default design:** the viewer is built for the canvas design; the default design is checked once by rendering the basic example under `AppShell` in a test (no layout assertions).

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 2: composition tests, part outside a viewer |
| R2 | Step 2: viewer without documents; step 1: ids in the types |
| R3 | Step 2: parts render; step 6: screenshots |
| R4 | Step 3: example pages in fixed-height boxes; step 4: `/full` in `CanvasShell(mode="full")` |
| R5 | Step 1: view-model tests |
| R6 | Step 1: geometry tests |
| R7 | Step 1: size tests; step 3: browser run (A4 corrected, lazy loading) |
| R8 | Step 2: standard toolbar test |
| R9 | Step 2: custom toolbar test; step 3: `/toolbar` |
| R10 | Step 2: fixed/following title tests; step 3: browser run (title follows the second document) |
| R11 | Step 2: pager markup; step 3: browser run (counter per document, buttons disabled at the ends) |
| R12 | Step 3: browser run (zoom steps, fit, place kept) |
| R13 | Step 2: buttons are `hx-button--ghost` with `aria-label`; `back` is a link |
| R14 | Step 2: spacer rendered; step 3: `/toolbar` screenshot |
| R15 | Step 2: pages markup (headings with 2+ documents, lazy images); step 3: browser run |
| R16 | Step 3: browser run (counter changes once on a thumbnail jump, follows scrolling) |
| R17 | Step 2: group tests, `aria-current`; step 3: browser run |
| R18 | Step 2: badge tests |
| R19 | Step 2: mark markup (look, colour); step 6: screenshots |
| R20 | Step 2: note markup and order; step 6: screenshots |
| R21 | Step 2: `attrs` on marks and notes; step 3: `hx-get` from a pin in the browser |
| R22 | Step 3: browser run (spotlight, toggle, Esc); step 6: screenshot |
| R23 | Step 3: browser run (event detail logged) |
| R24 | Step 3: browser run (sidebar entries select, also after an HTMX swap of the sidebar detail) |
| R25 | Step 3: browser run (`aria-pressed` on linked entries) |
| R26 | Step 3: browser run (`activate` from the marks page) |
| R27 | Step 2: sidebar test; step 6: screenshots |
| R28 | Step 3: browser run at 390 px; step 6: phone screenshots |
| R29 | Step 3: simulated touch pinch in the browser run; device test open (Risks) |
| R30 | Step 2: i18n check in `poe check` |
| R31 | Step 3: sample tests |
| R32 | Step 5: `poe docs-build` |
| R33 | Step 4: `/full` test |
| R34 | Steps 1–4: the tests named there |
