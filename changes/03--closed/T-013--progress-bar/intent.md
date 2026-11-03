# T-013 Progress bar

## Problem

Apps on pyhx can't show how far a piece of work has got. pyhx has a slider (`c.slider`, from the change "sliders and timeline", PR #3), which is an input: a track with a filled range, thumbs, hidden form inputs and pointer handling in `pyhx.slider.js`. It has no read-only counterpart: no bar that shows a value, with the semantics screen readers announce as progress (`role="progressbar"` or `<progress>`), in the look of the canvas design.

So every app builds its own: the sample of server-sent events (T-011) uses a native `<progress>` with sample CSS, which looks like the browser's bar and not like the design. The first real use is CaseSight's analysis panel (its change T-010): "Analysing 35 %", a bar, a translated stage label ("Extracting findings · page 1 of 3"), a rough time left; while the job waits in the queue, there is no value yet.

## Proposed outcome

- A component `c.progress_bar` shows a value between 0 and 1 as a filled bar on a track, with the accessible semantics of a progress bar (its value and an accessible name), in the look of the canvas design and of the slider's track.
- A bar with a value is either **static** (a value that stands still: a quota, a step reached) or **working** (work in progress, shown by a movement of the filled part while the value stays readable). The app chooses the movement: a sheen (a light band sweeps across the fill; the default), moving diagonal stripes, or a pulse; each has its purpose (calm, visible from afar, quiet).
- A bar without a value shows work whose amount is unknown yet (waiting, indeterminate), e.g. a job in the queue: a segment travels along the track.
- Nothing moves when the system asks for reduced motion (`prefers-reduced-motion`); a waiting bar then shows a faint full track.
- The component renders the bar with an optional label and value text above it (e.g. "Extracting findings" and "35 %") and an optional line below it (e.g. "page 1 of 3 · about 3 minutes left"), in the design's layout, like `metric_tile`; without texts it renders the bar alone. What the texts say is the app's.
- The bar takes the colours of the other components (`Appearance`: e.g. `success` when done, `danger` when failed) and the sizes of the design.
- The value is a `Pct` (the existing value type of `pyhx.components.view_model`), so apps pass `Pct.clamp(done / total)` or `Pct.of(35)`.
- The components sample gets a page with every variant and its code, and the guide or reference that lists the components mentions it.
- When this change is merged, the T-011 sample's job page uses `c.progress_bar` instead of `<progress>`.
- Deliberately not: a value the user sets (that is the slider), steps or a stepper, a circular progress, animations driven by JavaScript.

## Affected users and systems

- **App developers on pyhx:** get a progress bar; nothing they use today changes.
- **CaseSight (T-010):** shows the analysis progress with it.
- **pyhx T-011 (server-sent events):** its sample switches to the component before T-011 is closed.
- **End users and screen-reader users:** see and hear progress the same way in every app.

## Constraints

- Additive and non-breaking (a `feat`, minor release on `versions/1`).
- Follows the design and the CSS authoring conventions of pyhx (`docs/decisions/2026-05-27-1436--css-authoring-conventions.md`), shares the slider's tokens where they mean the same (track colour, rail height), and works at phone width.
- Accessible: announced as a progress bar with its value; a working or waiting bar is announced as busy; colour is never the only carrier of meaning; the motion respects reduced motion.
- Looks right in both page templates, `CanvasShell` (canvas design) and `AppShell` (plain design).
- Process: a design draft (both shells) is reviewed by the developer before the intent is accepted; after that, spec, plan and steps run without acceptance stops up to the published PR, which the developer reviews in the components sample and the PR before it is merged.
- No JavaScript and no new dependency; it renders on the server, so it can be swapped in by htmx and server-sent events.
- Texts pyhx itself adds (if any, e.g. a default accessible name) are marked for translation and translated into de, it and fr.

## Open questions

None.

The design draft reviewed with the developer: https://claude.ai/artifact/EPXcwYY2UDavzJk67nZZSe (canvas and AppShell design, in context, phone width).
