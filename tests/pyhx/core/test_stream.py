import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

import htpy as y
import pytest
from fastapi import FastAPI, Header, Response
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from pyhx.core import (
    STREAM_CLOSE_EVENT,
    STREAM_ERROR_EVENT,
    FragmentResponse,
    RequestContext,
    SseEvent,
    StreamItem,
    StreamResponse,
    WebApp,
    WebAppRouter,
    component,
)
from pyhx.core import hx as hx_proxy
from pyhx.core.fragment_registry import FragmentRegistry
from pyhx.core.stream import StreamFactory, encode_event
from pyhx.i18n import _

_CLOSE = f"event: {STREAM_CLOSE_EVENT}\ndata: \n\n"


def _encode(item: StreamItem) -> str:
    return asyncio.run(encode_event(item))


def _events(body: str) -> list[str]:
    """Split an SSE body into its frames (without the blank-line terminator)."""
    return [frame for frame in body.split("\n\n") if frame]


class TestEncodeEvent:
    def test_bare_node_is_unnamed_event(self):
        assert _encode(y.p["hi"]) == "data: <p>hi</p>\n\n"

    def test_named_event_with_id_and_retry(self):
        event = SseEvent(y.p["hi"], event="log", id="7", retry=1000)
        assert _encode(event) == "event: log\nid: 7\nretry: 1000\ndata: <p>hi</p>\n\n"

    def test_multiline_html_keeps_its_newlines(self):
        # v1 replaced newlines with spaces, which broke <pre> / code blocks.
        frame = _encode(y.pre["a\nb\r\nc\rd"])
        assert frame == "data: <pre>a\ndata: b\ndata: c\ndata: d</pre>\n\n"

    def test_empty_event_still_has_a_data_line(self):
        # Without a data line the browser would not dispatch the event.
        assert _encode(SseEvent(event="done")) == "event: done\ndata: \n\n"

    def test_text_is_escaped(self):
        assert _encode("<b>") == "data: &lt;b&gt;\n\n"

    def test_async_children_are_rendered(self):
        async def child() -> str:
            return "late"

        assert _encode(y.p[child()]) == "data: <p>late</p>\n\n"

    @pytest.mark.parametrize("field", ["event", "id"])
    def test_rejects_line_breaks_in_fields(self, field):
        with pytest.raises(ValueError):
            SseEvent(**{field: "a\nb"})

    def test_rejects_negative_retry(self):
        with pytest.raises(ValueError):
            SseEvent(retry=-1)


