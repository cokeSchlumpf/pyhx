# T-019 Timeline: spec

## Requirements

- **R1** `c.timeline` takes events (`TimelineEvent`: a key, a category, a start date, an optional end date, an accessible label, a warn flag) and categories (`TimelineCategory`: a key, a label, a colour, an icon, whether it is shown by default) and renders a horizontal axis with markers for the events of the shown categories within the shown span.
- **R2** The axis has ticks and labels in one unit chosen from the shown span and the axis' width: years, quarters, months, weeks or days, the coarsest that gives each tick at least about 68 px; labels use the page's language (`<html lang>`); the first tick of a year shows the year.
- **R3** A marker is a dot on the axis, a line and a round icon button in one of four places (near above, near below, far above, far below); no two icons overlap; events whose icons would overlap, or whose dots lie within 10 px, are combined. A marker of one category shows its icon and colour, with a badge of its number of events when it has more than one; a marker of several categories shows the number in a neutral circle.
- **R4** A marker with at least one warn event is drawn in the warning colour (dot, line and border) with an exclamation mark.
- **R5** An event with an end date also shows as a bar along the axis from its start to its end, clipped to the shown span.
- **R6** Below the axis a range slider (`slider` with two thumbs, "Start" and "End") sets the shown span within the bounds (by default the earliest and latest date of the events, extended by a month at each end); behind it a strip shows the number of events of the shown categories per month; "Whole period" resets the span. Moving the slider needs no request.
- **R7** Above the axis one toggle chip per category with its colour and its number of events in the shown span, plus "Default" and "All"; toggling needs no request. A line tells how many of all events are shown and in how many markers; without shown events the axis says so.
- **R8** A marker is a button that requests `open_url` with the keys of its events (repeated `key` parameter) into the drawer (as `open_drawer_htmx_attributes` does); closing the drawer returns the focus to the marker; the marker is shown as open while its drawer is.
- **R9** With `query` set, the shown categories and span are written into the page's URL (`history.replaceState`) under the given parameter names whenever they change; the app passes the initial categories and span, so a reload shows the same view.
- **R10** Chips, markers (in time order) and slider thumbs are reachable with Tab; Enter or Space opens a marker; the slider's keys are those of `slider`; touch targets are at least 40 px; the layout follows the component's width, also when it changes, and works at 360 px.
- **R11** Its texts are in en, de, it and fr.
- **R12** The components sample's Timeline page shows it with generic data (categories, periods, warn events, a drawer per marker with a pager) and explains the API with code snippets; the docstring documents the parameters.

## Design

```python
c.timeline(
    events=[TimelineEvent(key="e12", category="release", start=date(2026, 3, 2), label="Release 2.1, 2 Mar 2026")],
    categories=[TimelineCategory(key="release", label="Releases", color="#16a34a", icon="tag")],
    open_url="/timeline/events",
    shown=None,          # initial categories; default: each category's `shown`
    span=None,           # initial (start, end); default: the bounds
    bounds=None,         # default: earliest/latest date ± 1 month
    query=TimelineQuery(categories="types", start="from", end="to"),   # optional
    id="timeline",
)
```

- **Server** (`components/primitives/timeline.py`): renders `div.hx-timeline[data-timeline]` with the chips (`button` with `aria-pressed`), the summary line, the empty axis area, the slider (day numbers since 1970-01-01, step 1) with the density strip behind it, the events as JSON (`<script type="application/json">`), one `<template>` per category with its icon, the URL, the query names and the translated texts as `data-text-*` (plural forms as one/other).
- **Browser** (`static/js/pyhx.timeline.js`, loaded by the skeleton, initialised like `pyhx.slider.js`): keeps the state (shown categories, span) and renders the axis on every change of chips, slider (`input`) or width (`ResizeObserver`): ticks with `Intl.DateTimeFormat`, period bars, markers placed from left to right in the first of the four places whose last icon is at least 40 px away (else the event joins the marker before), counts, summary, the strip's highlight, `aria-valuetext` on the thumbs. Markers are buttons with `hx-get`, `hx-target="#drawer-content"`, `hx-swap="none"`, processed by `htmx.process`. Ticks and placement are pure functions on `window.PyhxTimeline`.
- **CSS** (`components/primitives/timeline.css`): a category's colour per marker as `--timeline--color`; the warning colours from the theme.
- **Sample**: a product's year (releases, incidents flagged as warn, sprints as periods, meetings, milestones) with a drawer per marker and a pager in `header_controls`.

