# T-017 End streams at shutdown: spec

## Requirements

- **R1** `end_streams()` (exported from `pyhx.core`) ends every open stream of the process: its response ends after the item being sent, without `pyhx-close`; the handler's generator is closed (its `finally` runs).
- **R2** A stream that starts after `end_streams()` ends without `pyhx-close` at once (at most after its first item).
- **R3** When the process receives `SIGTERM` or `SIGINT`, pyhx calls `end_streams()` and then the handler that was installed before (e.g. uvicorn's), so the server's shutdown goes on as before.
- **R4** The handlers are wrapped once, only in the main thread, only when a callable handler is installed (`SIG_DFL` and `SIG_IGN` stay); this happens when the first stream starts.
- **R5** Streams that end by themselves still send `pyhx-close`; keepalives, errors and disconnects work as before.
- **R6** The SSE guide describes the behaviour and `end_streams()`.

## Design

`stream.py` keeps an `_OpenStreams` registry: `wait_for_end()` (an `asyncio.Event` per waiting stream, with its loop) and `end()` (marks the process as ending, sets every event with `loop.call_soon_threadsafe`, safe from signal handlers and other threads). `_sse_frames` waits for the next item and for the end at once (`asyncio.wait(..., FIRST_COMPLETED)`); on the end it returns without the close event, and its `finally` cancels the pending item and closes the generator as on a disconnect. `_hook_signals()` runs at the start of `_sse_frames`: uvicorn installs its handlers before it imports the app and runs the lifespan shutdown only after all connections are closed, so neither the lifespan nor an ASGI message can carry the signal.

## Alternatives considered

- **Patching `uvicorn.Server.handle_exit`:** uvicorn binds its handler before the app is imported, so a patch arrives too late, and it would tie pyhx to uvicorn.
- **A maximum duration per stream:** every page would reconnect every few minutes, and a reload would still wait up to that duration.
- **The lifespan shutdown:** uvicorn runs it only after all connections have closed.

## Constraint mapping

| Constraint (intent) | Met by |
| --- | --- |
| Non-breaking | R5; `end_streams()` is new |
| Works with uvicorn, doesn't change what the server does | R3, R4 |

## Open questions

None.

## Areas of concern

1. **Process-wide side effect** (R3, R4): wrapping signal handlers affects the whole process; the wrapper always calls the previous handler, and is installed once. Owner: this change.

## Out of scope

- Telling the browser to reconnect elsewhere, draining connections in other servers.

## Outcome

Implemented as specified. Verified with `fastapi dev` and an open stream: a reload restarts at once, and the browser reconnects to the new process (previously the reload waited until the page was closed). Tests in `tests/pyhx/core/test_stream_shutdown.py`.

Rollout: released with the next Release PR (minor version), first used by app--casesight T-020.

Open after this change: nothing.
