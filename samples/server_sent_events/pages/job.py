"""Example: the progress of a background job, pushed to the page.

Shaped like a document analysis: a ``POST`` fragment starts the job, which
runs as an ``asyncio`` task, stores its state (the sample's "database" is a
dict) and appends every change to a live stream of ``commons.streams``. One
stream per job sends the current state first, then the live changes as two
named events (the status pill and the progress area), each with the position
of the live stream as its id, so a reconnecting browser resumes after
``Last-Event-ID``. When the job is finished, the live stream is closed, the
handler ends and ``pyhx-close`` stops the browser.
"""

import asyncio
import time
from collections.abc import AsyncIterator
from typing import Annotated, Literal
from uuid import uuid4

import htpy as y

# docs:start imports
from commons.streams import InMemoryLiveStreams, PydanticCodec, TypedLiveStreams
from fastapi import Header, HTTPException
from pydantic import BaseModel

import pyhx.components as c
from pyhx.components.view_model import Pct
from pyhx.core import SseEvent, StreamItem, WebAppRouter

# docs:end imports
from ._layout import code, example_page

STEP_SECONDS = 0.6
"""Seconds per step of the simulated job; the tests set it to 0."""

PAGES = 12

router = WebAppRouter()


# docs:start state
class JobState(BaseModel):
    version: int  # counts the changes, to skip what the page already shows
    status: Literal["queued", "running", "finished"]
    stage: str
    pages_done: int = 0
    pages_total: int = PAGES
    seconds_left: int | None = None


# The app's database: the state of each job, read on every connect.
JOBS: dict[str, JobState] = {}

# The live view of the changes, fanned out to every open stream; in an app
# with several instances an adapter on Redis or similar replaces it.
live = TypedLiveStreams[JobState](
    InMemoryLiveStreams(), "sample:job", PydanticCodec(JobState)
)
# docs:end state

_tasks: set[asyncio.Task[None]] = set()


# docs:start worker
async def run_job(job_id: str) -> None:
    """The worker: in an app, a consumer of the job's events (commons.events)."""

    async def record(**changes) -> None:
        state = JOBS[job_id]
        state = state.model_copy(update={"version": state.version + 1, **changes})
        JOBS[job_id] = state  # 1. store the state
        await live.append(job_id, [state])  # 2. push it to open streams

    await asyncio.sleep(STEP_SECONDS)
    for done in range(1, PAGES + 1):
        await asyncio.sleep(STEP_SECONDS)
        left = round((PAGES - done + 2) * STEP_SECONDS)
        await record(
            status="running", stage="Reading pages", pages_done=done, seconds_left=left
        )
    await asyncio.sleep(STEP_SECONDS)
    await record(stage="Finding contradictions", seconds_left=round(STEP_SECONDS))
    await asyncio.sleep(STEP_SECONDS)
    await record(status="finished", stage="Done", seconds_left=None)
    await live.close(job_id)  # open streams end after the last change


# docs:end worker


