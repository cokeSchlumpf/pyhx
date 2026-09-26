import difflib
import html as htmllib
import re

import htpy as y
from markupsafe import Markup, escape

from pyhx.core import component
from pyhx.core.primitives import classnames

_TOKEN_RE = re.compile(r"\S+|\s+")

# HTML-mode markup: a start/end tag, a comment, or a declaration. Only a ``<``
# that actually begins one of these (``</`` or ``<`` + a letter, ``<!--``, ``<!``)
# is treated as a tag; a bare ``<`` in prose (``a < b``) is left in the text run so
# it can never swallow the run up to the next ``>`` as a phantom tag. Everything
# between two markup matches is a text run — decoded and word-tokenised separately.
_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>|<!--.*?-->|<![^>]*>", re.DOTALL)

# Block-level elements define a text run's structural context; inline elements
# (``b``, ``i``, ``a`` …) do not. Reworking a paragraph into a list item changes
# the block stack, so the text reads as moved/changed; bolding a word does not.
_BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "figure",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "ul",
    }
)
_VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
_TAG_NAME_RE = re.compile(r"</?\s*([a-zA-Z][a-zA-Z0-9]*)")


def _tokenize(text: str) -> list[str]:
    """Split into runs of non-whitespace + runs of whitespace.

    This preserves spacing exactly when the diff output is reassembled.
    """
    return _TOKEN_RE.findall(text)


def _tag_name(tag: str) -> str:
    match = _TAG_NAME_RE.match(tag)
    return match.group(1).lower() if match else ""


def _keyed_tokens(html: str) -> list[tuple[str, tuple, bool]]:
    """Split HTML into keyed ``(render, match_key, is_tag)`` tokens.

    Markup is split off at real tags (:data:`_HTML_TAG_RE`); everything between
    tags is a text run that is *entity-decoded first* and only then word-tokenised.
    Decoding up front means spellings that render identically collapse to the same
    tokens — ``&quot;``/``"``, ``&#39;``/``'`` and, crucially, ``&nbsp;`` versus a
    literal U+00A0 (which would otherwise fall on different token boundaries: the
    entity glues onto its word while the literal splits off as whitespace). Text
    tokens render *re-escaped*, so decoding never emits invalid markup.

    Text tokens are keyed by *(enclosing block-tag stack, decoded text)*, so
    identical text only matches across the two versions when its block context is
    the same: a paragraph reworked into a list item counts as changed (the text
    moved into a new block), while inline re-formatting leaves the block stack —
    and thus the match — intact. Tags key on themselves so like tags still align.
    """
    stack: list[str] = []
    out: list[tuple[str, tuple, bool]] = []

    def emit_text(raw: str) -> None:
        for tok in _TOKEN_RE.findall(htmllib.unescape(raw)):
            out.append((str(escape(tok)), ("text", tuple(stack), tok), False))

    pos = 0
    for match in _HTML_TAG_RE.finditer(html):
        if match.start() > pos:
            emit_text(html[pos : match.start()])
        tag = match.group()
        out.append((tag, ("tag", tag), True))
        name = _tag_name(tag)
        if name in _BLOCK_TAGS and name not in _VOID_TAGS:
            if tag.startswith("</"):
                if name in stack:  # pop to the matching open tag (tolerant)
                    while stack and stack.pop() != name:
                        pass
            else:
                stack.append(name)
        pos = match.end()
    if pos < len(html):
        emit_text(html[pos:])
    return out


def _inline_nodes(text: str) -> list[y.Node]:
    """Render a paragraph-local string, turning single ``\\n`` into ``<br>``.

    Paragraph boundaries (``\\n\\n``) are handled by the caller; this only
    deals with line breaks *within* a single paragraph.
    """
    parts = text.split("\n")
    nodes: list[y.Node] = []
    for i, part in enumerate(parts):
        if part:
            nodes.append(part)
        if i < len(parts) - 1:
            nodes.append(y.br)
    return nodes


