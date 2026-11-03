# T-014 Progress bar fixes: plan

## Findings while planning

- **F1** Pico is imported in the layer `pico`, below `pyhx` (`src/pyhx/static/css/pyhx.css`), so the fixes only have to set the two properties Pico sets; specificity matters only for apps that load Pico unlayered.
- **F2** The components sample (`/progress-bar`, `samples/components/pages/progress_bar.py`) already shows a striped bar (section "Motion") and a waiting bar (section "Modes"); no sample change is needed for the screenshots.
- **F3** T-013 tests CSS by reading `progress-bar.css` as text (`test_styles_stop_the_motion_for_reduced_motion`); the new tests follow that style.

Deviations from the spec:

None.

## Branching

Branch `fix/progress-bar-fixes`, draft PR #53, published at close-out. The developer waived the review stops up to the published PR (autonomous run).

## Steps

### 1. Fix the CSS

- Before screenshots of the components sample (striped and waiting bars, desktop and phone width).
- `background-repeat: repeat` in `.hx-progress-bar--stripes .hx-progress-bar__fill`. **R1, R2**
- `.hx-progress-bar__track[aria-busy="true"]::before { content: none; }`. **R3, R4**
- Proof: tests in `tests/pyhx/components/test_progress_bar.py` check both rules and that the sheen keeps `no-repeat`; the existing tests show the markup is unchanged; `poetry run poe check`. **R5**

### 2. Check in the browser and take the after screenshots

- Run the components sample, check with Playwright: the fill of a striped bar repeats its tile (`getComputedStyle(...).backgroundRepeat`), the stripes loop without a jump, the waiting track's `::before` has `content: none`; reduced motion stops the stripes. **R1, R3, R5**
- After screenshots, desktop and phone width.

## Risks

- **Stale screenshots:** the screenshot tool sometimes returns an old frame after a DOM change; each image is checked against the page and retaken if needed.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 1 test, step 2 browser check |
| R2 | Step 1 test |
| R3 | Step 1 test, step 2 browser check |
| R4 | Existing markup tests of T-013 (step 1) |
| R5 | Steps 1 and 2, screenshots |
