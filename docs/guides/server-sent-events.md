# Server-Sent Events

A **stream** pushes HTML from the server to a page over one [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) connection, without the page asking: the progress of a background job, a status a worker changes, a count that grows. It replaces htmx polling (`hx_trigger="every 3s"`), which sends requests while nothing changes and lags behind when something does.

The handler is an async generator. Every item it yields becomes one event, which the htmx `sse` extension (loaded by every page template) swaps into the page.

Every scenario below is a page of the sample, with its explanation, the live demo and its code:

```bash
poetry run fastapi dev samples/server_sent_events/main.py
```

## Declaring a stream

```python
import asyncio
from collections.abc import AsyncIterator

import htpy as y
from pyhx.core import SseEvent, StreamItem, hx


@hx.stream.get("/countdown/events")
async def countdown(start: int = 5) -> AsyncIterator[StreamItem]:
    for n in range(start, 0, -1):
        yield y.span[n]                               # unnamed event: "message"
        yield SseEvent(y.li[f"{n} …"], event="log")   # named event
        await asyncio.sleep(1)
```

`stream.get(path, keepalive=15.0)` is on `WebApp`, on `WebAppRouter` (with the router's prefix) and on the shared `hx` proxy, and components declare streams next to their fragments: `my_component.fragments.stream(path)`. Streams are `GET` routes, because the browser's `EventSource` sends nothing else; input comes as path or query parameters, and every other FastAPI parameter (`Header`, `Cookie`, …) works as in a fragment.

A handler yields:

| Item | Sent as |
| --- | --- |
| an htpy node | an unnamed event, which the browser dispatches as `message` |
| `SseEvent(data, event=None, id=None, retry=None)` | an event with a name, an id (for resuming) and a reconnection delay in milliseconds |

The HTML is rendered with htpy (async children work) and sent as one `data:` line per line, so whitespace in `<pre>` survives. Instead of a generator, the handler may be an `async` function that returns an async iterable, e.g. one read from another service.

## Connecting from a page

`stream.connect(**path_params)` returns the htmx attributes that open the connection. Spread them into the element that owns it:

```python
y.div(**countdown.connect())["Ready …"]   # swaps every "message" into the div
```

To update several parts of the page from one stream, pass `swap=None` and let the children choose their events with `sse-swap`:

```python
y.div(**job_events.connect(job_id=job_id, swap=None))[
    y.span(sse_swap="status")[status_pill(state)],
    y.div(sse_swap="progress")[progress(job_id, state)],
]
```

`swap` also takes a list of event names (`swap=["status", "progress"]`), and `query={...}` adds query parameters, as with `url()`. The connection opens when the element enters the page and closes when the element is removed, e.g. replaced by another swap.

## What pyhx takes care of

- **Request context.** The stream runs like a fragment: the signed-in user, `RequestContext.get()`, the app context and the language of the session are there for the whole stream, so texts marked with `pyhx.i18n` are translated.
- **Checks before the first item.** The handler runs to its first item before the response starts. A permission check, a missing record (`HTTPException(404)`) or the sign-in redirect at the top of the handler is answered exactly as in a fragment; no stream is started.
- **End of stream.** When the handler ends, pyhx sends `pyhx-close` (`STREAM_CLOSE_EVENT`). `connect()` sets `sse-close` to it, so the browser closes the connection instead of reconnecting and running the stream again. This is how a finished job stops its stream for good.
- **Errors.** An exception after the first item is logged and sent as `pyhx-error` (`STREAM_ERROR_EVENT`), then `pyhx-close`. `connect()` adds `pyhx-error` to `sse-swap`, so the error replaces the content; with `swap=None`, add it to the child that should show it. The traceback is only sent in dev mode.
- **Keep-alive.** While the handler yields nothing, a comment line is sent every 15 seconds, so proxies don't close the connection. Change it with `stream.get(path, keepalive=5.0)`, or turn it off with `keepalive=None`.
- **Disconnects.** When the browser goes away, the handler is closed: its `finally` blocks run, and nothing keeps running for the stream.
- **Restarts.** When the process is asked to stop (`SIGTERM`, `SIGINT`: a reload of `fastapi dev`, a deployment, Ctrl+C), every open stream ends its response without `pyhx-close`, and so does a stream that starts after that. Servers like uvicorn wait for open responses before they stop; without this, a page that stays connected would hold up every reload. The browser reconnects by itself, to the new process, and the stream sends the current state again (see [Resuming](#resuming-with-last-event-id)). pyhx wraps the handlers the server installed when the first stream starts and calls them afterwards; where a server stops in another way, call `end_streams()` (`pyhx.core`) yourself.
- **Headers.** `Content-Type: text/event-stream`, `Cache-Control: no-cache` and `X-Accel-Buffering: no` (no buffering in nginx-like proxies).

pyhx defines only the event names `pyhx-close` and `pyhx-error`; all others are the app's.

## Progress of a background job

The sample's job page shows the pattern for long-running work, e.g. the analysis of a case. Three parts work together:

1. **The worker** stores every change of the job's state (in the app's database) and appends it to a live stream of `commons.streams`.
2. **The stream** of the job sends the stored state first, then reads the live stream and yields the changes as named events, each with the position of the live stream as its id.
3. **The page** connects one element per job; its parts swap the events they show.

```python
@router.stream.get("/jobs/{job_id}/events")
async def job_events(
    job_id: str,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> AsyncIterator[StreamItem]:
    state = JOBS.get(job_id)                 # the app's database
    if state is None:
        raise HTTPException(status_code=404)  # before the first item: a 404

    # The current state first, on every connect.
    yield SseEvent(status_pill(state), event="status")
    yield SseEvent(progress(job_id, state), event="progress")
    if state.status == "finished":
        return                                # pyhx-close: no reconnect

    # Then the live changes; the id lets a reconnect continue after it.
    async for position, change in live.read(job_id, after=last_event_id):
        if change.version <= state.version:
            continue                          # already shown with the state
        yield SseEvent(status_pill(change), event="status", id=position)
        yield SseEvent(progress(job_id, change), event="progress", id=position)
```

`progress(job_id, state)` renders `c.progress_bar(..., id=f"job-{job_id}-progress")`. With a stable `id`, htmx carries the old width into the bar it swaps in, so the bar glides to the new value instead of jumping; without an `id`, it jumps.

The work itself starts with a `POST` fragment, since `EventSource` can only `GET`: it creates the job and returns the element that connects to the job's stream.

### Where the events come from

pyhx has no message bus; the handler reads from whatever source the app chooses. With the libraries of the platform:

- **`commons.events`** carries the facts between the app's workers: durable, at least once, through the outbox of the change that caused them (e.g. `CaseAnalysisProgressed`). A browser connection doesn't subscribe here; its consumers are durable and get every event again after a restart.
- **`commons.streams`** carries the live view to the open streams: not durable, at most once, fanned out to every current reader, read from a position on. A consumer of the events appends to it, the stream handler reads from it. Its positions are opaque, increasing strings, which fit `Last-Event-ID`.

`InMemoryLiveStreams` serves one app instance; with several instances, an adapter on a shared store (Redis or similar) fans out across them, without a change in the stream handler.

### Resuming with `Last-Event-ID`

When a connection drops (a proxy timeout, a restart of the app), the browser reconnects by itself after the `retry` delay (about 3 seconds by default) and sends the id of the last event it received as the header `Last-Event-ID`. The handler reads it like any header, as above, and continues after it.

The browser doesn't always send it: when a request is refused or fails (e.g. the app is down for a moment), the htmx extension opens a new `EventSource`, which starts without an id. So a stream sends the current state first on every connect and uses the id only to skip what the page already shows. The sample's "Drop the connection" button ends a response the way a proxy would, and the card shows after which event it resumed.

## Several streams and HTTP/2

Every open stream holds one connection. Over HTTP/1.1, a browser opens at most 6 connections per domain, across all tabs; with many tabs open, further requests wait. Serve the app over HTTP/2 (Azure App Service and most proxies do), where one connection carries many streams, and keep to one stream per page where you can, using named events for its parts.

## `StreamResponse`

`stream.get` wraps the handler into a `StreamResponse`. A fragment can return one directly, e.g. to set headers:

```python
@hx.fragment.get("/legacy")
async def legacy() -> StreamResponse:
    return StreamResponse(events(), keepalive=None, headers={"X-Custom": "1"})
```

Unlike `stream.get`, this doesn't run the generator to its first item before the response starts.
