import asyncio

import pytest
from fastapi.testclient import TestClient

from pyhx.core import STREAM_CLOSE_EVENT, STREAM_ERROR_EVENT
from samples.server_sent_events.main import app
from samples.server_sent_events.pages import _drop, countdown, job

_CLOSE = f"event: {STREAM_CLOSE_EVENT}\ndata: "


def _events(body: str) -> list[str]:
    return [frame for frame in body.split("\n\n") if frame]


def _names(body: str) -> list[str]:
    return [
        next(
            (line[7:] for line in frame.splitlines() if line.startswith("event: ")),
            "message",
        )
        for frame in _events(body)
    ]


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(countdown, "STEP_SECONDS", 0)
    monkeypatch.setattr(job, "STEP_SECONDS", 0.02)


class TestPages:
    def test_the_overview_links_every_example(self):
        html = TestClient(app).get("/").text

        assert 'href="/countdown"' in html
        assert 'href="/job"' in html
        assert "hx-code" in html

    @pytest.mark.parametrize("path", ["/countdown", "/job"])
    def test_each_example_shows_its_code(self, path: str):
        html = TestClient(app).get(path).text

        assert "hx-code" in html
        assert "docs:start" not in html


class TestCountdown:
    def test_start_returns_an_element_connecting_to_the_stream(self):
        html = TestClient(app).get("/countdown/start").text

        assert 'hx-ext="sse"' in html
        assert 'sse-connect="/countdown/events"' in html
        assert f'sse-close="{STREAM_CLOSE_EVENT}"' in html
        assert 'sse-swap="log"' in html

    def test_counts_down_and_closes(self):
        body = TestClient(app).get("/countdown/events", params={"start": 2}).text

        assert _names(body) == ["message", "log"] * 3 + [STREAM_CLOSE_EVENT]
        assert "Liftoff!" in body

    def test_an_error_is_sent_and_the_stream_closed(self):
        body = (
            TestClient(app)
            .get("/countdown/events", params={"start": 5, "fail_at": 3})
            .text
        )

        assert _names(body)[-2:] == [STREAM_ERROR_EVENT, STREAM_CLOSE_EVENT]


class TestJob:
    def test_unknown_job_is_a_404_before_streaming(self):
        assert TestClient(app).get("/jobs/nope/events").status_code == 404

    def test_a_started_job_is_streamed_until_it_is_finished(self):
        with TestClient(app) as client:
            card = client.post("/jobs").text
            job_id = card.split('sse-connect="/jobs/')[1].split("/events")[0]

            body = client.get(f"/jobs/{job_id}/events").text

        names = _names(body)
        assert names[:3] == ["connection", "status", "progress"]
        assert names[-1] == STREAM_CLOSE_EVENT
        assert "status" in names[3:] and "progress" in names[3:]
        assert "Finished" in body
        assert "hx-progress-bar--working" in body  # while the job runs
        assert "hx-progress-bar--success" in body  # when it is finished
        assert job.JOBS[job_id].status == "finished"

    def test_the_current_state_comes_first_and_a_finished_job_ends(self):
        job.JOBS["done"] = job.JobState(
            version=3, status="finished", stage="Done", pages_done=12
        )

        body = TestClient(app).get("/jobs/done/events").text

        assert _names(body) == ["connection", "status", "progress", STREAM_CLOSE_EVENT]
        assert "new connection" in body
        assert "12 of 12 pages" in body

    def test_a_reconnect_resumes_after_last_event_id(self):
        states = [
            job.JobState(
                version=v, status="running", stage="Reading pages", pages_done=v
            )
            for v in range(1, 5)
        ]
        job.JOBS["resume"] = states[1]  # what the database says when reconnecting

        async def fill() -> None:
            await job.live.append("resume", states)  # positions 1 to 4
            await job.live.close("resume")

        asyncio.run(fill())

        body = (
            TestClient(app)
            .get("/jobs/resume/events", headers={"Last-Event-ID": "2"})
            .text
        )
        frames = _events(body)

        assert "resumed after event 2" in frames[0]
        ids = [
            line[4:]
            for f in frames
            for line in f.splitlines()
            if line.startswith("id: ")
        ]
        assert ids == ["3", "3", "4", "4"]
        assert frames[-1] == _CLOSE

    def test_the_job_page_shows_a_known_job(self):
        job.JOBS["shown"] = job.JobState(version=0, status="queued", stage="Waiting")

        html = TestClient(app).get("/job", params={"job": "shown"}).text

        assert 'sse-connect="/jobs/shown/events"' in html
        assert "Job shown" in html


class TestDroppedConnection:
    def test_a_dropped_response_ends_without_close_so_the_browser_reconnects(self):
        job.JOBS["drop"] = job.JobState(version=0, status="running", stage="Reading")

        with TestClient(app) as client:
            assert client.post("/jobs/drop/drop").status_code == 200
            body = client.get("/jobs/drop/events").text

        assert body == ""  # ended at once, without pyhx-close
        assert "drop" not in _drop._DROP
