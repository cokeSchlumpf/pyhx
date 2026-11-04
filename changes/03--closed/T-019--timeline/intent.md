# T-019 Timeline

## Problem

Apps on pyhx can't show many dated events on a time axis. The `chronicle` lists entries one below the other, which hides how they spread over time; the `timeline` primitive is an empty skeleton. An app that wants to show the course of a record over a year (a few hundred events, many on the same few days, some of them periods) has to build its own axis, units, overlap handling and range control in its own CSS and JavaScript.

The first use is an app on pyhx that shows the course of a record from its documents: about 180 dated findings over a year, in nine categories, up to 25 on one day, some with an end date, some of them flagged as contradicting others.

## Proposed outcome

- `c.timeline` (replacing the skeleton) renders events on a horizontal axis whose units adapt to the shown span and the available width (years, quarters, months, weeks, days).
- Each event is a dot on the axis with a line to a round icon above or below it, wherever there is room; events whose icons would overlap are combined into one marker with their number, so nothing overlaps at any width.
- Events have a category (label, colour, icon); chips with counts toggle which categories are shown, with "Default" and "All".
- A range slider (the existing `slider` with two thumbs) over a strip of events per month sets the shown span; "Whole period" resets it.
- Events with an end date also show as a bar along the axis; flagged events draw their marker in the warning colour.
- A marker opens the app's content for its events in the drawer (the app gives the URL), so the details stay app-specific; the focus returns to the marker.
- Optionally the shown categories and span are kept in the page's URL.
- Works with the keyboard and at phone width; texts in en, de, it and fr.
- The components sample shows it with generic data and a drawer per marker; design reviewed on the developer's design canvas.
- Deliberately not: zooming with the mouse wheel or dragging the axis, vertical layout, export, editing events.

## Affected users and systems

- **App developers on pyhx:** get a timeline component; the empty skeleton is replaced (it rendered only a placeholder, so nothing real breaks).
- **End users:** see the course of a record at a glance and open the details of each point.

## Constraints

- Additive (a `feat`, minor release on `versions/1`); the skeleton had no parameters, so replacing it doesn't break callers.
- Follows the CSS authoring conventions (`docs/decisions/2026-05-27-1436--css-authoring-conventions.md`) and the pattern of `slider` for server-rendered state plus a small script.
- Generic: no terms or data of the first app in pyhx, its docs or samples.

## Open questions

None.
