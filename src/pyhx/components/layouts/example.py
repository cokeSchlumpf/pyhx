"""Documentation example component: a live preview above a c.code terminal.

The terminal (part tabs, line numbers, copy, fragment switching, highlighting)
lives in :mod:`pyhx.components.layouts.code`; this component only adds the
preview and the shared outer frame.
"""

from __future__ import annotations

from collections.abc import Sequence

import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames

from .code import CodePartArg
from .code import code as code_block


@component
def example(
    *preview: y.Node,
    code: Sequence[CodePartArg],
    copy: bool = True,
    max_height: str | None = "24rem",
    **kwargs,
) -> y.Node:
    """A documentation example: a live preview over a part-switchable code block.

    Parameters
    ----------
    *preview
        The rendered example — any htpy node(s).
    code
        Ordered parts forwarded to :func:`pyhx.components.code`; each is
        ``(label, source)`` or ``(label, source, lang)``.
    copy
        Show the copy button (default True).
    max_height
        Code-area max height before it scrolls (``None`` = no cap).

    Examples
    --------
    >>> example(
    ...     button("Save", appearance="primary"),
    ...     code=[("code", 'button("Save")', "python")],
    ... )
    """
    return y.figure(**classnames("hx-example", **kwargs))[
        y.div(class_="hx-example__preview")[*preview],
        code_block(code, copy=copy, max_height=max_height),
    ]
