"""Layout of an example page: what it shows, the code, the live viewer.

The code is cut from the example's own module between ``# docs:start <name>``
and ``# docs:end <name>`` (see :mod:`samples.components._snippets`), so the
code shown is the code that renders the viewer below it.
"""

from collections.abc import Sequence
from pathlib import Path

import htpy as y
from markupsafe import Markup

import pyhx.components as c
from samples.components._snippets import extract_region

STYLESHEET = "/static/css/document-viewer.css"
SCRIPT = "/static/js/document-viewer.js"

EXAMPLES: list[tuple[str, str, str]] = [
    ("/basic", "Basic viewer", "One document with the standard toolbar."),
    (
        "/documents",
        "Several documents",
        "Groups in the thumbnail rail, badges chosen by the app.",
    ),
    ("/marks", "Marks", "Colours and looks, the selected mark and its spotlight."),
    ("/notes", "Notes", "Pins, their content in the sidebar, HTMX on a pin."),
    (
        "/toolbar",
        "Custom toolbar",
        "Controls left out, reordered, the app's own controls.",
    ),
    ("/case", "Case page", "Everything together, as in the design template."),
]


def code(module_file: str, *regions: str) -> y.Node:
    """The regions of ``module_file`` as one highlighted code block."""
    source = Path(module_file).read_text()
    parts = [(name, extract_region(source, name), "python") for name in regions]
    return c.code(parts, max_height="28rem")


def example_page(
    *,
    title: str,
    intro: y.Node,
    code: y.Node,
    viewer: y.Node,
    height: str = "44rem",
    script: str | None = None,
) -> y.Node:
    """An example: title and explanation, the code, the live viewer below."""
    return y.div(class_="sample-example")[
        y.link(rel="stylesheet", href=STYLESHEET),
        y.link(rel="stylesheet", href="/static/css/sample.css"),
        c.breadcrumbs(y.a(href="/")["Document viewer"], title),
        y.h1[title],
        y.div(class_="sample-example__intro")[intro],
        code,
        y.div(class_="sample-example__frame", style=f"height: {height};")[viewer],
        y.script(src=SCRIPT),
        y.script[Markup(script)] if script else None,
    ]


def links(items: Sequence[tuple[str, str, str]] = EXAMPLES) -> y.Node:
    return y.ul(class_="sample-example__links")[
        (y.li[y.a(href=href)[name], " – ", text] for href, name, text in items)
    ]
