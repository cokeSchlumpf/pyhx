"""Server-Sent Event (SSE) streams.

A stream is a ``GET`` route whose handler is an async generator. Every item it
yields is rendered and sent to the browser as one SSE event; the htmx ``sse``
extension (loaded by the default page templates) swaps the HTML into the page::

    @hx.stream.get("/reports/{id}/progress")
    async def progress(id: str) -> AsyncIterator[StreamItem]:
        for pct in range(0, 101, 10):
            yield progress_bar(pct)                       # default "message" event
            yield SseEvent(log_line(pct), event="log")    # named event

    y.div(**progress.connect(id=report_id))["Waiting …"]

The framework takes care of the wire protocol:

- multi-line ``data:`` framing (HTML keeps its newlines),
- ``Cache-Control: no-cache`` / ``X-Accel-Buffering: no`` headers,
- keepalive comments while the generator is idle,
- a final :data:`STREAM_CLOSE_EVENT` when the generator is exhausted, which
  :meth:`Stream.connect` wires to ``sse-close`` so the browser does not
  reconnect and re-run the stream,
- a :data:`STREAM_ERROR_EVENT` (followed by the close event) when the
  generator raises,
- closing the generator (``aclose()``) when the client disconnects, so
  ``finally`` blocks in app code run,
- ending every open stream, without the close event, when the process is
  asked to stop (``SIGTERM``, ``SIGINT``) or :func:`end_streams` is called,
  so the server doesn't wait for them and the browser reconnects to the next
  process.

The generator is advanced to its first item *before* the response starts.
Anything raised up to the first ``yield`` (e.g. an auth check) therefore goes
through the regular error handling and FastAPI exception handlers, just like a
fragment.
"""

import asyncio
import functools
import inspect
import signal
import threading
import traceback
from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from http import HTTPMethod
from types import FrameType
from typing import Any, Final, Protocol

import anyio
import htpy as y
from fastapi import Response
from starlette.responses import StreamingResponse
from starlette.types import Receive, Scope, Send

from ._dev_mode import is_dev_mode
from .fragment import Fragment, FragmentDefinition
from .log import LOG
from .primitives import PathTemplate

STREAM_CLOSE_EVENT: Final = "pyhx-close"
"""Event sent after the last item; :meth:`Stream.connect` sets ``sse-close`` to it."""

STREAM_ERROR_EVENT: Final = "pyhx-error"
"""Event carrying the rendered error when the stream generator raises."""

DEFAULT_KEEPALIVE: Final = 15.0
"""Seconds of generator silence after which a keepalive comment is sent."""

_SSE_HEADERS: Final = {
    "Cache-Control": "no-cache",
    # Disables response buffering in nginx-style reverse proxies.
    "X-Accel-Buffering": "no",
}

# How long a disconnected stream waits for the app's cleanup (``finally``
# blocks) before giving up on it.
_CLEANUP_TIMEOUT: Final = 5.0


class _OpenStreams:
    """The open streams of the process, to end them all when it stops.

    Once ended, streams that start afterwards end at once too: the process is
    on its way out.
    """

    def __init__(self) -> None:
        self._ending = False
        self._waiters: set[tuple[asyncio.AbstractEventLoop, asyncio.Event]] = set()

    async def wait_for_end(self) -> None:
        """Return when the streams are ended."""
        if self._ending:
            return
        entry = (asyncio.get_running_loop(), asyncio.Event())
        self._waiters.add(entry)
        try:
            await entry[1].wait()
        finally:
            self._waiters.discard(entry)

    def end(self) -> None:
        """End all open streams and the ones started later; safe from any thread and from signal handlers."""
        self._ending = True
        for loop, event in list(self._waiters):
            try:
                loop.call_soon_threadsafe(event.set)
            except RuntimeError:  # the loop is closed already
                pass


_open_streams = _OpenStreams()

_HOOKED_SIGNALS: Final = (signal.SIGINT, signal.SIGTERM)