def _html_diff_nodes(old: str, current: str) -> list[y.Node]:
    """Tag-aware, block-aware inline diff: mark changed *text*, never tags.

    Tokenises both sides into atomic tags + text words (see :func:`_keyed_tokens`
    for how text is keyed by its block context), diffs the streams, and
    reassembles so that ``<ins>`` / ``<del>`` wrap only contiguous runs of text —
    every tag flushes the open marker first. Tags thus stay intact and a marker
    never spans an element boundary (no ``<ins>`` straddling two paragraphs).
    Equal and inserted tags are emitted (together they are the *current*
    structure); deleted tags are dropped, so the output is valid current-
    structure markup with deleted text shown inline. Because text is keyed by its
    block stack, text moved into a new block (e.g. a paragraph turned into a list
    item) is marked even though the words themselves did not change.
    """
    a = _keyed_tokens(old)
    b = _keyed_tokens(current)
    sm = difflib.SequenceMatcher(
        a=[key for _, key, _ in a], b=[key for _, key, _ in b], autojunk=False
    )

    nodes: list[y.Node] = []

    def emit_marked(items: list[tuple[str, tuple, bool]], kind: str) -> None:
        run: list[str] = []

        def flush() -> None:
            if run:
                element = y.ins if kind == "ins" else y.del_
                nodes.append(
                    element(class_=f"hx-text-diff__{kind}")[Markup("".join(run))]
                )
                run.clear()

        for render, _key, is_tag in items:
            if is_tag:
                # A tag closes any open marker so ins/del never wrap or cross it.
                flush()
                # Inserted tags carry the new structure; deleted tags are dropped.
                if kind == "ins":
                    nodes.append(Markup(render))
            else:
                run.append(render)
        flush()

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            nodes.append(Markup("".join(render for render, _, _ in a[i1:i2])))
        elif tag == "insert":
            emit_marked(b[j1:j2], "ins")
        elif tag == "delete":
            emit_marked(a[i1:i2], "del")
        elif tag == "replace":
            emit_marked(a[i1:i2], "del")
            emit_marked(b[j1:j2], "ins")

    return nodes


@component
def text_diff(old: str, current: str, *, html: bool = False, **kwargs) -> y.Node:
    """Word-level inline diff between two strings, as a list of paragraphs.

    Computes a whitespace-preserving, word-level diff with
    ``difflib.SequenceMatcher`` and renders it as a ``hx-text-diff`` container
    of ``<p>`` paragraphs. Changed runs are wrapped in semantic ``<ins>`` /
    ``<del>`` elements carrying ``hx-text-diff__ins`` / ``hx-text-diff__del``
    classes, so the styling lives in CSS (design-system tokens) rather than
    inline styles.

    Newline handling mirrors prose: a blank line (``\\n\\n``) starts a new
    paragraph, while a single ``\\n`` becomes a ``<br>`` within the current
    paragraph. Inline markers may span ``<br>`` breaks but never cross a
    paragraph boundary.

    With ``html=True`` the inputs are treated as HTML (see :func:`_html_diff_nodes`):
    tags are tokenised atomically and only changed *text* is wrapped, so a marker
    never splits a tag nor spans an element boundary, and the structure follows
    the current markup (deleted tags are dropped). Only pass trusted markup. Tag-
    only changes (e.g. wrapping a word in ``<b>``) surface as structure, not as a
    text ins/del.

    Examples
    --------
    >>> text_diff("the quick brown fox", "the slow brown fox")
    >>> text_diff(old_comment, current_comment)
    >>> text_diff(old_body_html, current_body_html, html=True)
    """
    if html:
        return y.div(**classnames("hx-text-diff", **kwargs))[
            _html_diff_nodes(old, current)
        ]

    a = _tokenize(old)
    b = _tokenize(current)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)

    # Flatten opcodes into (kind, text) segments; a 'replace' becomes del+ins.
    segments: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            segments.append(("equal", "".join(a[i1:i2])))
        elif tag == "delete":
            segments.append(("del", "".join(a[i1:i2])))
        elif tag == "insert":
            segments.append(("ins", "".join(b[j1:j2])))
        elif tag == "replace":
            segments.append(("del", "".join(a[i1:i2])))
            segments.append(("ins", "".join(b[j1:j2])))

    paragraphs: list[list[y.Node]] = [[]]
    for kind, text in segments:
        # Each '\n\n' flushes the current paragraph and starts a new one.
        for ci, chunk in enumerate(text.split("\n\n")):
            if ci > 0:
                paragraphs.append([])
            inner = _inline_nodes(chunk)
            if not inner:
                continue
            if kind == "equal":
                paragraphs[-1].extend(inner)
            elif kind == "del":
                paragraphs[-1].append(y.del_(class_="hx-text-diff__del")[inner])
            else:
                paragraphs[-1].append(y.ins(class_="hx-text-diff__ins")[inner])

    para_nodes = [
        y.p(class_="hx-text-diff__line")[nodes] for nodes in paragraphs if nodes
    ]
    return y.div(**classnames("hx-text-diff", **kwargs))[para_nodes]
