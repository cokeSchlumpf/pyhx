# T-004 Secondary links of the login pages below the card: plan

## Findings while planning

- **F1** `c.card.footer` already exists (`components/layouts/card.py`): right-aligned, wrapping, separated from the section by the card's divider (`card.css`, `.hx-card__footer`). No new component or CSS is needed for R3 and R5.
- **F2** `c.button(..., href=...)` renders an `<a>` with the button classes, so "Request a new link" can be a primary button that is a link (R3).
- **F3** The tests in `tests/pyhx/addons/test_email_login.py` check the code page's link only by its `href` (`test_code_page_after_request_shows_the_code_form`), not by its place; the token page tests check texts and `hx-post`. They stay green and get assertions for the place of the links.
- **F4** `samples/user_auth` has the login pages in both designs (`main.py` with `AppShell`, `canvas.py` with `CanvasShell`); the link and the code are logged to the console (`LoggingLoginTokenSender`). The screenshots are taken there.
- **F5** `gh` can't attach images to a PR description. The screenshots are committed in the change folder (`screenshots/`) and linked from the PR; they stay in `03--closed/` with the change as its record.

Deviations from the spec:

- None.

## Branching

Branch `feature/login-secondary-links`, draft PR #21. The developer accepted intent, spec, plan and steps up front and reviews the PR; the steps are committed one by one without a pause.

## Steps

### 1. Pages, style and tests

- `_card` gets `footer=`, a helper `_switch` renders `.hx-login__switch`; code page, message box and confirmation page use them as in the spec's design; `login.css` gives `.hx-login__switch` its grey. **R1, R2, R3, R4, R5, R6, R7**
- Tests in `test_email_login.py`: the code page has "Request a new link" in `hx-login__switch` after the card and not inside it; the message pages have the primary button link in `hx-card__footer` and "Back to sign in" in `hx-login__switch`; the confirmation button is in `hx-card__footer`. **R9**
- Proof: `poetry run poe check`, `poetry run poe docs-build`.

### 2. Screenshots

- Run `samples/user_auth/main.py` and `canvas.py`, take screenshots of "Check your email", "Login link not valid" and the confirmation page, on desktop and at phone width; commit them under `screenshots/` and show them in the PR. **R8**
- Proof: the screenshots, reviewed by the developer in the PR.

## Risks

- **Grey text on the grey canvas:** checked on the screenshots (spec, concern 1).
- **Screenshots in the repository:** a few small PNGs in the change folder; they can be removed at close-out if the developer prefers.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 1, test of the code page |
| R2 | Step 1, test of the code page |
| R3 | Step 1, tests of the message pages |
| R4 | Step 1, tests of the message pages |
| R5 | Step 1, test of the confirmation page |
| R6 | Step 1 (`login.css`), step 2 screenshots |
| R7 | Step 1, existing tests unchanged and green |
| R8 | Step 2 screenshots |
| R9 | Step 1, `poe check` |