def end_streams() -> None:
    """End every open stream of the process, and every stream started later.

    Each response ends without :data:`STREAM_CLOSE_EVENT`, so the browser
    reconnects, e.g. to the process that replaces this one. pyhx calls it when
    the process receives ``SIGTERM`` or ``SIGINT``; call it yourself where a
    server stops in another way. Safe from any thread.
    """
    _open_streams.end()


def _hook_signals() -> None:
    """Make ``SIGTERM`` and ``SIGINT`` end the open streams, then run the handlers installed before.

    Servers like uvicorn wait for open responses before they shut down and tell
    them nothing, so a stream would keep the process alive. The server installs
    its handlers before it starts the app, so they are wrapped when the first
    stream starts. Only the main thread may install signal handlers; elsewhere
    (e.g. in a test client) nothing is wrapped.
    """
    if threading.current_thread() is not threading.main_thread():
        return
    for sig in _HOOKED_SIGNALS:
        previous = signal.getsignal(sig)
        if not callable(previous) or getattr(previous, "_pyhx_ends_streams", False):
            continue
        signal.signal(sig, _ending_handler(previous))


def _ending_handler(
    previous: Callable[[int, FrameType | None], Any],
) -> Callable[[int, FrameType | None], Any]:
    def handler(sig: int, frame: FrameType | None) -> Any:
        end_streams()
        return previous(sig, frame)

    handler._pyhx_ends_streams = True  # type: ignore[attr-defined]
    return handler


@dataclass(frozen=True)
class SseEvent:
    """A single Server-Sent Event.

    Yield an ``SseEvent`` from a stream handler to control the event name,
    ``id`` or ``retry`` fields. A bare ``Node`` is shorthand for
    ``SseEvent(node)`` — an unnamed event, which the browser dispatches as
    ``message``.

    Attributes
    ----------
    data : Node
        The HTML to send. Rendered with htpy, so async children work.
    event : str, optional
        Event name; matched by ``sse-swap`` on the client.
    id : str, optional
        Event id; the browser echoes the last one in ``Last-Event-ID``
        when it reconnects.
    retry : int, optional
        Reconnection delay in milliseconds the browser should use.
    """

    data: y.Node = ""
    event: str | None = None
    id: str | None = None
    retry: int | None = None

    def __post_init__(self) -> None:
        for name, value in (("event", self.event), ("id", self.id)):
            if value is not None and any(c in value for c in "\r\n\0"):
                raise ValueError(f"SSE {name} must not contain CR, LF or NUL")
        if self.retry is not None and self.retry < 0:
            raise ValueError("SSE retry must not be negative")


StreamItem = y.Node | SseEvent
"""What a stream handler yields: a ``Node`` (unnamed event) or an :class:`SseEvent`."""

StreamFn = Callable[
    ..., AsyncIterable[StreamItem] | Awaitable[AsyncIterable[StreamItem]]
]
"""A stream handler: an async generator function, or an async function
returning an async iterable (handy for running checks before streaming)."""


async def encode_event(item: StreamItem) -> str:
    """Render ``item`` into its SSE wire format, including the blank-line terminator."""
    event = item if isinstance(item, SseEvent) else SseEvent(item)

    lines: list[str] = []
    if event.event is not None:
        lines.append(f"event: {event.event}")
    if event.id is not None:
        lines.append(f"id: {event.id}")
    if event.retry is not None:
        lines.append(f"retry: {event.retry}")

    html = "".join([chunk async for chunk in y.fragment[event.data].aiter_chunks()])
    # Every line of the payload gets its own ``data:`` field; the browser
    # re-joins them with ``\n``. Always emitting at least one ``data:`` line
    # also guarantees that empty events (e.g. the close event) are dispatched.
    html = html.replace("\r\n", "\n").replace("\r", "\n")
    lines.extend(f"data: {line}" for line in html.split("\n"))

    return "\n".join(lines) + "\n\n"


