# T-019 Timeline: plan

## Findings

- **F1** `slider` already supports two thumbs with labels and fires `input` / `change` on its hidden inputs; the timeline reuses it.
- **F2** Component scripts are loaded by the skeleton and initialise on `DOMContentLoaded`, `htmx:afterSwap` and `htmx:load`.
- **F3** `drawer_content(header_controls=…)` holds the sample's pager; `pyhx.drawer.js` returns the focus to the element that opened the drawer.
- **F4** The skeleton (`timeline()` without parameters, the `timelines` fragment anchor) is used only by the components sample.

## Deviations

None yet.

## Branching

`feature/timeline`, one PR (`feat(timeline): …`), reviewed by the developer before merging.

## Steps

1. **Server side:** `TimelineEvent`, `TimelineCategory`, `TimelineQuery`, `timeline(...)` with validation; tests of the markup and defaults. Proves R1, R6, R7, R9 (server part), R11 (marked texts).
2. **Browser side and CSS:** `pyhx.timeline.js`, `timeline.css`. Proves R2–R5, R8–R10 together with step 3's browser check.
3. **Sample, docs, translations:** the sample page with a drawer route and its test, docstring, de/it/fr, `poe check`; browser check at 1280 and 390 px; screenshots in `screenshots/`; PR published. Proves R10–R12.

## Risks

- Placement may need tuning at small widths; the four places can become two rows per side.

## Proof per requirement

| Requirement | Step | Proof |
| --- | --- | --- |
| R1 | 1 | component tests |
| R2–R5 | 2, 3 | browser check of the sample |
| R6, R7 | 1, 3 | component tests, browser check |
| R8 | 2, 3 | sample drawer test, browser check |
| R9 | 1, 3 | component tests, browser check |
| R10 | 3 | browser check |
| R11 | 3 | `poe check` |
| R12 | 3 | sample page test, screenshots |
