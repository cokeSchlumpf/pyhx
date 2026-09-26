from textwrap import dedent

import htpy as y
import nh3
from markdown_it import MarkdownIt
from markupsafe import Markup

md = MarkdownIt("commonmark").enable(["table"])


def markdown(markdown: str) -> y.Node:
    """Render markdown as HTML.

    The input is :func:`textwrap.dedent`-ed before parsing so callers can pass
    indented triple-quoted strings that visually align with surrounding code
    without leaking the indentation into the rendered output (which would
    otherwise turn every paragraph into a code block).
    """

    html_str = md.render(dedent(markdown))
    clean_html_str = nh3.clean(html_str)
    return y.fragment[Markup(clean_html_str)]