@dataclass(frozen=True)
class StreamResponse:
    """Response wrapper that sends ``events`` as a Server-Sent Event stream.

    Returned by the handlers that :meth:`StreamFactory.get` registers; it can
    also be returned from a fragment directly. Implements
    :class:`~pyhx.core.primitives.HandlerResponse`.

    Attributes
    ----------
    events : AsyncIterable of StreamItem
        The items to send, in order.
    keepalive : float, optional
        Seconds of silence after which a keepalive comment is sent.
        ``None`` disables keepalives.
    headers : Mapping of str to str, optional
        Extra response headers, merged over the SSE defaults.
    """

    events: AsyncIterable[StreamItem]
    keepalive: float | None = DEFAULT_KEEPALIVE
    headers: Mapping[str, str] | None = None

    def to_response(self) -> Response:
        return _SseStreamingResponse(
            _sse_frames(aiter(self.events), self.keepalive),
            headers={**_SSE_HEADERS, **(self.headers or {})},
            media_type="text/event-stream",
        )


class _SseStreamingResponse(StreamingResponse):
    """``StreamingResponse`` that always closes its body iterator.

    Starlette cancels the sending task when the client disconnects but leaves
    the async generator suspended, so its cleanup would only run whenever the
    garbage collector finalises it. Closing it here makes the app's ``finally``
    blocks run deterministically on disconnect.
    """

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            body_iterator = self.body_iterator
            if isinstance(body_iterator, AsyncIterator) and hasattr(
                body_iterator, "aclose"
            ):
                with anyio.move_on_after(_CLEANUP_TIMEOUT, shield=True):
                    await body_iterator.aclose()


_END: Final = object()


async def _next_or_end(iterator: AsyncIterator[StreamItem]) -> Any:
    # A Task cannot carry StopAsyncIteration cleanly, so map it to a sentinel.
    try:
        return await anext(iterator)
    except StopAsyncIteration:
        return _END


