"""Server-sent events sample (T-011): streams pushed from async generators.

Run with::

    poetry run fastapi dev samples/server_sent_events/main.py

Each example page explains a scenario, runs it live and shows its code (cut
from the page's own module, so the code shown is the code that runs): a
countdown (nodes and a named event, end of stream, an error) and the progress
of a background job (current state first, several targets, resume with
``Last-Event-ID``, end of stream), see :mod:`samples.server_sent_events.pages`.
"""

from pathlib import Path

import htpy as y

import pyhx.components as c
from pyhx.core import WebApp
from pyhx.page_templates import CanvasShell

from .pages import _drop, countdown, job
from .pages._layout import links

HERE = Path(__file__).parent

hx = WebApp(
    title="Server-sent events",
    default_page_template=CanvasShell(
        header_content=lambda: [y.span["T-011"]], mode="wide"
    ),
    static_dirs=[HERE / "static"],
    # Only for the demo of a dropped connection, see pages/job.py.
    configure_fastapi_app=[lambda app: app.add_middleware(_drop.DropConnections)],
)

hx.include_router(countdown.router)
hx.include_router(job.router)
hx.include_router(_drop.router)

_GLANCE = """from pyhx.core import SseEvent, StreamItem

# Declare: a GET route whose handler is an async generator
# (also on WebAppRouter and on components: my_component.fragments.stream(path)).
@hx.stream.get("/jobs/{job_id}/events", keepalive=15.0)
async def job_events(
    job_id: str,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> AsyncIterator[StreamItem]:
    ensure_permission(...)                      # before the first item: like a fragment
    yield status_pill(...)                      # a node: unnamed event "message"
    yield SseEvent(bar(...), event="progress",  # named, with an id for resuming
                   id="7", retry=1000)
                                                # the generator ends: "pyhx-close"

# Connect: spread the htmx attributes into the element owning the connection.
y.div(**job_events.connect(job_id=42))                 # swaps "message"
y.div(**job_events.connect(job_id=42, swap=None))[     # children choose
    y.span(sse_swap="status"),
    y.div(sse_swap="progress"),
]

# pyhx takes care of: data framing, keep-alive comments, "pyhx-close" at the end,
# "pyhx-error" on an exception, closing the generator when the browser leaves,
# the request context (user, language) for the whole stream."""


@hx.page("/", title="Server-sent events")
async def index() -> y.Node:
    return y.div(style="display: flex; flex-direction: column; gap: 1rem;")[
        y.h1(style="margin: 0;")["Server-sent events"],
        y.p[
            "Streams of ",
            y.code["pyhx.core"],
            " (T-011) push rendered HTML to the page from async generators: each example explains a scenario, runs it live and shows its code.",
        ],
        links(),
        y.h2["The API at a glance"],
        c.code([("API", _GLANCE, "python")], max_height=None),
    ]


app = hx.create_app()
