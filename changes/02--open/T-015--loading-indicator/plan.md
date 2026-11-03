# T-015 Loading indicator: plan

## Findings while planning

- **F1** `c.button` is an inline-flex row with `align-items: center` and a gap, so a mark passed in its label list (`c.button([label, c.loading_indicator(...)])`) is centred by the button itself; the solid variant has the class `hx-button--solid`.
- **F2** `.hx-pill__label` is `inline-flex` with `align-items: center` but no gap; the mark inside it needs the gap rule of the spec.
- **F3** `nav_item` takes a plain text label, so the navigation example of the samples is a small list of links in the sample, not the shell's navigation.
- **F4** Pico's rules that reach every element are `box-sizing: border-box` and `background-repeat: no-repeat` on `*, ::before, ::after`; neither matters for shapes drawn with `background-color` and borders. Its `[aria-busy=true]` spinner is avoided by not using `aria-busy`.
- **F5** `vertical-align: middle` centres on half the x-height, so in running text (a link in the navigation) the mark sat 1.3px low; `vertical-align: calc(0.5cap - height / 2)` (with the mark's height as a token per kind) puts its centre at half the cap height and measures within 0.05px.
- **F6** The mark's `aria-label` becomes part of the accessible name of a button or link it stands in (the solid button read "Saving Saving"): the docs and the sample choose a label that reads on from the text ("Import" + "running") or give the button its own `aria_label`.
- **F7** Measured in both designs after the change: every mark animates (57 of 57); the centre of the mark is within 0.4px of its text's centre in the header, pill, buttons, table cells and navigation; the visible gap between a button's label and the outermost painted part of its mark (the ripple's ring at its largest) equals the button's gap (7px plain, 8px canvas); with reduced motion emulated no animation runs and every mark keeps its size; the spinner in the solid primary button is white on a 30 % white ring.

Deviations from the spec:

- **D1** Design update by the developer during step 3 ("Can we add some spacing to the loading indicator within the button?"): the ripple's box is as big as its ring (twice the dot), the dot (`::before`) and the ring (`::after`) are centred in it, and the ring grows to 2 instead of 3. New requirement **R12**: every kind keeps its motion inside its own box, so the gap next to the mark is the visible spacing.
- **D2** The mark centres in running text by `vertical-align` on the cap height (F5), not `middle`.

## Branching

Branch `feature/loading-indicator`, draft PR #54. Autonomous run: no review stops between steps (developer's waiver); each step is committed and pushed after `poetry run poe check`.

## Steps

### 1. Component, CSS and unit tests

- `loading_indicator.py`, its exports, `loading-indicator.css` and its import in `pyhx.css`. **R1–R8, R10**
- Proof: `tests/pyhx/components/test_loading_indicator.py` (markup, role, label, no `aria-busy`, classes per kind, size and appearance, reduced-motion rules, solid-button and pill rules, the CSS import). **R11**

### 2. Samples

- `samples/components/pages/loading_indicator.py` with `showcase()` (kinds, sizes, appearances, when to use which, in use), the page and the home link; `samples/canvas_layout/loading.py` with `/loading-indicators` and its home link. **R9**
- Proof: `tests/samples/components/test_loading_indicator_page.py` for both apps. **R11**

### 3. Browser check and screenshots

- Run both samples, check in Playwright: every kind animates, the mark's centre against its text line's centre (within 1px) in the in-use examples in both designs, nothing moves with reduced motion emulated, the spinner in the solid button is visible. **R3–R8**
- Screenshots of the new page in both designs at 1280×800 and 390×844, animations paused at a fixed moment, in `screenshots/`.
- Proof: the measurements (recorded under Findings) and the screenshots.

## Risks

- **Centring off by a pixel in running text:** measured in step 3; fixed in the CSS if it is more than 1px.
- **A stale screenshot frame:** every image is read back and retaken if it doesn't match.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1, R2 | Step 1, unit tests |
| R3 | Step 1, unit tests; step 3, animations running |
| R4 | Step 1, unit tests; step 3, solid button |
| R5 | Step 3, measurements |
| R6 | Step 1, unit tests; step 3, reduced motion |
| R7 | Step 1, unit tests; step 3 |
| R8 | Step 3, screenshots |
| R9 | Step 2, sample tests |
| R10 | Step 1, docstring; `poe docs-build` |
| R11 | Steps 1–2, `poe check` |
| R12 | Step 1, unit tests (ripple box, keyframes); step 3, measured gaps |
