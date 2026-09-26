# src/pyhx/components/layouts/code.py
"""Source-code component: a dark, terminal-styled viewer with part tabs, line
numbers, a copy button, and optional per-part syntax highlighting.

Parts are switched server-side via an htmx fragment: a shared ``CodeConfig``
(all the snippets + their languages) travels to the client in a hidden input and
back to the fragment, which re-renders the shell with the requested part active.
The only client JavaScript is the clipboard copy button (see ``pyhx.code.js``).
"""

from __future__ import annotations

from collections.abc import Sequence

import htpy as y
from pydantic import BaseModel
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import STANDARD_TYPES
from pygments.util import ClassNotFound

from pyhx.components.primitives.button import button
from pyhx.core import RequestContext, component
from pyhx.core.primitives import classnames, htmx

CodePartArg = tuple[str, str] | tuple[str, str, str | None]

# lang values that mean "render plain, do not highlight".
_PLAIN_LANGS: set[str | None] = {None, "none", "plaintext", "text"}


class CodePart(BaseModel):
    label: str
    source: str
    lang: str | None = None


class CodeConfig(BaseModel):
    parts: list[CodePart]
    # Named `show_copy` rather than `copy` so it doesn't shadow BaseModel.copy()
    # (which emits a UserWarning at class-definition time).
    show_copy: bool


# Form field the hidden config input is submitted under, read back by the
# fragment. Keep in sync with the fragment handler below.
_CFG_FIELD = "hx_code__cfg"


def _token_class(ttype) -> str:  # type: ignore[no-untyped-def]
    """Pygments short CSS class for a token type (walk parents until known), so
    the emitted classes match the generated code-highlight.css."""
    t = ttype
    while t not in STANDARD_TYPES:
        if t.parent is None:
            return ""
        t = t.parent
    return STANDARD_TYPES[t]


def _plain_lines(source: str) -> list[y.Node]:
    return [y.span(class_="hx-code__line")[line] for line in source.split("\n")]


def _highlighted_lines(source: str, lang: str) -> list[y.Node]:
    """Lex with Pygments and rebuild per-line spans with token spans inside,
    re-applying each token's class across newlines so multiline tokens (triple-
    quoted strings) stay valid and every source line is its own hx-code__line."""
    lexer = get_lexer_by_name(lang)
    lines: list[list[y.Node]] = [[]]
    for ttype, value in lex(source, lexer):
        cls = _token_class(ttype)
        pieces = value.split("\n")
        for i, piece in enumerate(pieces):
            if i > 0:
                lines.append([])
            if piece:
                lines[-1].append(y.span(class_=cls)[piece] if cls else piece)
    # Pygments appends a trailing newline -> drop the resulting empty last line
    # so the line count matches the plain path for the same source.
    if len(lines) > 1 and not lines[-1]:
        lines.pop()
    return [y.span(class_="hx-code__line")[parts] for parts in lines]


def _render_lines(source: str, lang: str | None) -> list[y.Node]:
    # Normalize a single trailing newline so the plain and highlighted paths
    # produce the same line count (Pygments always emits a trailing newline,
    # which _highlighted_lines drops). Callers passing raw, unstripped source
    # therefore get consistent results either way.
    source = source.removesuffix("\n")
    if lang in _PLAIN_LANGS:
        return _plain_lines(source)
    assert lang is not None  # _PLAIN_LANGS includes None; mypy narrowing
    try:
        return _highlighted_lines(source, lang)
    except ClassNotFound:
        return _plain_lines(source)


def _panel(part: CodePart) -> y.Node:
    return y.pre(class_="hx-code__panel")[y.code[_render_lines(part.source, part.lang)]]


def _copy_button() -> y.Node:
    return button(
        icon="copy",
        aria_label="Copy code",
        class_="hx-code__copy",
        appearance="neutral",
        variant="glass",
        size="sm",
    )


def _tab(label: str, active: str) -> y.Node:
    classes = "hx-code__tab" + (" is-active" if label == active else "")
    return button(  # type: ignore[arg-type]
        label,
        class_=classes,
        appearance="neutral",
        variant="glass",
        size="sm",
        **htmx(
            hx_post=serve_part.url(),
            hx_target="closest .hx-code__shell",
            hx_swap="innerHTML transition:true",
            hx_vals={"part": label},
            hx_include="closest .hx-code",
        ),
    )


def _shell(cfg: CodeConfig, active: str) -> y.Node:
    """The swappable inner markup: an optional switcher bar + the active part's
    panel. Shared by the initial render and the fragment so they cannot drift.

    The bar is rendered only when there are tabs (2+ parts). With a single part
    there is no bar — the code starts at the top — and the copy button (if any)
    floats top-right via a zero-height sticky dock."""
    part = next(p for p in cfg.parts if p.label == active)
    multi = len(cfg.parts) > 1

    children: list[y.Node] = []
    if multi:
        children.append(
            y.div(class_="hx-code__bar")[
                *[_tab(p.label, active) for p in cfg.parts],
                _copy_button() if cfg.show_copy else None,
            ]
        )
    elif cfg.show_copy:
        children.append(y.div(class_="hx-code__copy-dock")[_copy_button()])
    children.append(y.div(class_="hx-code__viewport")[_panel(part)])
    return children


def _normalize(parts: Sequence[CodePartArg]) -> list[CodePart]:
    items: list[CodePart] = []
    for p in parts:
        if len(p) == 3:
            label, source, lang = p
        else:
            label, source = p
            lang = None
        items.append(CodePart(label=label, source=source, lang=lang))
    return items


@component
def code(
    parts: Sequence[CodePartArg],
    *,
    copy: bool = True,
    max_height: str | None = "24rem",
    **kwargs,
) -> y.Node:
    """A dark, terminal-styled source viewer with part tabs, line numbers, a copy
    button, and optional per-part syntax highlighting.

    Parameters
    ----------
    parts
        Ordered parts. Each is ``(label, source)`` for plain text, or
        ``(label, source, lang)`` to highlight with that language. ``lang`` of
        ``None`` / ``"none"`` / ``"plaintext"`` / ``"text"`` (or an unknown
        language) renders plain. The first part is shown by default.
    copy
        Show a copy button that copies the active part (default True).
    max_height
        CSS length capping the height; it scrolls past that. ``None`` removes
        the cap.

    Examples
    --------
    >>> code([("code", 'button("Save")', "python")])
    """
    items = _normalize(parts)
    if not items:
        raise ValueError("code() requires at least one part")
    labels = [p.label for p in items]
    if len(set(labels)) != len(labels):
        raise ValueError("code() parts must have unique labels")

    cfg = CodeConfig(parts=items, show_copy=copy)
    active = cfg.parts[0].label

    attrs: dict = dict(classnames("hx-code", **kwargs))
    if max_height is not None:
        attrs["style"] = f"--hx-code-max-height: {max_height};"

    return y.div(**attrs)[
        # Shared config, outside the shell so it survives every swap.
        y.input(type="hidden", name=_CFG_FIELD, value=cfg.model_dump_json()),
        y.div(class_="hx-code__shell")[_shell(cfg, active)],
    ]


@code.fragments.post("/part")
async def serve_part() -> y.Node:
    """Re-render the shell for the requested part. Reads the shared config (which
    the tab buttons hx-include) and the clicked ``part`` from the form."""
    request = RequestContext.get().request
    assert request is not None
    form = await request.form()
    cfg = CodeConfig.model_validate_json(str(form[_CFG_FIELD]))
    active = str(form["part"])
    return _shell(cfg, active)
