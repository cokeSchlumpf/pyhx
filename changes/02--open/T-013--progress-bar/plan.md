# T-013 Progress bar: plan

## Findings while planning

- **F1** `metric_tile` is the pattern to follow: a `@component` function, `classnames` for the modifiers, its CSS in `static/css/pyhx/components/primitives/` imported by `pyhx.css` in layer `pyhx`, the canvas design overriding tokens under `[data-hx-design="canvas"]` (as `pill.css` does).
- **F2** The canvas theme has no own `--hx-color-primary`; its primary buttons use `--hx-color-text` (#171717), which the draft uses for the default bar.
- **F3** The slider's track colour is the token `--hx-slider--track-color` (neutral-300); the draft's canvas track is neutral-200, so the canvas block sets it.
- **F4** No page of `docs/` lists components; the components sample is their reference (spec, out of scope).

- **F5** (implementation) The reduced-motion rule first had a lower specificity than the motion rules and didn't stop them; found by emulating reduced motion in the browser, fixed by the same specificity (`.hx-progress-bar .hx-progress-bar__fill`).
- **F6** (implementation) `hx-grid` has no phone breakpoint; the sample lays its examples out with an auto-fit grid (three columns, one at phone width).

Deviations from the spec:

- None.

## Branching

Branch `feature/progress-bar`, draft PR #50 (`feat: progress bar`). The developer reviewed the design and waived the stops up to the published PR, which they review in the samples before it is merged.

## Steps

### 1. Component and styles

- `progress_bar.py`, exports, `progress-bar.css` with modes, motions, reduced motion, appearances, sizes and the canvas block. **R1–R8**
- Proof: `tests/pyhx/components/test_progress_bar.py` (attributes and classes per mode, motion, appearance, size; texts; accessible name; no head without texts; kwargs); `poetry run poe check`.

### 2. Samples

- `samples/components/pages/progress_bar.py` with the showcase and its code, linked from the home page; `samples/canvas_layout/progress.py` rendering it in the canvas design; tests in `tests/samples`. **R9, R10**
- Proof: sample tests; both samples run and are looked at in a browser at desktop and phone width (screenshots in `screenshots/`, compared with the draft); `poe check`, `docs-build`.

## Risks

- **Animations in screenshots:** a moving bar is captured at some frame; the screenshots are for the look, the movement is checked live.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 1: import and render tests |
| R2 | Step 1: aria attributes and fill width |
| R3 | Step 1: accessible name tests |
| R4 | Step 1: mode and motion classes, `aria-busy`; step 2: live check |
| R5 | Step 1: CSS contains the reduced-motion block; step 2: emulated reduced motion in the browser |
| R6 | Step 1: texts and bar-only tests |
| R7 | Step 1: appearance and size classes; step 2: screenshots |
| R8 | Step 2: screenshots in both designs and at phone width; kwargs test |
| R9 | Step 2: sample tests |
| R10 | Steps 1 and 2: `poe check`, `docs-build` |
