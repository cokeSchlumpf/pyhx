# T-011 Server-sent events: spec

## Requirements

### Declaring a stream

- **R1** `@hx.stream.get(path, keepalive=15.0)` registers a stream on `WebApp`, on `WebAppRouter` (with the router's prefix, like fragments) and on the `hx` proxy before any `WebApp` exists (through the global fragment registry, like `@hx.fragment.get`). `WebAppRoutes` has `stream`.
- **R2** A component declares a stream with `my_component.fragments.stream(path)`; its route is `/_components/<handler name>/<path>`, like the component's fragments.
- **R3** The handler is an async generator, or an async function returning an async iterable; path and query parameters, `Header(...)` and the other FastAPI parameters reach it as they reach a fragment.
- **R4** The handle returned by the decorator is a `Fragment` (`path`, `method == GET`, `url(query=…, **params)`), so it can be found with `hx.fragment.exists(...)` and linked like a fragment.

### Events on the wire

- **R5** A yielded htpy node is sent as an unnamed event (`message` in the browser); a yielded `SseEvent(data, event=None, id=None, retry=None)` sets the event's name, id and reconnection delay. The data is rendered with htpy (async children work) and sent as one `data:` line per line of HTML, so line breaks survive.
- **R6** `SseEvent` refuses a name or id containing CR, LF or NUL, and a negative `retry`, with a `ValueError`.
- **R7** The response has `Content-Type: text/event-stream`, `Cache-Control: no-cache` and `X-Accel-Buffering: no`.
- **R8** While the handler yields nothing for `keepalive` seconds, a comment line (`: keepalive`) is sent, without cancelling the handler's pending step; `keepalive=None` sends none.

### Lifecycle

- **R9** The handler runs to its first item before the response starts: an exception up to there is handled exactly as in a fragment (an exception handler registered by the app or an addon, e.g. 403 or the redirect to sign-in, otherwise the error page), and no `200` stream is started. A handler that yields nothing sends only the close event.
- **R10** When the handler is exhausted, the event `pyhx-close` (`STREAM_CLOSE_EVENT`) is sent and the response ends.
- **R11** An exception after the first item is logged and sent as the event `pyhx-error` (`STREAM_ERROR_EVENT`) with an error message (with the traceback only when the `WebApp` runs in dev mode), followed by `pyhx-close`.
- **R12** When the browser disconnects, the handler is closed: its `finally` blocks run and no task of the stream keeps running (bounded wait of 5 s for the app's cleanup).
- **R13** The request context (`RequestContext.get()`, the signed-in user, the app context) and the language of the request are available to the handler for the whole stream, so texts marked with `pyhx.i18n` are rendered in the session's language.

### Page side

- **R14** `stream.connect(swap="message", query=None, **path_params)` returns the attributes `hx-ext="sse"`, `sse-connect` (the stream's URL), `sse-close="pyhx-close"` and `sse-swap` (the given event name or names plus `pyhx-error`); with `swap=None` there is no `sse-swap`, so child elements choose their events.
- **R15** A fragment may return a `StreamResponse(events, keepalive=…, headers=…)` directly; any other `HandlerResponse` returned by a fragment is sent as it is. Fragments returning a node or a `FragmentResponse` behave as before.

### WebSocket API removed

- **R16** `pyhx.core.WebSocket`, `WebApp(websockets=…)`, `WebAppRouter.add_websocket`, the websocket handler and route registration, `RequestContext.websocket` and `build_from_websocket` no longer exist; the docs no longer mention them. Released as a `feat` (intent, constraints).

### Guide and sample

- **R17** A guide `docs/guides/server-sent-events.md` (in the mkdocs navigation under "Building Apps") explains declaring and connecting a stream, several targets with `swap=None`, the close and error events, keep-alive, disconnects, `Last-Event-ID` (as a `Header` parameter, when the browser sends it and when it doesn't, current state first), starting work with a `POST` fragment, where events come from (`commons.events` between workers, `commons.streams` to the stream handler), several app instances, and HTTP/2.
- **R18** A sample `samples/server_sent_events` on `CanvasShell` has an overview with the API at a glance and example pages that each explain a scenario, show their own code (cut from the module) and run it live: a countdown (nodes and a named event, end of stream, an error), and a job (started by a `POST` fragment, one stream per job id, current state first, a status pill and a progress area updated by separate events, ids from `commons.streams` and resume with `Last-Event-ID`, end of stream when the job is finished).
- **R19** The sample is tested in `tests/samples/server_sent_events`, and `poetry run poe check` and `poetry run poe docs-build` pass.

## Design

Port of `src/kpmx/core/stream.py` of lib--kpmx 2.0.0, with the names and behaviour kept and these differences: the event names start with `pyhx-`; the error event's traceback follows `WebApp.is_dev` (kpmx does the same); the WebSocket removal is pyhx's own.

```
@hx.stream.get("/jobs/{job_id}/events")          StreamFactory.get → StreamDefinition(FragmentDefinition, Stream)
async def job_events(job_id, last_event_id=Header(None, alias="Last-Event-ID")):
    yield current_state(job_id)                   resolve_stream_result: runs to the first item inside
    async for pos, value in live.read(...):       WebApp._handle_request (try/except of fragments)
        yield SseEvent(render(value), event="progress", id=pos)
                                                  StreamResponse.to_response → _SseStreamingResponse
y.div(**job_events.connect(job_id=…, swap=None))[  _sse_frames: framing, keep-alive task, error, close
    y.span(sse_swap="status"), y.div(sse_swap="progress")]
```

- **New module `src/pyhx/core/stream.py`:** `SseEvent`, `StreamItem`, `StreamFn`, `StreamResponse`, `Stream` (protocol, a `Fragment` with `connect`), `StreamDefinition`, `StreamFactory`, `STREAM_CLOSE_EVENT`, `STREAM_ERROR_EVENT`, `DEFAULT_KEEPALIVE`, `encode_event`. Exported from `pyhx.core`: `SseEvent`, `Stream`, `StreamItem`, `StreamResponse`, `STREAM_CLOSE_EVENT`, `STREAM_ERROR_EVENT`.
- **Request handling stays the one of fragments.** A `StreamDefinition` is a `FragmentDefinition` with method `GET` whose `render` is `resolve_stream_result(fn)`, so `WebApp._register_fragments` and `_handle_request` register and run it unchanged: the request context and the locale are set there as context variables, which the streaming response inherits (Starlette runs the body in the same request task's context), and exceptions up to the first item go through `_has_app_exception_handler`.
- **Registration:** `WebApp.stream` and `WebAppRouter.stream` are `StreamFactory(self._fragments.append)`; the `hx` proxy gets a registry-backed `stream = StreamFactory(get_fragment_registry().register)`; `ComponentFragmentFactory.stream` builds the component path like `_add`. A registered stream travels as a fragment: router prefixes, the registry replay and `exists` work without change.
- **Registry replay:** `WebApp._on_global_fragment_registered` re-wraps a replayed fragment's `render` with `resolve_fragment_result`. That function now returns any `HandlerResponse` as it is (`HandlerResponse` becomes `runtime_checkable`), so a replayed stream still returns its `StreamResponse`, and R15 holds.
- **Disconnects:** `_SseStreamingResponse` closes the frame generator after Starlette's `StreamingResponse` returns or is cancelled; the frame generator cancels the pending `anext` task and closes the handler's iterator, both shielded and bounded by 5 s.
- **WebSocket removal:** the protocol and pseudo types in `webapp.py`, `websockets=`, `_websockets`, `_register_websockets`, `_handle_websocket_request` and the router's `add_websocket`/`_websockets`; `RequestContext.websocket`, `build_from_websocket` and the WebSocket branch of `_resolve_one`; `negotiate_locale` reads the session from `ctx.request` only; docstrings and the row in `docs/guides/routers.md`. The session middleware of the auth addon keeps accepting `websocket` scopes, as it is generic ASGI code.
- **Sample:** `samples/server_sent_events/main.py` (CanvasShell, mode `wide`) with `pages/countdown.py` and `pages/job.py`, the layout helper of `samples/document_viewer/pages/_layout.py` reused in a small `_layout.py`, code shown with `c.code` from `# docs:start`/`# docs:end` regions. The job keeps its state in a dict (the sample's "database") and runs as an `asyncio` task that updates the dict and appends `JobProgress` values to `TypedLiveStreams` over `InMemoryLiveStreams` of `commons.streams`; the stream handler sends the stored state first, then reads the live stream after `Last-Event-ID` and yields `status` and `progress` events with the stream positions as ids; when the job is finished, the live stream is closed, the handler ends and `pyhx-close` stops the browser. Progress shows with a native `<progress>`, `c.pill` for the status, stage, pages and time left.

## Alternatives considered

- **A pyhx-specific `Last-Event-ID` parameter (e.g. `last_event_id` injected by pyhx):** saves one `Header` annotation but adds an API that FastAPI already has; the guide shows the annotation (intent Q5).
- **`sse-starlette` or another dependency:** solves framing and keep-alive, but kpmx shows it takes about 200 lines, and the constraints exclude new dependencies.
- **Finishing the WebSocket stub instead of removing it:** no use case needs messages from the browser; kept out (intent Q1).
- **A stream as its own route kind next to fragments (own list, own handler in `WebApp`):** duplicates the request handling and the registry; a stream is a `GET` fragment with a streaming response, as in kpmx.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Existing pages, fragments and components keep working unchanged | R15, design "Registry replay"; existing tests unchanged |
| Released as a `feat`, WebSocket removal as a deliberate exception | R16; PR title `feat: server-sent events` |
| No new dependency | Design (Starlette `StreamingResponse`, anyio, htpy, the htmx SSE extension already in the skeleton) |
| Close to kpmx | Design (port, names kept, differences listed) |
| Same security as fragments | R9, R13 |
| Works behind the Azure App Service proxy | R7, R8 |
| Texts users see translated | R13 (texts of the app in a stream); pyhx adds no new text (Q1) |

## Open questions

Answer below each question; leave **Answer** empty to accept the proposal. The developer waived the acceptance stops of this change up to the final pull request, so the proposals are applied; they can be changed in the review of the pull request.

### Q1 Are the error message of the error event and the sample's texts translated?

**Proposal:** No. The error event shows the same "Internal Server Error" as the error page of fragments and pages today, which is not translated either; translating both belongs to a change of pyhx's error pages. The sample is in English like the other samples except `user_auth`; R13 is proven by a test that renders a text of pyhx's catalog in a stream under a German session.

**Answer:**

### Q2 Where does the guide live: `docs/guides/` or `docs/concepts/` (as kpmx's `concepts/streams.md`)?

**Proposal:** `docs/guides/server-sent-events.md` under "Building Apps", as the intent says, linked from `concepts/fragments.md`; it is a how-to with a real use case rather than a basic concept.

**Answer:**

## Areas of concern

1. **Context variables in the streaming body** (R13): if Starlette ran the body in a fresh context, `RequestContext.get()` and the language would be gone after the first item. Tested with a handler that reads the request context and translates a text after an `await`. Owner: Claude.
2. **Disconnects in tests** (R12): `TestClient` doesn't drop connections like a browser; the test calls the ASGI app directly with a `send` that fails, as kpmx's test does. Owner: Claude.
3. **Buffering in front of the app** (R7, R8): Azure App Service's front end may buffer `text/event-stream` despite the headers; it is checked when CaseSight T-010 runs on UAT, not in this change. Owner: Michael.
4. **One connection per open page** (R17): over HTTP/1.1 a browser opens at most 6 connections per domain, so many tabs with streams block each other; the guide names HTTP/2 (Azure App Service serves it to browsers). Owner: Michael.

## Out of scope

- A broadcaster or message bus in pyhx, and fan-out across app instances: apps use `commons.events` and `commons.streams`.
- JSON or other non-HTML payloads, messages from the browser to the server.
- Translating the error page and the error event (Q1).
- Using streams in CaseSight: its change T-010, after a pyhx release with this change.