async def _sse_frames(
    events: AsyncIterator[StreamItem], keepalive: float | None
) -> AsyncIterator[str]:
    """Turn ``events`` into SSE frames, adding keepalives, error and close events.

    The next item is awaited in a separate task so that a keepalive can be sent
    while the generator is busy without cancelling it. When the streams are
    ended (:func:`end_streams`), the frames stop without the close event, so the
    browser reconnects.
    """
    _hook_signals()
    pending: asyncio.Task[Any] | None = None
    ending = asyncio.ensure_future(_open_streams.wait_for_end())
    try:
        try:
            while True:
                pending = asyncio.create_task(_next_or_end(events))
                while True:
                    done, _ = await asyncio.wait(
                        {pending, ending},
                        timeout=keepalive,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if pending in done:
                        break
                    if ending in done:
                        return
                    yield ": keepalive\n\n"
                item = pending.result()
                pending = None
                if item is _END:
                    break
                yield await encode_event(item)
        except Exception as exc:  # noqa: BLE001 - reported to the client as an error event
            LOG.exception("Error in event stream")
            yield await encode_event(
                SseEvent(_render_error(exc), event=STREAM_ERROR_EVENT)
            )
        yield await encode_event(SseEvent(event=STREAM_CLOSE_EVENT))
    finally:
        ending.cancel()
        with anyio.move_on_after(_CLEANUP_TIMEOUT, shield=True):
            if pending is not None:
                # Cancelling the task throws CancelledError into the app's
                # generator, which runs its cleanup and finishes it.
                pending.cancel()
                await asyncio.wait({pending})
            aclose = getattr(events, "aclose", None)
            if aclose is not None:
                await aclose()


def _render_error(exc: BaseException) -> y.Node:
    # Imported lazily: ``webapp`` imports this module.
    from .webapp import WebApp

    try:
        is_dev = WebApp.get().is_dev
    except LookupError:
        is_dev = is_dev_mode()

    if not is_dev:
        return y.div[y.h1["Internal Server Error"]]
    return y.div[
        y.h1["Internal Server Error"],
        y.pre["".join(traceback.format_exception(exc))],
    ]


async def _prepend(
    first: StreamItem, rest: AsyncIterator[StreamItem]
) -> AsyncIterator[StreamItem]:
    try:
        yield first
        async for item in rest:
            yield item
    finally:
        aclose = getattr(rest, "aclose", None)
        if aclose is not None:
            await aclose()


async def _empty() -> AsyncIterator[StreamItem]:
    return
    yield


def resolve_stream_result(
    fn: StreamFn, *, keepalive: float | None = DEFAULT_KEEPALIVE
) -> Callable[..., Awaitable[StreamResponse]]:
    """Wrap a stream handler into a render function returning a :class:`StreamResponse`.

    The handler is advanced to its first item here, i.e. before the response
    starts, so errors raised up to the first ``yield`` surface as regular
    request errors instead of a broken stream.
    """

    # See ``resolve_fragment_result``: ``wraps`` keeps the original signature
    # visible to FastAPI's parameter analysis.
    @functools.wraps(fn)
    async def __call__(**kwargs) -> StreamResponse:
        source = fn(**kwargs)
        if inspect.isawaitable(source):
            source = await source

        iterator = aiter(source)
        try:
            first = await anext(iterator)
        except StopAsyncIteration:
            return StreamResponse(_empty(), keepalive=keepalive)

        return StreamResponse(_prepend(first, iterator), keepalive=keepalive)

    return __call__


class Stream(Fragment, Protocol):
    """Handle for a registered stream, returned by ``@hx.stream.get(...)``."""

    def connect(
        self,
        *,
        swap: str | Sequence[str] | None = "message",
        query: Mapping[str, object] | None = None,
        **kwargs,
    ) -> dict[str, str]: ...


class StreamDefinition(FragmentDefinition, Stream):
    def __init__(
        self,
        path: PathTemplate,
        fn: StreamFn,
        *,
        keepalive: float | None = DEFAULT_KEEPALIVE,
    ) -> None:
        super().__init__(
            path, HTTPMethod.GET, resolve_stream_result(fn, keepalive=keepalive)
        )

    def connect(
        self,
        *,
        swap: str | Sequence[str] | None = "message",
        query: Mapping[str, object] | None = None,
        **kwargs,
    ) -> dict[str, str]:
        """Build the htmx ``sse`` attributes that open this stream.

        Spread the result into the element that should own the connection::

            y.div(**progress.connect(id=42))["Waiting …"]

        The connection is opened when the element enters the DOM and closed
        when it is removed or the stream ends (``sse-close`` is set to
        :data:`STREAM_CLOSE_EVENT`).

        Parameters
        ----------
        swap : str or Sequence of str, optional
            Event name(s) whose HTML is swapped into this element
            (``sse-swap``). :data:`STREAM_ERROR_EVENT` is added
            automatically so errors become visible. Pass ``None`` when
            child elements declare their own ``sse-swap``.
        query : Mapping of str to object, optional
            Query parameters for the stream URL, see :meth:`url`.
        **kwargs
            Path parameters for the stream URL.
        """
        attrs = {
            "hx-ext": "sse",
            "sse-connect": self.url(query=query, **kwargs),
            "sse-close": STREAM_CLOSE_EVENT,
        }
        if swap is not None:
            events = [swap] if isinstance(swap, str) else list(swap)
            attrs["sse-swap"] = ",".join([*events, STREAM_ERROR_EVENT])
        return attrs


class StreamFactory:
    """Decorator factory for ``@hx.stream.get(...)``.

    Streams are ``GET``-only because the browser's ``EventSource`` only issues
    ``GET`` requests; pass input via path or query parameters.
    """

    def __init__(self, register: Callable[[Fragment], None]) -> None:
        self._register = register

    def get(
        self, path: str, *, keepalive: float | None = DEFAULT_KEEPALIVE
    ) -> Callable[[StreamFn], Stream]:
        """Register an async generator as a Server-Sent Event stream at ``path``.

        Parameters
        ----------
        path : str
            Route path template, e.g. ``"/jobs/{id}/progress"``.
        keepalive : float, optional
            Seconds of generator silence after which a keepalive comment is
            sent. ``None`` disables keepalives.
        """

        def __call__(fn: StreamFn) -> Stream:
            stream = StreamDefinition(PathTemplate(path), fn, keepalive=keepalive)
            self._register(stream)
            return stream

        return __call__
