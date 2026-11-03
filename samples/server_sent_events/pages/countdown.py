"""Example: a countdown pushed over one stream (ported from lib--kpmx).

The unnamed events (plain nodes) replace the big number, the named ``log``
events are appended to a list below it; when the generator ends, pyhx sends
``pyhx-close`` and the browser closes the connection instead of reconnecting.
"Start (fails at 3)" raises inside the generator to show the error event.
Starting again replaces the connecting element, which closes the old
connection; the generator's ``finally`` block logs that.
"""

import asyncio
import logging
from collections.abc import AsyncIterator

import htpy as y

import pyhx.components as c

# docs:start imports
from pyhx.core import STREAM_ERROR_EVENT, SseEvent, StreamItem, WebAppRouter

# docs:end imports
from ._layout import code, example_page

LOG = logging.getLogger("uvicorn.error")

STEP_SECONDS = 1.0
"""Seconds between two numbers; the tests set it to 0."""

router = WebAppRouter()


# docs:start stream
@router.stream.get("/countdown/events")
async def countdown(
    start: int = 5, fail_at: int | None = None
) -> AsyncIterator[StreamItem]:
    try:
        for n in range(start, 0, -1):
            if n == fail_at:
                raise RuntimeError(f"Countdown aborted at {n}")
            yield y.span(class_="sample-countdown__number")[n]  # unnamed: "message"
            yield SseEvent(y.li[f"{n} …"], event="log")  # named event
            await asyncio.sleep(STEP_SECONDS)

        yield y.span(class_="sample-countdown__number")["Liftoff!"]
        yield SseEvent(y.li["Liftoff, stream closed."], event="log")
        # The generator ends: pyhx sends "pyhx-close", the browser stops.
    finally:
        LOG.info("Countdown stream finished (start=%s, fail_at=%s)", start, fail_at)


# docs:end stream


# docs:start connect
@router.fragment.get("/countdown/start")
async def start_countdown(fail_at: int | None = None) -> y.Node:
    # swap=None: the children choose their events with sse-swap, so the
    # number and the log are updated independently.
    return y.div(**countdown.connect(swap=None, query={"fail_at": fail_at}))[
        y.p(sse_swap=f"message,{STREAM_ERROR_EVENT}")["Ready …"],
        y.ul(sse_swap="log", hx_swap="beforeend"),
    ]


# docs:end connect


@router.page("/countdown", title="Countdown")
async def countdown_page() -> y.Node:
    return example_page(
        title="Countdown",
        intro=[
            y.p[
                "Each number is pushed by the server over one server-sent events connection, declared with ",
                y.code["@router.stream.get"],
                ". The handler is an async generator: a yielded node is an unnamed event (",
                y.code["message"],
                "), an ",
                y.code["SseEvent"],
                " has a name, an id or a reconnection delay.",
            ],
            y.p[
                "When the generator ends, pyhx sends ",
                y.code["pyhx-close"],
                ", which ",
                y.code["connect()"],
                " wires to ",
                y.code["sse-close"],
                ": the browser closes the connection instead of running the countdown again. An exception after the first item is sent as ",
                y.code["pyhx-error"],
                " (with the traceback only in dev mode), then the stream is closed.",
            ],
        ],
        demo=[
            y.div(class_="sample-countdown__buttons")[
                c.button(
                    "Start countdown",
                    appearance="primary",
                    hx_get=start_countdown.url(),
                    hx_target="#countdown",
                ),
                c.button(
                    "Start (fails at 3)",
                    hx_get=start_countdown.url(query={"fail_at": 3}),
                    hx_target="#countdown",
                ),
            ],
            y.div("#countdown.sample-countdown"),
        ],
        code=code(__file__, "imports", "stream", "connect"),
    )
