# T-020 Translated error messages

## Problem

Since T-005 an app built with pyhx can show its UI in several languages, but the error messages that come from pyhx stay in English, so a user who works in German, Italian or French sees a mixed UI as soon as something goes wrong:

- Forms show Pydantic's English messages ("String should have at least 1 character", "Field required") as they come.
- A failed htmx request shows a toast with an English title ("Request failed (403)") and the HTTP status phrase ("Forbidden"), not the text the app answered, so an app can't tell its users why a request was refused.
- An error the app doesn't handle answers the bare English page "Internal Server Error" with the stack trace, outside the page layout and also in production; streams send the same heading; an unknown URL answers FastAPI's JSON `{"detail":"Not Found"}` to a browser.

## Proposed outcome

- Validation errors of Pydantic, the error toasts of htmx requests, error pages and the errors of fragments and streams are shown in the language of the request, with the i18n of T-005; apps can override every text through their catalog.
- A short plain-text answer of a failed htmx request is shown in its toast, so apps can show their own translated refusals.
- Error pages are rendered in the app's page template; stack traces are shown only in development and always logged.
- Browser requests get HTML error pages for HTTP errors; API clients keep FastAPI's JSON.
- Apps get a public function to translate a Pydantic error themselves.
- It doesn't translate log messages, messages of apps (they pass them translated) or model-level errors without a field, which forms don't show.

## Affected users and systems

- **Users of pyhx apps:** error texts in their language, no stack traces in production.
- **Apps on `versions/1`:** get the translations with the update; their own exception handlers keep precedence.

## Constraints

- Backwards compatible within `versions/1` (minor release); apps without catalogs keep English texts.
- No stack traces or exception texts for users outside development.
- Every new text in the catalogs for de, it and fr; `poe check` passes.

## Open questions

None. Requested by an app's change on translated error messages, which runs without review stops; decisions: traces in development only, JSON stays for API clients.