class TestStreamEndpoint:
    def test_streams_items_and_closes(self):
        hx = WebApp()

        @hx.stream.get("/s")
        async def s() -> AsyncIterator[StreamItem]:
            yield y.p["one"]
            yield SseEvent(y.p["two"], event="log")

        response = TestClient(hx.create_app()).get("/s")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["x-accel-buffering"] == "no"
        assert response.text == (
            "data: <p>one</p>\n\nevent: log\ndata: <p>two</p>\n\n" + _CLOSE
        )

    def test_path_and_query_params(self):
        hx = WebApp()

        @hx.stream.get("/jobs/{id}")
        async def job(id: int, q: str = "") -> AsyncIterator[StreamItem]:
            yield f"{id}:{q}"

        response = TestClient(hx.create_app()).get("/jobs/42?q=x")

        assert _events(response.text)[0] == "data: 42:x"

    def test_empty_generator_only_closes(self):
        hx = WebApp()

        @hx.stream.get("/s")
        async def s() -> AsyncIterator[StreamItem]:
            return
            yield

        assert TestClient(hx.create_app()).get("/s").text == _CLOSE

    def test_async_function_returning_iterable(self):
        hx = WebApp()

        async def items() -> AsyncIterator[StreamItem]:
            yield "x"

        @hx.stream.get("/s")
        async def s() -> AsyncIterator[StreamItem]:
            return items()

        assert TestClient(hx.create_app()).get("/s").text == "data: x\n\n" + _CLOSE

    def test_error_mid_stream_sends_error_then_close(self):
        hx = WebApp(is_dev=False)

        @hx.stream.get("/s")
        async def s() -> AsyncIterator[StreamItem]:
            yield "ok"
            raise RuntimeError("secret detail")

        events = _events(TestClient(hx.create_app()).get("/s").text)

        assert events[0] == "data: ok"
        assert events[1].startswith(f"event: {STREAM_ERROR_EVENT}\n")
        assert "Something went wrong" in events[1]
        assert "secret detail" not in events[1]
        assert events[2] + "\n\n" == _CLOSE

    def test_error_event_has_traceback_in_dev(self):
        hx = WebApp(is_dev=True)

        @hx.stream.get("/s")
        async def s() -> AsyncIterator[StreamItem]:
            yield "ok"
            raise RuntimeError("secret detail")

        assert "secret detail" in TestClient(hx.create_app()).get("/s").text

    def test_error_before_first_item_uses_exception_handlers(self):
        # The generator is primed before the response starts, so e.g. an auth
        # check at the top of the handler can still answer with a redirect/401.
        class _Denied(Exception):
            pass

        hx = WebApp()

        @hx.stream.get("/s")
        async def s() -> AsyncIterator[StreamItem]:
            raise _Denied()
            yield

        app = hx.create_app()

        async def handle(request, exc) -> Response:
            return JSONResponse({"denied": True}, status_code=401)

        app.add_exception_handler(_Denied, handle)

        response = TestClient(app).get("/s")

        assert response.status_code == 401
        assert response.json() == {"denied": True}

    def test_request_context_is_available_while_streaming(self):
        hx = WebApp()

        @hx.stream.get("/s")
        async def s() -> AsyncIterator[StreamItem]:
            yield "first"
            await asyncio.sleep(0)
            yield RequestContext.get_request().url.path

        events = _events(TestClient(hx.create_app()).get("/s").text)

        assert events[1] == "data: /s"

    def test_keepalive_while_generator_is_idle(self):
        hx = WebApp()

        @hx.stream.get("/s", keepalive=0.01)
        async def s() -> AsyncIterator[StreamItem]:
            yield "a"
            await asyncio.sleep(0.1)
            yield "b"

        body = TestClient(hx.create_app()).get("/s").text

        assert ": keepalive\n\n" in body
        assert body.endswith("data: b\n\n" + _CLOSE)

    def test_keepalive_can_be_disabled(self):
        hx = WebApp()

        @hx.stream.get("/s", keepalive=None)
        async def s() -> AsyncIterator[StreamItem]:
            await asyncio.sleep(0.02)
            yield "a"
            await asyncio.sleep(0.02)
            yield "b"

        assert "keepalive" not in TestClient(hx.create_app()).get("/s").text

    def test_texts_are_translated_while_streaming(self):
        hx = WebApp()

        @hx.stream.get("/s")
        async def s() -> AsyncIterator[StreamItem]:
            yield _("Save")
            await asyncio.sleep(0)
            yield _("Save")

        response = TestClient(hx.create_app()).get(
            "/s", headers={"Accept-Language": "de-CH"}
        )

        assert _events(response.text)[:2] == ["data: Speichern", "data: Speichern"]

    def test_last_event_id_reaches_the_handler_as_a_header(self):
        hx = WebApp()

        @hx.stream.get("/s")
        async def s(
            last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
        ) -> AsyncIterator[StreamItem]:
            yield SseEvent(f"after {last_event_id}", id="8")

        client = TestClient(hx.create_app())

        assert _events(client.get("/s").text)[0] == "id: 8\ndata: after None"
        resumed = client.get("/s", headers={"Last-Event-ID": "7"}).text
        assert _events(resumed)[0] == "id: 8\ndata: after 7"

    def test_fragment_may_return_stream_response(self):
        hx = WebApp()

        async def items() -> AsyncIterator[StreamItem]:
            yield "x"

        @hx.fragment.get("/s")
        async def s() -> StreamResponse:
            return StreamResponse(items())

        assert TestClient(hx.create_app()).get("/s").text == "data: x\n\n" + _CLOSE

    def test_fragment_response_still_passes_through(self):
        hx = WebApp()

        @hx.fragment.get("/f")
        async def f() -> FragmentResponse:
            return FragmentResponse(node=y.p["hi"], headers={"X-Test": "1"})

        response = TestClient(hx.create_app()).get("/f")

        assert response.text == "<p>hi</p>"
        assert response.headers["x-test"] == "1"


