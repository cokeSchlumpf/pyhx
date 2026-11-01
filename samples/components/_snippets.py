"""Render named regions of a sample page's own source as code blocks.

Mark a region in a page module with fence comments::

    # docs:start all_appearances
    pill.container(...)
    # docs:end all_appearances

Bind the extractor to the module and render the region::

    src = snippets(__file__)
    ...
    src["all_appearances"]   # -> y.pre[y.code[<the source above, dedented>]]

The fenced lines are real, runnable source, so the demo and its snippet
cannot drift.

Matching is line-based: a ``# docs:start`` / ``# docs:end`` marker is found
wherever it appears as a comment, with no awareness of Python strings. Keep
markers as bare comments inside the page's element tree; don't place the
marker text inside a string literal in the same file.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import htpy as y

_START = re.compile(r"^\s*#\s*docs:start\s+(\S+)\s*$")
_END = re.compile(r"^\s*#\s*docs:end\s+(\S+)\s*$")


def extract_region(source: str, name: str) -> str:
    """Return the dedented source between the fences for ``name``.

    Excludes the fence lines and strips surrounding blank lines. Raises
    ``ValueError`` on an unbalanced or duplicated fence, ``KeyError`` when
    ``name`` is absent.
    """
    lines = source.splitlines()
    open_name: str | None = None
    captured: list[str] | None = None
    regions: dict[str, list[str]] = {}

    for line in lines:
        start = _START.match(line)
        end = _END.match(line)
        if start:
            if open_name is not None:
                raise ValueError(
                    f"docs:start {start.group(1)!r} inside open region "
                    f"{open_name!r}"
                )
            open_name = start.group(1)
            if open_name in regions:
                raise ValueError(f"duplicate docs region {open_name!r}")
            captured = []
        elif end:
            if open_name is None or end.group(1) != open_name:
                raise ValueError(f"unbalanced docs:end {end.group(1)!r}")
            regions[open_name] = captured or []
            open_name = None
            captured = None
        elif captured is not None:
            captured.append(line)

    if open_name is not None:
        raise ValueError(f"docs:start {open_name!r} has no matching docs:end")

    if name not in regions:
        raise KeyError(name)

    body = "\n".join(regions[name])
    return textwrap.dedent(body).strip("\n")


class Snippets:
    """Extractor bound to a single source file."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)

    def text(self, name: str) -> str:
        """Return the dedented source text for ``name`` (re-read each call)."""
        return extract_region(self._path.read_text(encoding="utf-8"), name)

    def __getitem__(self, name: str) -> y.Element:
        return y.pre[y.code[self.text(name)]]


def snippets(path: str) -> Snippets:
    """Bind a :class:`Snippets` extractor to ``path`` (pass ``__file__``)."""
    return Snippets(path)
