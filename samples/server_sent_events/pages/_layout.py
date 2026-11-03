"""Layout of an example page: what it shows, the code, the live demo.

The code is cut from the example's own module between ``# docs:start <name>``
and ``# docs:end <name>`` (see :mod:`samples.components._snippets`), so the
code shown is the code that runs the demo below it.
"""

from collections.abc import Sequence
from pathlib import Path

import htpy as y

import pyhx.components as c
from samples.components._snippets import extract_region

EXAMPLES: list[tuple[str, str, str]] = [
    (
        "/countdown",
        "Countdown",
        "A stream of nodes and a named event, the end of the stream, an error.",
    ),
    (
        "/job",
        "Job progress",
        "A background job: current state first, several targets, resume, end.",
    ),
]


def code(module_file: str, *regions: str) -> y.Node:
    """The regions of ``module_file`` as one highlighted code block."""
    source = Path(module_file).read_text()
    parts = [(name, extract_region(source, name), "python") for name in regions]
    return c.code(parts, max_height="32rem")


def example_page(*, title: str, intro: y.Node, code: y.Node, demo: y.Node) -> y.Node:
    """An example: title and explanation, the live demo, the code below."""
    return y.div(class_="sample-example")[
        y.link(rel="stylesheet", href="/static/css/sample.css"),
        c.breadcrumbs(y.a(href="/")["Server-sent events"], title),
        y.h1[title],
        y.div(class_="sample-example__intro")[intro],
        y.div(class_="sample-example__demo")[demo],
        code,
    ]


def links(items: Sequence[tuple[str, str, str]] = EXAMPLES) -> y.Node:
    return y.ul(class_="sample-example__links")[
        (y.li[y.a(href=href)[name], " – ", text] for href, name, text in items)
    ]
