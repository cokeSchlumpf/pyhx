"""Zoomable timeline with icon markers and drill-down details.

Skeleton only: the component renders an empty ``hx-timeline`` container with a
placeholder. Properties (time range, zoom level, events) and the fragment
endpoints (zoom, details) are added as the component grows.
"""

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames


class _Timeline:
    """Public entry point for the timeline primitive (the :data:`timeline`
    singleton).

    Sub-builders for the timeline's parts (lanes, events, …) are exposed as
    methods so fragment endpoints can re-render them individually.
    """

    def __call__(self, **kwargs: y.Attribute) -> y.Node:
        """Render the timeline.

        Args:
            **kwargs: Extra HTML attributes forwarded to the outer ``<div>``.
        """
        return y.div(**classnames("hx-timeline", **kwargs))[self.placeholder()]

    def placeholder(self) -> y.Node:
        """Render the placeholder shown until the timeline has real content."""
        return y.div(class_="hx-timeline__placeholder")["Timeline"]


@component
def timelines() -> y.Node:
    """Anchor for the timeline's fragment endpoints (zoom, details), mounted
    under ``/_components/timelines/...``."""
    return y.fragment[""]


timeline = _Timeline()
