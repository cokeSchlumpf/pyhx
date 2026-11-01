# T-004 Secondary links of the login pages below the card: spec

## Requirements

### Check your email

- **R1** The page `{login_path}/code` has no link inside its card; the card holds the text and the code form.
- **R2** Below the card, the page shows "Didn't get it? Request a new link" in `.hx-login__switch`; the link goes to the email method (`{login_path}?method=email`).

### Login link not valid

- **R3** The pages "Login link not valid" (`GET {login_path}/token` with an unknown or used link, and `POST {login_path}/token` that fails) show "Request a new link" as a primary button in the card's footer, linking to `{login_path}?method=email`.
- **R4** Below the card they show "Back to sign in" in `.hx-login__switch`, linking to `login_path`; there is no link inside the card.

### Sign in on another device

- **R5** The confirmation page of a link opened in another browser shows its "Sign In" button in the card's footer (right-aligned, below a divider), posting to `{login_path}/token` as before.

### Style

- **R6** Every secondary link of the login pages ("Sign in with another method", "Request a new link", "Back to sign in") is a `.hx-login__switch` paragraph below the card: small, grey, centred; the text around a link has the same grey.
- **R7** Texts, routes and the login behaviour don't change; the existing tests of the login pages pass unchanged except where they check the place of a link.
- **R8** The pages look right in `AppShell` and `CanvasShell` and at phone width.

### Tests

- **R9** `tests/pyhx/addons/test_email_login.py` covers R1–R5.

## Design

All changes are in `addons/user_authentication/_pages.py` and `static/css/pyhx/components/layout/login.css`.

- `_card(title, *body, heading=y.h1)` gets a keyword `footer: y.Node = None`; when set, it is rendered as `c.card.footer[footer]` after the section. The card component already draws the footer right-aligned and separates it from the section by a thin line (`card.css`, `.hx-card__footer`), the same look as the forms' divider and actions row.
- A helper `_switch(*content)` returns `y.p(class_="hx-login__switch")[content]`; `switch_link()` uses it, as do the code page (R2) and the message box (R4). It sits in the login column (`_login_box`) after the card, like the method switch today.
- `render_code_box` drops the link from the card and adds `_switch("Didn't get it? ", y.a(href=method_url(EmailTokenLogin.key))["Request a new link"])` after it (R1, R2).
- `message_box(title, text)` renders the card with `footer=c.button("Request a new link", appearance="primary", href=method_url(EmailTokenLogin.key))` and `_switch(y.a(href=login_path)["Back to sign in"])` after the card (R3, R4). `message_box` is only used by the token pages, which exist only with email login, so the email method is always available.
- The confirmation page passes its `c.button(..., hx_post=...)` as `footer=` instead of as part of the body (R5).
- `login.css`: `.hx-login__switch` gets `color: var(--hx-color-neutral-600)`, so the text around a link is grey too (R6); the comment says it is used below any login card.

## Alternatives considered

- **Link in the row of the button (variant A on the design canvas):** keeps the action near the form, but puts a second style of secondary link inside the card, next to the one below it on the email page.
- **A secondary button "Request a new link" in the form's actions row:** too prominent for an action most users never need, and `DataForm` would need an option for extra actions.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| No change of the public API, released as `fix:` | Design: private helpers in `_pages.py` only |
| Looks right in `AppShell`, `CanvasShell` and on a phone | R8; existing card and login column styles, checked with screenshots |
| CSS authoring conventions | Design: one property added to an existing rule, in its group |
| `poe check` and `poe docs-build` pass | R7, R9 |

## Open questions

None.

## Areas of concern

1. **Grey text on the grey canvas** (R6): `neutral-600` is already used for the switch link on the same background; the added text uses the same color. Checked on the screenshots. Owner: Michael Wellner.
2. **Apps that style or test the old markup** (R7): the link inside the card is gone; apps could have matched it in their own tests. Low risk, the markup was never documented. Owner: Michael Wellner.

## Out of scope

- The look of the forms themselves (fields, button sizes) and of the page that lists the methods.
- Changing texts of the pages beyond "Didn't get it?".

## Outcome

Implemented as specified, with these deviations and findings (from the plan, removed at close-out):

- **F1** `c.card.footer` and `c.button(href=...)` already covered the footer rows and the link button; no new component or CSS rule was needed, only the grey of `.hx-login__switch`.
- **F2** The screenshots of the login pages in both designs, on desktop and at phone width, are kept in `screenshots/` next to this spec (`canvas-shell--code--before.png` is the page before the change).

Rollout: PR #21, released as a `fix:` with the next release of `pyhx`; apps such as case-sight get it by updating `pyhx` on `versions/1`.

Open after this change: Nothing.
