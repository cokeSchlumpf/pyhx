# T-011 Server-sent events

## Problem

Apps on pyhx need to show state that changes on the server without a user action: the progress of a long-running background job, a status that a worker updates, a count that grows. Today the only way is htmx polling (`hx_trigger="every 3s"`), which sends requests while nothing changes and lags behind when something does. pyhx loads the htmx extensions for server-sent events (SSE) and WebSockets, and has a `WebSocket` protocol with route registration, but the connection handler is a stub (`# TODO mw: Impelment ....` in `src/pyhx/core/webapp.py`) and there is no SSE support at all.

## Proposed outcome

- A way to declare an SSE endpoint on a page or router, like fragments: an async generator yields events, each with a name and an htpy node (or a fragment) that pyhx renders to HTML, so the page swaps it in with `sse-connect` and `sse-swap`.
- The endpoint runs in the same request context as fragments: the signed-in user, permissions and the language of the session, so rendered texts are translated.
- Resuming: the endpoint receives `Last-Event-ID` and events carry ids, so a reconnecting browser continues where it stopped; the endpoint can first send the current state.
- Keep-alive comments at a configurable interval, so proxies don't close idle connections; the stream ends cleanly when the browser disconnects or the generator finishes.
- A small API on the page side (e.g. an `sse` helper on `htmx()` or a component) that wires `hx-ext="sse"`, `sse-connect` and `sse-swap`.
- A guide in `docs/guides/` and a sample with a simulated background job whose progress is pushed, including reconnect.
- Decide in the intent: what happens to the WebSocket stub (finish, remove, or leave for later).

## Notes

- One-way updates are the common case; SSE is plain HTTP, uses the session cookie and needs no extra protocol.
- Fan-out across app instances is the app's concern: the generator can read from any source, e.g. `LiveStreams` of `commons.streams`, whose positions fit `Last-Event-ID`.
- Over HTTP/1.1 a browser keeps at most 6 connections per domain; the guide should mention HTTP/2.
