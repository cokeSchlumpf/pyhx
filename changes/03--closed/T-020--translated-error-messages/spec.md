# T-020 Translated error messages: spec

## Requirements

### Form validation

- **R1** The forms of pyhx (`DataForm`, its drawers and `HeadlessForm`) show the validation errors that Pydantic produces itself (missing value, too short or too long text, number and date formats, number limits, patterns, choices, list lengths) in the request language, with the limits of the error (e.g. the minimal length) in the text, formatted for the language.
- **R2** An error of another type (an app's `PydanticCustomError`, `field_error`/`validation_error` of pyhx) is shown with its message as it comes; for an error raised by a validator as `ValueError` or `AssertionError`, without Pydantic's English prefix ("Value error, ").
- **R3** pyhx offers the translation of R1 as a public function in `pyhx.i18n`, so apps can use it for errors they show themselves.

### Error toasts of htmx requests

- **R4** When an htmx request fails, the toast's title and text are in the request language of the page (failed request with its status, lost connection, timeout, response not applicable).
- **R5** When the failed response is plain text (`text/plain`) and short, the toast shows that text instead of the general one, so a translated refusal of the app reaches the user; any other body (HTML, JSON, a long text) is never shown.

### Error pages and errors of fragments and streams

- **R6** A page request that fails with an error the app doesn't handle answers 500 with a translated message inside the app's page template; if the page template fails too, the message alone. The error is logged with its stack trace.
- **R7** A fragment, API endpoint or stream that fails with an error the app doesn't handle answers a translated text (fragment and endpoint: `text/plain`, 500, which R5 shows; stream: the error event).
- **R8** Stack traces and exception texts are shown only in development (`WebApp.is_dev`), never outside it.
- **R9** An HTTP error (`HTTPException` of Starlette or FastAPI: an unknown URL, a method not allowed, a 404 an app raises) answers a browser page request (not htmx, `Accept` includes `text/html`) with an error page in the page template: a translated title and text for the status (400, 403, 404, 405; other statuses a general text), the status code unchanged; an htmx request gets the translated text as `text/plain`; every other request keeps FastAPI's JSON answer. A `detail` the app set itself (other than the status' phrase) is shown as the text; headers of the exception are kept.
- **R10** Exception handlers the app registers keep their precedence (e.g. `NotAuthenticated` of the auth addon).

### Catalogs and docs

- **R11** All new texts are in pyhx's catalogs for de, it and fr; an app can override each by its `msgid`.
- **R12** The guide "Multilingual apps" (`docs/guides/i18n.md`) has a section on error messages: what pyhx translates, how an app translates its own refusals (codes in the domain, then a translated `PydanticCustomError` or `field_error` at the field, or a short plain-text answer to htmx), the function of R3, the error pages and that traces show in development only.

## Design

- **Validation messages.** New module `src/pyhx/i18n/_validation.py`, exported as `pyhx.i18n.validation_message(error) -> str` (`error`: one entry of `ValidationError.errors()`). A table from Pydantic's error `type` to the translated text, filled from `ctx`: `missing`, `string_too_short`, `string_too_long`, `string_pattern_mismatch`, `too_short`, `too_long`, `int_parsing`, `int_from_float`, `float_parsing`, `decimal_parsing`, `bool_parsing`, the date, datetime and time parsing errors, `greater_than`, `greater_than_equal`, `less_than`, `less_than_equal`, `multiple_of`, `decimal_max_digits`, `decimal_max_places`, `enum`, `literal_error`, `url_parsing`, `url_type`, the `*_type` errors of scalar types (one general text). Counts with `_n`, numbers and limits with `format_number` (dates as `format_date`). `value_error` and `assertion_error` give `str(ctx["error"])`; everything else `error["msg"]`. `DataForm` and `HeadlessForm` call it in `_validation_errors_to_dict`.
- **Toasts.** `notification_error_template()` gets `data-text-*` attributes with the translated texts, rendered with the page; the title of a failed request has a `{status}` placeholder the JS fills. `pyhx.notifications.js` reads them (today's English texts if an attribute is missing) and, on `htmx:responseError`, shows `xhr.responseText` when the response's `Content-Type` is `text/plain` and the text has at most 300 characters.
- **Unhandled errors.** `src/pyhx/core/_errors.py` builds the answers: the translated texts per status, `error_page(…)` (a `y.section` with title and text, the trace in a `y.pre` in development) rendered through `WebApp._render_page_template` with a fallback to the bare node, and `error_text_response(…)` (`PlainTextResponse`, with the trace in development). The page, fragment and endpoint wrappers of `webapp.py` use them; `stream._render_error` uses the translated title.
- **HTTP errors.** `create_app` registers a handler for `starlette.exceptions.HTTPException` before the app's `configure_fastapi_app` functions run, so an app's own handler replaces it. The handler sets the `RequestContext` with `build_from_request` (the user is in `request.state`, set by the session middleware for every request) and answers as R9 says; other requests go to FastAPI's `http_exception_handler`.
- **Catalogs, docs.** `python -m pyhx.i18n update`, translations of the new entries for de, it and fr; the guide section of R12.

## Alternatives considered

- **Translating Pydantic's messages by their English text:** the texts change between Pydantic versions and contain their values; `type` and `ctx` are stable and meant for it (as `validation_error.py` says).
- **Showing every failed response's body in the toast:** HTML or JSON bodies are no messages for users and may reveal internals.
- **Model-level errors (empty `loc`) in forms:** would need a new place in every form; apps attach such errors to the field they concern.
- **Keeping the trace on the 500 page in production:** shows internals to every user.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Backwards compatible within `versions/1`; English without catalogs | R2, R9 (JSON for API clients), R10, R11 (source text as fallback) |
| No traces or exception texts for users outside development | R5, R6–R8 |
| New texts in de, it, fr; `poe check` | R11 |

## Open questions

None.

## Areas of concern

1. **Behavior change for apps** (R6, R8, R9): browsers get an HTML 404 instead of JSON; the 500 page loses its trace outside development. Both without an API change; part of the release notes. Owner: agent.
2. **Error page while the page template fails** (R6, R9): falls back to the message alone; tested. Owner: agent.
3. **Parallel change T-019 (timeline):** both add catalog entries; the second to merge runs `pyhx.i18n update` again. Owner: agent.

## Out of scope

- Log messages, apps' own messages, model-level errors in forms, the browser's own validation messages.

## Outcome

Implemented as specified, with these deviations and findings (from the plan, removed at close-out):

- **D1** An app that replaces the handler of HTTP errors registers it for `starlette.exceptions.HTTPException`, as FastAPI's default does; a handler for FastAPI's subclass alone doesn't see the router's 404s (as before this change).
- **F1** `InlineEdit` reports its validation errors through the same forms, so its messages are translated too ("Enter a value of at most 100.").
- **F2** The toast falls back to its English texts when a page was rendered by an older pyhx without the `data-text-*` attributes.
- **F3** Two tests changed with the behavior: the auth addon's catch-all test no longer finds the exception name in the 500 page outside development, and the stream error event says "Something went wrong".

Rollout: minor release on `versions/1`; apps get the texts with `poetry update pyhx`. Browser requests to unknown URLs now get an HTML 404 page instead of JSON.