## Alternatives considered

- **Layout on the server for a fixed width:** breaks on resizing and phones; every slider move would need a request.
- **Filtering on the server:** a request per chip; a few hundred events are small enough to send at once.
- **A popup at the marker instead of the drawer:** the drawer already exists, works on phones, and keeps the details app-specific.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Additive, minor release | R1 (replaces a parameterless skeleton) |
| CSS conventions, slider pattern | Design |
| Generic | R12 (generic sample data) |

## Open questions

None.

## Areas of concern

1. **Placement at narrow widths** (R3, R10): many events on one day at 360 px; combined markers instead of overlaps, checked in the browser at 1280 and 390 px. Owner: Claude.
2. **No JavaScript test runner** (R2–R10): ticks and placement are pure functions checked in the browser; the sample is the reference. Owner: Claude.

## Out of scope

- Zoom by mouse wheel or dragging, a vertical layout, export, editing events.

## Outcome

Implemented as specified, with these deviations and findings (from the plan, removed at close-out):

- **D1** `slider` gets a small hook: other scripts move its thumbs with a `hx-slider:set` event (values snapped, clamped and kept in order; `input` and `change` fire as if the user had moved them). "Whole period" uses it; nothing else in `slider` changed.
- **D2** Tick spacing is 68 px, or 48 px and then 40 px when that gives fewer than three ticks (narrow axes); on an axis under 480 px the first label carries its year only if no January tick shows one. Without this a phone showed a single label ("2026") for a year.
- **D3** The axis is 22rem high (not 20rem), so the far places below the axis keep clear of the tick labels at phone width.
- **D4** After the developer's review ("not nice spacing, the labels are not centred on the same line"): the chip row is a `role="group"`, which Pico styles as a joined button group (stretched children, margin); the timeline undoes that, the chips have one height (2rem) and even padding, and "Default" and "All" sit centred on the chips' line. The density strip is lighter (neutral-200, neutral-400 in the span).
- **D5** After the review ("a hover effect like pulse, just not pulsing; warning markers pulsing"): markers show a still ring in their colour on hover and focus; markers with a warning send out a pulsing ring (like the loading indicator's ripple) and keep a still ring when the system asks for reduced motion.
- **D6** After the review: the canvas layout sample has a timeline page too (`/timeline`, the course of a dossier in a card, with a drawer per marker), since the first app uses `CanvasShell`.
- **F1** `feather.replace()` doesn't reach into `<template>`: the script turns a category's Feather icon into SVG with `feather.icons[name].toSvg()`.
- **F2** The drawer's close button is swapped out with the drawer's content, so htmx events of the close don't reach the document; while a marker is open the script follows the drawer with a `MutationObserver`, to show the marker closed again.
- **F3** A period that began before the shown span puts its marker at the axis' start (it stuck out on the left before).
- **F4** Checked in the browser (components sample, `AppShell`) at 1280, 390 and 360 px: no two icons overlap, no icon leaves the axis, no tick labels collide, no horizontal scroll; the units change from quarters to weeks when the span is narrowed to six weeks; chips filter and update their counts; sprints show as bars; the busiest marker (4 events) opens the drawer with its pager; Esc closes it and the focus is back on the marker, shown closed; the URL follows chips and slider, and a reload restores the view. The canvas layout sample (`CanvasShell`) at 1280 and 390 px: no overlaps, no icon outside the axis, no horizontal scroll; chips and presets on one centre line in both designs; with reduced motion emulated the warning markers' ring stands still. Not checked: screen readers beyond the accessible names.

Screenshots (`screenshots/`): components sample: [desktop](screenshots/timeline--desktop.png), [desktop with drawer](screenshots/timeline-drawer--desktop.png), [phone](screenshots/timeline--phone.png), [phone with drawer](screenshots/timeline-drawer--phone.png); canvas layout sample: [desktop](screenshots/canvas-timeline--desktop.png), [phone](screenshots/canvas-timeline--phone.png).

Rollout: PR #65, released with the next minor release of pyhx on `versions/1`.

Open after this change: the app that asked for it shows the course of its records with the timeline (its own change).