async def _get_until_disconnect(
    app: FastAPI, path: str, chunks: int, *, block_send: bool = False
) -> None:
    """Drive ``app`` at the ASGI level and disconnect after ``chunks`` body chunks.

    With ``block_send`` the disconnecting ``send`` never returns, so the
    disconnect lands while the stream is suspended at a ``yield`` rather than
    while it awaits the app's generator.
    """
    disconnected = asyncio.Event()
    received = 0

    async def receive() -> dict:
        await disconnected.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict) -> None:
        nonlocal received
        if message["type"] == "http.response.body" and message.get("body"):
            received += 1
            if received >= chunks:
                disconnected.set()
                if block_send:
                    await asyncio.Event().wait()

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


class TestStreamDisconnect:
    @pytest.mark.parametrize("block_send", [False, True])
    def test_client_disconnect_closes_the_generator(self, block_send):
        hx = WebApp()
        cleaned_up = asyncio.Event()

        @hx.stream.get("/s")
        async def s() -> AsyncIterator[StreamItem]:
            try:
                yield "first"
                await asyncio.sleep(60)
                yield "never"
            finally:
                cleaned_up.set()

        async def run() -> bool:
            await _get_until_disconnect(
                hx.create_app(), "/s", chunks=1, block_send=block_send
            )
            # Checked before ``asyncio.run`` finalises leftover generators, so
            # this proves the cleanup ran as part of the request.
            return cleaned_up.is_set()

        assert asyncio.run(run())


class TestConnect:
    def _stream(self, path: str = "/jobs/{id}"):
        factory = StreamFactory(lambda _: None)

        @factory.get(path)
        async def job(id: int) -> AsyncIterator[StreamItem]:
            yield ""

        return job

    def test_default_attributes(self):
        assert self._stream().connect(id=42, query={"tab": "log"}) == {
            "hx-ext": "sse",
            "sse-connect": "/jobs/42?tab=log",
            "sse-close": STREAM_CLOSE_EVENT,
            "sse-swap": f"message,{STREAM_ERROR_EVENT}",
        }

    def test_multiple_swap_events(self):
        attrs = self._stream().connect(id=1, swap=["status", "log"])
        assert attrs["sse-swap"] == f"status,log,{STREAM_ERROR_EVENT}"

    def test_no_swap_for_child_targets(self):
        assert "sse-swap" not in self._stream().connect(id=1, swap=None)

    def test_spreads_into_htpy_element(self):
        html = str(y.div(**self._stream().connect(id=1)))
        assert 'hx-ext="sse"' in html
        assert 'sse-connect="/jobs/1"' in html


class TestStreamRegistration:
    def test_router_prefix_applies_to_stream(self):
        router = WebAppRouter()

        @router.stream.get("/progress")
        async def progress() -> AsyncIterator[StreamItem]:
            yield "x"

        hx = WebApp()
        hx.include_router(router, prefix="/jobs")

        assert progress.connect()["sse-connect"] == "/jobs/progress"
        response = TestClient(hx.create_app()).get("/jobs/progress")
        assert response.text == "data: x\n\n" + _CLOSE

    def test_registers_through_a_fragment_registry(self):
        registry = FragmentRegistry()
        factory = StreamFactory(registry.register)

        @factory.get("/s")
        async def s() -> AsyncIterator[StreamItem]:
            yield "x"

        assert registry.fragments() == (s,)

    def test_hx_proxy_registers_through_the_global_registry(self):
        # Declared before the WebApp exists; the WebApp replays the registry
        # and re-wraps the render, which must keep the StreamResponse.
        @hx_proxy.stream.get("/_tests/stream/from-global-registry")
        async def from_registry() -> AsyncIterator[StreamItem]:
            yield "x"

        response = TestClient(WebApp().create_app()).get(
            "/_tests/stream/from-global-registry"
        )

        assert response.text == "data: x\n\n" + _CLOSE

    def test_stream_is_a_get_fragment(self):
        hx = WebApp()

        @hx.stream.get("/jobs/{id}/events")
        async def events(id: int) -> AsyncIterator[StreamItem]:
            yield ""

        assert hx.fragment.exists("/jobs/{id}/events", "GET")
        assert events.url(id=3, query={"a": 1}) == "/jobs/3/events?a=1"

    def test_component_stream_is_namespaced(self):
        @component(auto_register=False)
        def ticker() -> y.Node:
            return y.div

        @ticker.fragments.stream("/ticks")
        async def ticks() -> AsyncIterator[StreamItem]:
            yield "x"

        assert ticks.url() == "/_components/ticks/ticks"
