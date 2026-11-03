# T-011 Server-sent events

## Problem

Apps on pyhx need to show state that changes on the server without a user action: the progress of a long-running background job, a status that a worker updates, a count that grows. Today the only way is htmx polling (`hx_trigger="every 3s"`), which sends requests while nothing changes and lags behind when something does. Every app that wants push would write its own streaming endpoint, with its own handling of the user, the language, reconnects and idle proxies.

pyhx loads the htmx extension for server-sent events (SSE) in the skeleton (`/static/js/htmx-ext-sse.min.js`), and has a `WebSocket` protocol with route registration, but the connection handler is a stub (`# TODO mw: Impelment ....` in `src/pyhx/core/webapp.py`) and there is no SSE support at all.

The first app that needs it is CaseSight (its change T-010 "Analysis jobs"): an analysis of a case runs for several minutes in an external service, a poller records each status change, and the Case Details page shows a status pill, a progress bar, the stage, pages done and the time left. CaseSight decided (D6 of its note "Document analysis integration") that this progress reaches the browser by SSE through pyhx, with htmx polling only as a stopgap until this change is released.

## Proposed outcome

pyhx gets server-sent events the way `lib--kpmx` (`cokeSchlumpf/lib--kpmx`, a fork of pyhx, release 2.0.0) already has them in `src/kpmx/core/stream.py`, its guide `docs/concepts/streams.md`, its sample `samples/streaming` and the tests `tests/kpmx/core/test_stream.py`. Same names, same behaviour, adapted to what pyhx has and kpmx doesn't (translations, permissions of the apps):

- An app declares a stream with `@hx.stream.get(path)` on `WebApp` and `WebAppRouter`, next to `.page` and `.fragment`, and a component with `my_component.fragments.stream(path)`, namespaced like its fragments: a `GET` route with path and query parameters (e.g. one stream per case) whose handler is an async generator, or an async function returning an async iterable.
- The handler yields an htpy node (an unnamed event, `message` in the browser) or an `SseEvent(data, event=, id=, retry=)`; pyhx renders the HTML with htpy and frames it as multi-line `data:` fields.
- `stream.connect(swap=…, query=…, **path_params)` returns the htmx attributes (`hx-ext="sse"`, `sse-connect`, `sse-swap`, `sse-close`) to spread into the element that owns the connection; with `swap=None` its children choose their events with `sse-swap`, so one stream can update several parts of a page (CaseSight: status pill and progress bar).
- The handler runs to its first item before the response starts, so a permission check or a missing record goes through the same error handling as a fragment (403, redirect to sign-in). The request context, the signed-in user and the language of the session stay available for the whole stream, so rendered texts are translated.
- When the generator ends, pyhx sends the close event `pyhx-close` (`STREAM_CLOSE_EVENT`) that `connect()` wires to `sse-close`, so the browser closes the connection instead of reconnecting and running the stream again; this is how a finished job ends its stream for good. An error after the first item is logged and sent as the error event `pyhx-error` (`STREAM_ERROR_EVENT`, traceback in dev mode only), then the close event. These two are the only event names pyhx defines; every other name is the app's.
- Keep-alive comments while the generator is idle (15 s by default, `keepalive=` per stream, `None` to turn off); `Cache-Control: no-cache` and `X-Accel-Buffering: no`; when the browser disconnects, the generator is closed, so `finally` blocks of the app run and no task keeps running.
- Resuming: events can carry ids, and the handler reads a reconnecting browser's `Last-Event-ID` like any FastAPI parameter (`Header(alias="Last-Event-ID")`), without an API of pyhx. The browser sends it only when it reconnects by itself after a dropped connection; after a refused or failed request the htmx extension opens a new `EventSource` without it. So a stream sends the current state first on every connect (CaseSight reads it from its database) and uses the id only to skip what the browser already has; the guide and a test show this.
- A guide in `docs/guides/` and a sample with a simulated background job whose progress is pushed, ported from kpmx and extended by what CaseSight's progress display needs: a stream per path parameter, current state first, several named events swapped into different parts of the page, reconnect with `Last-Event-ID`, end of stream when the job is finished. The job, its events and their names exist only in the sample and the guide, as an example; CaseSight builds its display from the guide without changes to pyhx. The guide says where events come from in a real app: `commons.events` (durable, at least once, through the outbox) carries the facts between the app's workers, e.g. a consumer of `CaseAnalysisProgressed`, which appends to `commons.streams` (live, at most once, fanned out to every current reader, positions that fit `Last-Event-ID`), from which the stream handler reads. The guide also says how to start work with a `POST` fragment that returns an element connecting to the stream, and mentions HTTP/2 because of the browser's limit of 6 connections per domain over HTTP/1.1.
- The unfinished `WebSocket` API is removed (the `WebSocket` protocol and its export from `pyhx.core`, `websockets=` of `WebApp` and `WebAppRouter`, the stub handler and route registration, `RequestContext.websocket` and `build_from_websocket`), as kpmx has no WebSocket API either; no app on pyhx uses it.
- Deliberately not: a broadcaster or message bus in pyhx (apps use `commons.events` and `commons.streams`; fan-out across app instances is a matter of their adapters), JSON or other non-HTML payloads, events from the browser to the server.

## Affected users and systems

- **App developers on pyhx:** get streams on apps, routers and components and a page helper; the unused `WebSocket` API goes away.
- **CaseSight (T-010):** replaces the polling stopgap of its progress display by an SSE endpoint per case once a pyhx release has this change.
- **End users of the apps:** see progress and status as it happens instead of every few seconds, with fewer requests.
- **pyhx docs and samples:** a new guide and a new sample, tested in `tests/samples`.

## Constraints

- Existing pages, fragments and components keep working unchanged.
- Released as a `feat` (pyhx 1.6.0 on `versions/1`), not as a breaking change: removing the `WebSocket` API is a deliberate exception to the rule that a removal from the public API is a `feat!`, because it never worked (the handler is a stub) and no app on pyhx uses it (`app--casesight`, `app--hello`, `app--beleglotse` checked).
- Uses what FastAPI/Starlette and the htmx SSE extension already offer; no new dependency.
- Stays close to kpmx: same public names and behaviour where pyhx has the same concepts, so code and knowledge move between the two libraries; differences are deliberate and named in the spec.
- Same security as fragments: the session cookie authenticates, the app's permission checks run before the first event, nothing is streamed to an anonymous user of a protected endpoint.
- Works behind the Azure App Service proxy of the apps' UAT deployments (keep-alive, no buffering of the response).
- Texts users see (if any, e.g. in the sample) are marked for translation and translated into de, it and fr.

## Open questions

None.
