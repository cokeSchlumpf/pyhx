"""Tests for the timeline: what the server renders for the script, defaults and validation."""

import json
import re
from datetime import date

import pytest

from pyhx.components import TimelineCategory, TimelineEvent, TimelineQuery, timeline

_EPOCH = date(1970, 1, 1)

CATEGORIES = [
    TimelineCategory("release", "Releases", "#16a34a", "tag"),
    TimelineCategory("incident", "Incidents", "#dc2626", "zap"),
    TimelineCategory("meeting", "Meetings", "#64748b", "users", shown=False),
]

EVENTS = [
    TimelineEvent("r1", "release", date(2026, 3, 2), "Release 2.1"),
    TimelineEvent("i1", "incident", date(2026, 3, 9), "Outage", end=date(2026, 3, 10), warn=True),
    TimelineEvent("m1", "meeting", date(2026, 5, 20), "Review"),
]


def _day(value: date) -> int:
    return (value - _EPOCH).days


def _html(**kwargs) -> str:
    events = kwargs.pop("events", EVENTS)
    categories = kwargs.pop("categories", CATEGORIES)
    return str(timeline(events, categories, open_url="/x", **kwargs))


def _events(html: str) -> list[dict]:
    match = re.search(r'<script type="application/json" data-timeline-events>(.*?)</script>', html, re.S)
    assert match
    return json.loads(match.group(1))


def _chip(html: str, key: str) -> str:
    match = re.search(rf'<button[^>]*data-timeline-category="{key}"[^>]*>.*?</button>', html, re.S)
    assert match
    return match.group(0)


def _thumbs(html: str) -> list[str]:
    return re.findall(r'<input type="hidden" name="timeline-span" value="(-?\d+)"', html)


class TestData:
    def test_every_event_for_the_script_sorted_by_date(self) -> None:
        events = _events(_html(events=list(reversed(EVENTS))))

        assert [e["key"] for e in events] == ["r1", "i1", "m1"]
        assert events[1] == {
            "key": "i1",
            "category": "incident",
            "start": "2026-03-09",
            "end": "2026-03-10",
            "label": "Outage",
            "warn": True,
        }

    def test_a_label_can_not_end_the_script(self) -> None:
        html = _html(events=[TimelineEvent("x", "release", date(2026, 3, 2), "</script><b>")])

        assert "</script><b>" not in html
        assert _events(html)[0]["label"] == "</script><b>"

    def test_one_icon_template_per_category(self) -> None:
        html = _html()

        for key in ("release", "incident", "meeting"):
            assert f'<template data-timeline-icon="{key}">' in html

    def test_open_url_and_defaults_for_the_script(self) -> None:
        html = _html()

        assert 'data-timeline-open-url="/x"' in html
        assert 'data-timeline-default="release,incident"' in html
        assert "data-timeline-query" not in html

    def test_query_names(self) -> None:
        html = _html(query=TimelineQuery(categories="types", start="from", end="to"))

        assert "&#34;categories&#34;: &#34;types&#34;" in html

    def test_forwards_id_and_attributes(self) -> None:
        html = _html(id="roadmap", class_="extra")

        assert 'id="roadmap"' in html
        assert "hx-timeline extra" in html
        assert 'name="roadmap-span"' in html


class TestChips:
    def test_shown_by_default(self) -> None:
        html = _html()

        assert 'aria-pressed="true"' in _chip(html, "release")
        assert 'aria-pressed="false"' in _chip(html, "meeting")

    def test_shown_given_ignores_unknown_keys(self) -> None:
        html = _html(shown=["meeting", "nope"])

        assert 'aria-pressed="true"' in _chip(html, "meeting")
        assert 'aria-pressed="false"' in _chip(html, "release")

    def test_counts_events_in_the_span(self) -> None:
        html = _html(span=(date(2026, 3, 1), date(2026, 3, 31)))

        assert '<span class="hx-timeline__chip-count">1</span>' in _chip(html, "release")
        assert '<span class="hx-timeline__chip-count">0</span>' in _chip(html, "meeting")

    def test_colour_of_the_category(self) -> None:
        assert "--timeline--color: #dc2626" in _chip(_html(), "incident")

    def test_presets_and_reset_are_plain_buttons(self) -> None:
        html = _html()

        for action in ("default", "all", "reset"):
            assert re.search(rf'<button type="button" data-timeline-action="{action}"', html)


class TestSpan:
    def test_bounds_a_month_around_the_events(self) -> None:
        html = _html()

        assert f'data-slider-min="{_day(date(2026, 1, 30))}"' in html
        assert f'data-slider-max="{_day(date(2026, 6, 20))}"' in html
        assert _thumbs(html) == [str(_day(date(2026, 1, 30))), str(_day(date(2026, 6, 20)))]

    def test_span_given_and_clamped_to_the_bounds(self) -> None:
        html = _html(
            bounds=(date(2026, 1, 1), date(2026, 12, 31)),
            span=(date(2025, 6, 1), date(2026, 4, 30)),
        )

        assert _thumbs(html) == [str(_day(date(2026, 1, 1))), str(_day(date(2026, 4, 30)))]

    def test_empty_span_falls_back_to_the_bounds(self) -> None:
        html = _html(bounds=(date(2026, 1, 1), date(2026, 12, 31)), span=(date(2026, 5, 1), date(2026, 5, 1)))

        assert _thumbs(html) == [str(_day(date(2026, 1, 1))), str(_day(date(2026, 12, 31)))]

    def test_thumbs_are_named(self) -> None:
        html = _html()

        assert 'aria-label="Start"' in html
        assert 'aria-label="End"' in html

    def test_without_events_around_today(self) -> None:
        html = _html(events=[])

        assert len(_thumbs(html)) == 2
        assert _events(html) == []

    def test_strip_counts_shown_categories_per_month(self) -> None:
        html = _html(bounds=(date(2026, 3, 1), date(2026, 5, 31)))
        bars = re.findall(r'data-timeline-month="(\d+),(\d+)" style="--timeline--height: (\d+)%"', html)

        # March has the release and the incident; the meeting in May isn't shown by default.
        assert [b[2] for b in bars] == ["100", "0", "0"]
        assert bars[0][:2] == (str(_day(date(2026, 3, 1))), str(_day(date(2026, 4, 1))))


class TestValidation:
    def test_unknown_category(self) -> None:
        with pytest.raises(ValueError, match="unknown category"):
            _html(events=[TimelineEvent("x", "nope", date(2026, 1, 1), "x")])

    def test_repeated_event_keys(self) -> None:
        with pytest.raises(ValueError, match="event keys"):
            _html(events=[EVENTS[0], EVENTS[0]])

    def test_repeated_category_keys(self) -> None:
        with pytest.raises(ValueError, match="category keys"):
            _html(categories=[CATEGORIES[0], CATEGORIES[0]], events=[])

    def test_end_before_start(self) -> None:
        with pytest.raises(ValueError, match="ends before"):
            _html(events=[TimelineEvent("x", "release", date(2026, 3, 2), "x", end=date(2026, 3, 1))])

    def test_empty_bounds(self) -> None:
        with pytest.raises(ValueError, match="bounds are empty"):
            _html(bounds=(date(2026, 3, 2), date(2026, 3, 2)))
