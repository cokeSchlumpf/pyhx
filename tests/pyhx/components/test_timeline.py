"""Tests for the timeline skeleton component.

The skeleton only renders its container and a placeholder; rendering does not
require an application route or request context.
"""

from pyhx.components import timeline


def test_timeline_renders_container_with_placeholder() -> None:
    html = str(timeline())

    assert 'class="hx-timeline"' in html
    assert "hx-timeline__placeholder" in html


def test_timeline_forwards_attributes() -> None:
    html = str(timeline(id="roadmap", class_="extra"))

    assert 'id="roadmap"' in html
    assert "extra" in html
