# T-014 Progress bar fixes: spec

## Requirements

### Stripes

- **R1** A bar with `working=True, motion="stripes"` shows its stripes across the whole width of the fill, in every size, appearance and design; they keep moving as before, and stand still with reduced motion.
- **R2** The sheen (`motion="sheen"`) keeps a single band that does not repeat.

### No spinner on the track

- **R3** A waiting bar (`value=None`) and a working bar show no spinner or other mark of Pico's `aria-busy` style on or before the track.
- **R4** The track keeps `aria-busy="true"` while waiting or working; the markup and the API of `c.progress_bar` don't change.

### Proof

- **R5** Unit tests in the style of T-013 check the CSS rules of R1–R3; `poetry run poe check` and `poetry run poe docs-build` pass; the components sample shows the fixed bars (screenshots before and after, desktop and phone width).

## Design

Both flaws come from Pico, which pyhx bundles in the layer `pico` below the layer `pyhx` (`pyhx.css`: `@layer pico, pyhx, templates`). A rule of `progress-bar.css` therefore wins over Pico regardless of specificity, but only for properties it sets.

- **Stripes (R1, R2):** Pico's reset sets `background-repeat: no-repeat` on every element; the stripes rule `.hx-progress-bar--stripes .hx-progress-bar__fill` doesn't set it, so the 16.97 px tile is drawn once. The rule gets `background-repeat: repeat`. The sheen rule keeps its explicit `no-repeat`.
- **Spinner (R3, R4):** Pico's `[aria-busy=true]:not(input, select, textarea, html, form)::before` gives the track a `::before` with the loading icon (`content: ""`, 1em square, inline-block), clipped by the track's `overflow: hidden` to a mark at the start. A new rule `.hx-progress-bar__track[aria-busy="true"]::before { content: none; }` removes the pseudo-element. It is in the layer `pyhx`, and its specificity (0,2,1) is also above Pico's (0,1,2), so it holds when an app loads Pico unlayered.

## Alternatives considered

- **Drop `aria-busy` from the track:** removes the spinner, but screen readers would no longer hear that the bar is busy (T-013, R4).
- **Move `aria-busy` to the root element:** Pico's spinner would then appear before the label or the whole component instead.
- **Fix it in the reset of pyhx (`background-repeat: repeat` everywhere):** changes every other background in pyhx and in apps; the fix belongs to the component.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Non-breaking fix, markup and API unchanged | R4, design (CSS only) |
| CSS conventions, both designs, sizes, appearances, reduced motion | R1, R3, design |
| No JavaScript, no new dependency | Design (two CSS declarations) |

## Open questions

None.

## Areas of concern

1. **Seam of the moving stripes** (R1): with the tile repeating, the animation (`background-position` by one period, 16.97 px) must loop without a jump; checked in the browser. Owner: Claude.

## Out of scope

- A live indicator for pills, or a standalone activity indicator: a separate, later change, designed first (the developer moved it out of this change).
- Other uses of `aria-busy` in pyhx or apps: Pico's spinner stays where it is meant to show (e.g. a busy button).

## Outcome

Implemented as specified, with these findings (from the plan, removed at close-out):

- **F1** Pico is imported in the layer `pico`, below `pyhx`, so each fix only sets the property Pico sets; the spinner rule also outranks Pico's selector by specificity, for apps that load Pico unlayered.
- **F2** The components sample (`/progress-bar`) already shows a striped and a waiting bar; no sample change was needed.
- **F3** The spinner mark showed on every busy track (sheen and pulse too), not only on waiting bars; the one rule removes it everywhere.
- **F4** Checked in the browser: the fill of a striped bar computes `background-repeat: repeat`, the stripes loop without a jump (frames at 0 and 0.8 s match), every busy track's `::before` computes `content: none` with `aria-busy="true"` kept, and with reduced motion the stripes stand still. The canvas design has no own rules for either; it was not checked separately in the browser.
- **F5** The browser kept the old `@import`ed stylesheet across reloads; clearing its cache was needed to see the fix. Apps upgrading pyhx may need a hard reload during development.

Screenshots (`screenshots/`, components sample, plain design; animations paused at the same moment):

- Stripes: [before](screenshots/app-shell--progress-bar-stripes--before.png), [after](screenshots/app-shell--progress-bar-stripes--desktop.png); phone width [before](screenshots/app-shell--progress-bar-stripes-phone--before.png), [after](screenshots/app-shell--progress-bar-stripes--phone.png).
- Waiting bar: [before](screenshots/app-shell--progress-bar-waiting--before.png), [after](screenshots/app-shell--progress-bar-waiting--desktop.png); phone width [before](screenshots/app-shell--progress-bar-waiting-phone--before.png), [after](screenshots/app-shell--progress-bar-waiting--phone.png).

Rollout: PR #53 (`fix: progress bar stripes and busy spinner (T-014)`), released with the next patch release of pyhx on `versions/1`. Apps that work around the two flaws with their own rules (`background-repeat: repeat` on the striped fill, `content: none` on the busy track's `::before`) can drop them after upgrading.

Open after this change: a standalone activity indicator (the pulsing mark first proposed for pills), as a separate change designed first (Michael).
