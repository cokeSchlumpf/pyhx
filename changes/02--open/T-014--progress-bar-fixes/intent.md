# T-014 Progress bar fixes

## Problem

`c.progress_bar` (T-013, release 1.8.0) has two flaws that a consuming app found in its first real use, and that the app currently works around with its own CSS:

- **Stripes show as a single stripe.** With `working=True, motion="stripes"`, only one stripe at the start of the fill is visible. The stripes are a `repeating-linear-gradient` in a 16.97 px tile, but Pico's reset (`*, ::after, ::before { background-repeat: no-repeat }`) stops the tile from repeating.
- **A spinner mark at the start of a waiting or working bar.** The track carries `aria-busy="true"` while it waits or works. Pico draws its loading spinner before every element with `aria-busy=true` (`[aria-busy=true]:not(input, select, textarea, html, form)::before`). In the 8 px track it is clipped to a small mark at the start, visible while waiting, when the travelling segment moves away from the start.

Every app that uses the stripes or a waiting bar sees them, and has to patch pyhx's look with its own rules.

## Proposed outcome

- A striped bar shows its stripes across the whole fill, moving as before.
- No spinner mark appears in a waiting or working bar; the track keeps `aria-busy="true"`, which is correct for screen readers.
- The sheen keeps its single, non-repeating band.
- Apps that work around the two flaws can drop their rules after upgrading.
- Deliberately not: any new option or other change to the progress bar; a live indicator for pills (a separate, later change).

## Affected users and systems

- **App developers on pyhx:** the stripes and waiting bars look as designed; workarounds become unnecessary.
- **End users:** see the intended motion and no stray mark.

## Constraints

- A non-breaking fix (`fix`, patch release on `versions/1`); markup and API stay the same.
- In pyhx's CSS, following the CSS authoring conventions; works in both designs (default and canvas), all sizes and appearances, and with reduced motion.
- No JavaScript, no new dependency.

## Open questions

None.
