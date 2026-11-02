# T-012 Modal dialogs

## Problem

pyhx has drawers for forms (`data_form_drawer`), but no modal dialog. Apps need dialogs for things a user must see and answer before going on: a notice to confirm at the first sign-in (e.g. terms of use of a demo instance), a confirmation before a destructive or costly action, a short message that blocks the page until it is acknowledged. Without a component, each app builds its own markup, focus handling and htmx wiring.

## Proposed outcome

- A dialog component on the native `<dialog>` element: title, content (htpy nodes), and actions (buttons) in the look of the default design and the canvas design.
- Opened from the server: a page or fragment response can include a dialog that opens on load (e.g. right after sign-in), and a button can load a dialog as a fragment.
- Required dialogs: no close button, no closing by Escape or a click outside, until an action is chosen.
- An action posts to a fragment route, like a data form, and the response can close the dialog, replace its content (e.g. a validation error) or redirect.
- Optional content controls inside the dialog, e.g. a checkbox "Don't show this again", sent with the action.
- Accessible: focus moves into the dialog and returns afterwards, the title labels the dialog, it works with keyboard only and at phone width.
- Texts of the component translated in all languages of pyhx.
- A guide in `docs/guides/` and samples for a required notice and a confirmation.
