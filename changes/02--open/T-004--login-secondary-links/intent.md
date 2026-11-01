# T-004 Secondary links of the login pages below the card

## Problem

The login pages of `addons/user_authentication` place their secondary links inconsistently. "Sign in with another method" is a subtle, grey, centred link below the card (`.hx-login__switch`). "Request a new link" on the page "Check your email" is a regular blue link inside the card, below the row with the "Sign In" button; there it looks lost and competes with the button. "Back to sign in" on the page "Login link not valid" has the same problem, and that page offers no clear way to get a new link. The page "Sign in" for a link opened on another device shows its button directly below the text, without the footer row the forms have. Users of every app with email login (e.g. case-sight on the canvas design) see this.

## Proposed outcome

- "Request a new link" on the page "Check your email" is shown below the card, in the style of "Sign in with another method" ("Didn't get it? Request a new link"); the card holds only the form.
- The page "Login link not valid" offers "Request a new link" as its primary button in the footer row of the card, and "Back to sign in" as a subtle link below the card.
- The page "Sign in" for a link from another device shows its button right-aligned in a footer row below a divider, like the forms.
- All secondary links of the login pages share one style (`.hx-login__switch`).
- The texts of the pages, the routes and the login behaviour don't change.

## Affected users and systems

- **PyHX (library):** `addons/user_authentication/_pages.py`, possibly `static/css/pyhx/components/layout/login.css`.
- **Tests:** the tests of the login pages.
- **Apps with email login** (e.g. case-sight): their login pages look different; nothing to change in the apps.

## Constraints

- No change of the public API; released as `fix:`.
- Looks right in both page templates (`AppShell`, `CanvasShell`) and on a phone.
- Follows the CSS authoring conventions (`docs/decisions/2026-05-27-1436--css-authoring-conventions.md`).
- `poe check` and `poe docs-build` pass.

## Open questions

None.
