"""Open streams end when the process stops: ``end_streams()`` and the ``SIGTERM``/``SIGINT`` hook."""

import asyncio
import signal
import threading
from collections.abc import AsyncIterator, Callable

import pytest
from fastapi import FastAPI

from pyhx.core import STREAM_CLOSE_EVENT, StreamItem, WebApp, end_streams
from pyhx.core import stream as stream_module


@pytest.fixture(autouse=True)
def fresh_streams(monkeypatch):
    """A fresh registry of open streams, and the signal handlers as they were before the test."""
    monkeypatch.setattr(stream_module, "_open_streams", stream_module._OpenStreams())
    handlers = {sig: signal.getsignal(sig) for sig in stream_module._HOOKED_SIGNALS}
    yield
    for sig, handler in handlers.items():
        signal.signal(sig, handler)


async def _get(
    app: FastAPI, path: str, *, after_first_chunk: Callable[[], None] = lambda: None
) -> str:
    """Drive ``app`` at the ASGI level until the response is complete; call ``after_first_chunk`` once."""
    body: list[str] = []
    never = asyncio.Event()

    async def receive() -> dict:
        await never.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict) -> None:
        if message["type"] == "http.response.body" and message.get("body"):
            body.append(message["body"].decode())
            if len(body) == 1:
                after_first_chunk()

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": [],
        "server": ("test", 80),
        "client": ("test", 1234),
    }
    await asyncio.wait_for(app(scope, receive, send), timeout=5)
    return "".join(body)


def _endless_app(cleaned_up: asyncio.Event | None = None) -> FastAPI:
    hx = WebApp()

    @hx.stream.get("/s")
    async def s() -> AsyncIterator[StreamItem]:
        try:
            yield "first"
            await asyncio.sleep(60)
            yield "never"
        finally:
            if cleaned_up is not None:
                cleaned_up.set()

    return hx.create_app()


def test_end_streams_ends_an_open_stream_without_the_close_event():
    async def run() -> tuple[str, bool]:
        cleaned_up = asyncio.Event()
        body = await _get(_endless_app(cleaned_up), "/s", after_first_chunk=end_streams)
        return body, cleaned_up.is_set()

    body, cleaned_up = asyncio.run(run())

    assert body == "data: first\n\n"
    assert STREAM_CLOSE_EVENT not in body
    assert cleaned_up


def test_a_stream_started_after_the_end_ends_without_the_close_event():
    end_streams()

    body = asyncio.run(_get(_endless_app(), "/s"))

    assert "never" not in body
    assert STREAM_CLOSE_EVENT not in body


def test_a_finished_stream_still_sends_the_close_event():
    hx = WebApp()

    @hx.stream.get("/s")
    async def s() -> AsyncIterator[StreamItem]:
        yield "only"

    body = asyncio.run(_get(hx.create_app(), "/s"))

    assert body.endswith(f"event: {STREAM_CLOSE_EVENT}\ndata: \n\n")


def test_sigterm_ends_open_streams_and_runs_the_previous_handler():
    received: list[int] = []
    signal.signal(signal.SIGTERM, lambda sig, frame: received.append(sig))

    async def run() -> str:
        return await _get(
            _endless_app(),
            "/s",
            after_first_chunk=lambda: signal.raise_signal(signal.SIGTERM),
        )

    body = asyncio.run(run())

    assert body == "data: first\n\n"
    assert received == [signal.SIGTERM]


def test_the_handlers_are_wrapped_once():
    signal.signal(signal.SIGTERM, lambda sig, frame: None)

    stream_module._hook_signals()
    wrapped = signal.getsignal(signal.SIGTERM)
    stream_module._hook_signals()

    assert signal.getsignal(signal.SIGTERM) is wrapped
    assert getattr(wrapped, "_pyhx_ends_streams", False)


def test_default_handlers_are_left_alone():
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

    stream_module._hook_signals()

    assert signal.getsignal(signal.SIGTERM) is signal.SIG_DFL


def test_no_handlers_are_installed_outside_the_main_thread():
    before = signal.getsignal(signal.SIGTERM)
    thread = threading.Thread(target=stream_module._hook_signals)
    thread.start()
    thread.join()

    assert signal.getsignal(signal.SIGTERM) is before
