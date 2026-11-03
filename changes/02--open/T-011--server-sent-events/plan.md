# T-011 Server-sent events: plan

## Findings while planning

- **F1** `HandlerResponse` (`core/primitives/handler_response.py`) is a plain `Protocol`; `isinstance` on it raises `TypeError`. It becomes `@runtime_checkable` so `resolve_fragment_result` can pass any `HandlerResponse` through (spec, design "Registry replay").
- **F2** Starlette 1.6.0 runs the body of a `StreamingResponse` in a task of an anyio task group (`task_group.start_soon`), which copies the context of the request task: the request context and the locale set by `WebApp._handle_request` stay visible while streaming (area of concern 1).
- **F3** `anyio` is not declared in `pyproject.toml` but is a dependency of Starlette, so it is always installed; the stream module uses its shielded `move_on_after` for the cleanup on disconnect, as kpmx does. No new dependency.
- **F4** `commons` 1.5.0 (locked by pyhx) has `commons.streams` (`InMemoryLiveStreams`, `TypedLiveStreams`, `PydanticCodec`), which the sample uses; no update of `commons` is needed.
- **F5** The WebSocket API is used outside `webapp.py`, `webapp_router.py` and `request_context.py` only by `negotiate_locale.py` (`ctx.request or ctx.websocket`), one test (`tests/pyhx/core/test_request_context.py`), the row in `docs/guides/routers.md` and docstrings.
- **F6** Translation is chosen by `Accept-Language` when the session has no language (tests already use the header), so R13 can be tested with `TestClient` and a text of pyhx's catalog, e.g. "Close" → "Schließen".

Deviations from the spec:

- None.

## Branching

Branch `feature/server-sent-events`, draft PR #48 (`feat: server-sent events`). The developer waived the review stop after each step for this change (up to the published final PR with a demo); each step is committed and pushed, and the PR description is updated.

## Steps

### 1. Streams in pyhx core

- `src/pyhx/core/stream.py` ported from kpmx (`SseEvent`, `StreamResponse`, `StreamDefinition`, `StreamFactory`, `encode_event`, `pyhx-close`, `pyhx-error`); `stream` on `WebApp`, `WebAppRouter`, `WebAppRoutes`, the `hx` proxy and `ComponentFragmentFactory`; `HandlerResponse` runtime-checkable, `resolve_fragment_result` passes any `HandlerResponse` through; exports in `pyhx.core`. **R1–R15**
- Proof: `tests/pyhx/core/test_stream.py`, ported from kpmx's tests (encoding, items and close, path and query parameters, empty generator, async function returning an iterable, error mid-stream with and without dev mode, error before the first item through an exception handler, request context while streaming, keep-alive on and off, a fragment returning `StreamResponse`, disconnect closes the generator, `connect()` attributes, router prefix, registry, component namespace), plus: a text of pyhx's catalog rendered in German after an `await` (R13), `Last-Event-ID` read with `Header` (R3), `hx.fragment.exists` finds a stream (R4). `poetry run poe check`.

### 2. WebSocket API removed

- Remove the WebSocket protocol and pseudo types, `websockets=`, `_websockets`, `_register_websockets`, `_handle_websocket_request`, `WebAppRouter.add_websocket`, `RequestContext.websocket`, `build_from_websocket`, the WebSocket branch of `_resolve_one`, the `ctx.websocket` fallback in `negotiate_locale`, the export from `pyhx.core`, the test line and the docs row; adjust docstrings. **R16**
- Proof: `grep -rn "websocket" src docs samples tests` finds only the generic ASGI scope handling of the auth addon's session middleware; `poetry run poe check`.

### 3. Guide

- `docs/guides/server-sent-events.md` (in `mkdocs.yml` under "Building Apps"), a link from `docs/concepts/fragments.md`, the stream row in `docs/guides/routers.md`. **R17**
- Proof: `poetry run poe docs-build` (strict); the guide's examples match the sample's code.

### 4. Sample

- `samples/server_sent_events/` (overview with the API at a glance, `pages/countdown.py`, `pages/job.py`, `_layout.py`), its tests in `tests/samples/server_sent_events/`, screenshots of the pages (desktop and phone width) in `screenshots/` of the change folder. **R18, R19**
- Proof: the sample tests (each page shows code and a connected element, the countdown stream ends with `pyhx-close`, the job stream sends the current state first, then `status` and `progress` events with ids, resumes after `Last-Event-ID`, ends with `pyhx-close`); the sample run with `poetry run fastapi dev samples/server_sent_events/main.py` and driven in a browser (Playwright); `poetry run poe check` and `poetry run poe docs-build`.

## Risks

- **Hanging tests from streaming responses:** a stream that never ends blocks `TestClient`; every test stream is finite or is driven through the ASGI app with a timeout, as in kpmx.
- **Registry state between tests:** streams registered through the `hx` proxy land in the global fragment registry; the tests clear it like the existing registry tests do.
- **Removal reaches an app after all:** checked in the intent (no app uses the WebSocket API); `poe check` of CaseSight runs when it updates pyhx.

## Proof per requirement

| Requirement | Proven by |
| --- | --- |
| R1 | Step 1: tests for `WebApp`, router prefix, registry / `hx` proxy |
| R2 | Step 1: component namespace test |
| R3 | Step 1: path and query parameters, async function returning an iterable, `Last-Event-ID` header |
| R4 | Step 1: `exists` and `url` of a stream |
| R5 | Step 1: encoding tests (unnamed, named with id and retry, multi-line, escaping, async children) |
| R6 | Step 1: rejection tests |
| R7 | Step 1: header assertions |
| R8 | Step 1: keep-alive on and off |
| R9 | Step 1: error before the first item, empty generator |
| R10 | Step 1: items and close |
| R11 | Step 1: error mid-stream, dev mode traceback |
| R12 | Step 1: disconnect test on the ASGI app |
| R13 | Step 1: request context while streaming, German text after an `await` |
| R14 | Step 1: `connect()` attribute tests |
| R15 | Step 1: fragment returning `StreamResponse`, `FragmentResponse` still passes through, existing fragment tests |
| R16 | Step 2: grep and `poe check` |
| R17 | Step 3: `docs-build` |
| R18 | Step 4: sample tests and the browser run |
| R19 | Step 4: `poe check`, `docs-build` |