# docs:start stream
@router.stream.get("/jobs/{job_id}/events")
async def job_events(
    job_id: str,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> AsyncIterator[StreamItem]:
    state = JOBS.get(job_id)
    if state is None:  # before the first item: answered like a fragment (404)
        raise HTTPException(status_code=404)

    # retry: reconnect 1 s after a dropped connection (the browser's default is ~3 s)
    yield SseEvent(connection(last_event_id), event="connection", retry=1000)
    # The current state first, on every connect: nothing is lost while the
    # connection was down, also when the browser couldn't send Last-Event-ID.
    yield SseEvent(status_pill(state), event="status")
    yield SseEvent(progress(state), event="progress")
    if state.status == "finished":
        return  # pyhx-close: the browser doesn't reconnect

    # Then the live changes; the id lets a reconnect continue after it.
    async for position, change in live.read(job_id, after=last_event_id):
        if change.version <= state.version:
            continue  # already shown with the current state
        yield SseEvent(status_pill(change), event="status", id=position)
        yield SseEvent(progress(change), event="progress", id=position)


# docs:end stream


# docs:start start
@router.fragment.post("/jobs")
async def start_job() -> y.Node:
    job_id = uuid4().hex[:6]
    JOBS[job_id] = JobState(version=0, status="queued", stage="Waiting for a worker")
    task = asyncio.create_task(run_job(job_id))
    _tasks.add(task)  # keep a reference until the task is done
    task.add_done_callback(_tasks.discard)
    return job_card(job_id)


# docs:end start


# docs:start page
def job_card(job_id: str) -> y.Node:
    # One connection for the card; its parts choose their events.
    return y.div(".sample-job", **job_events.connect(job_id=job_id, swap=None))[
        y.div(".sample-job__head")[
            y.strong[f"Job {job_id}"],
            y.span(sse_swap="status")[status_pill(JOBS[job_id])],
        ],
        y.div(sse_swap="progress")[progress(JOBS[job_id])],
        y.div(".sample-job__foot")[
            y.small(sse_swap="connection"),
            y.span(".sample-job__actions")[
                y.button(
                    ".sample-job__drop",
                    type="button",
                    hx_post=f"/jobs/{job_id}/drop",
                    hx_swap="none",
                )["Drop the connection"],
                y.a(href=f"/job?job={job_id}", target="_blank")["Open in a new tab"],
            ],
        ],
    ]


def status_pill(state: JobState) -> y.Node:
    appearance = {"queued": "neutral", "running": "info", "finished": "success"}
    return c.pill(state.status.capitalize(), appearance=appearance[state.status])


def progress(state: JobState) -> y.Node:
    done = Pct.clamp(state.pages_done / state.pages_total)
    left = f" · about {state.seconds_left} s left" if state.seconds_left else ""
    return c.progress_bar(
        None if state.status == "queued" else done,  # queued: waiting, no value
        working=state.status == "running",
        appearance="success" if state.status == "finished" else "primary",
        label=state.stage,
        value_text=f"{done.percent:.0f} %",
        supporting_text=f"{state.pages_done} of {state.pages_total} pages{left}",
    )


# docs:end page


def connection(last_event_id: str | None) -> y.Node:
    at = time.strftime("%H:%M:%S")
    if last_event_id is None:
        return f"Connected at {at}, new connection"
    return f"Connected at {at}, resumed after event {last_event_id}"


@router.page("/job", title="Job progress")
async def job_page(job: str | None = None) -> y.Node:
    return example_page(
        title="Job progress",
        intro=[
            y.p[
                "A job runs in the background for about ten seconds, as an analysis of a case would for minutes. ",
                "The worker stores each change of its state and appends it to a live stream of ",
                y.code["commons.streams"],
                "; the stream of the job sends the stored state first, then the live changes as the events ",
                y.code["status"],
                " and ",
                y.code["progress"],
                ", which the pill and the progress area of the card swap in.",
            ],
            y.p[
                "Try: start a job and open it in a new tab (the current state comes first); reload the page while it runs; ",
                "press “Drop the connection” while it runs (the server ends the response without ",
                y.code["pyhx-close"],
                ", as a proxy timeout or a restart would): the browser reconnects by itself with ",
                y.code["Last-Event-ID"],
                " and the card says after which event it resumed. When the job is finished, the stream ends with ",
                y.code["pyhx-close"],
                " and the browser doesn't reconnect.",
            ],
        ],
        demo=[
            c.button(
                "Start a job",
                appearance="primary",
                hx_post=start_job.url(),
                hx_target="#jobs",
                hx_swap="afterbegin",
            ),
            y.div("#jobs.sample-jobs")[job_card(job) if job in JOBS else None],
        ],
        code=code(__file__, "imports", "state", "worker", "stream", "start", "page"),
    )
