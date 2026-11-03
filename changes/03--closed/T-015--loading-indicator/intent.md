# T-015 Loading indicator

## Problem

Apps on pyhx can't show that something is happening right now without a bar or a text. The progress bar (T-013) shows how far a piece of work has got, but it needs room and a value; a pill says what state something is in, but it stands still. An app that wants a small mark next to a status pill in a header, in a button that leads to running work, in a table row whose document is being processed or in the navigation entry of a section where an import runs has to build its own animated dot with its own CSS, which doesn't follow the design, isn't announced to screen readers and keeps moving when the system asks for reduced motion.

The first use is an app on pyhx that shows its analysis jobs: "In progress" in the header of a record, a button to the running analysis, rows of documents that are being processed.

## Proposed outcome

- A component `c.loading_indicator` renders a small mark with no visible text that says "this is happening right now". It sits next to a label, inside or beside a pill, in a button, in a table row or in the navigation, and it stops when the work ends because the app no longer renders it.
- Five kinds, as in the reviewed design draft: a turning arc (spinner), a dot sending out a ring (ripple), a breathing dot (pulse), three dots in turn (dots) and three rising bars (bars). The docs say when to use which.
- The colours of pill and progress bar (`Appearance`) and the sizes `sm`, `md`, `lg`, each sized to sit on a text line of the size it goes with; the mark is vertically centred on that line, in a button too.
- It is announced to screen readers by a required label (`role="status"`), never by its motion alone.
- Nothing moves when the system asks for reduced motion, but the mark stays visible.
- It looks right in both page templates, `AppShell` (plain design) and `CanvasShell` (canvas design), on light backgrounds and inside a solid button.
- The components sample and the canvas layout sample show every kind, size and colour and the places it is used in.
- Deliberately not: a progress value (that is the progress bar), a text of its own, changes to pill, button or navigation, JavaScript.

## Affected users and systems

- **App developers on pyhx:** get a loading indicator; nothing they use today changes.
- **The app that asked for it:** shows its running analysis jobs with it.
- **End users and screen-reader users:** see and hear "this is running" the same way in every app.

## Constraints

- Additive and non-breaking (a `feat`, minor release on `versions/1`).
- Follows the CSS authoring conventions of pyhx (`docs/decisions/2026-05-27-1436--css-authoring-conventions.md`) and the structure of `progress_bar`.
- Pico's global rules must not reach it: its `background-repeat: no-repeat` on every element and its spinner on `[aria-busy=true]` (both found in T-014).
- Accessible: a label is required; the motion respects reduced motion.
- No JavaScript and no new dependency; it renders on the server, so htmx and server-sent events can swap it in and out.
- pyhx is public: no client names, URLs or screenshots.
- Process: the developer reviewed the design drafts ("I like all drafts. I would create a loading_indicator component which supports all different modes and colors. And we need to check it in both layouts (shell, and canvas)."); intent, spec, plan and steps run without acceptance stops up to the published PR, which the developer reviews in the samples and the PR before it is merged.

## Open questions

None. The design drafts (kinds, sizes, colours, reduced motion, in use) were reviewed by the developer.
