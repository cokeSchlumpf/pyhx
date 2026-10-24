import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames


@component
def meta(*items: y.Node, **kwargs) -> y.Node:
    """A line of metadata, its items separated by a dot.

    ``meta("Eingang 15.03.2026", "12 Seiten")`` reads "Eingang 15.03.2026 ·
    12 Seiten". The dot comes from CSS: it looks the same everywhere, screen
    readers skip it, and when the line wraps it stays at the end of the
    line. The component takes the font size and colour of where it is
    placed, e.g. a ``card.subtitle`` or the description of a list row.

    Parameters
    ----------
    *items : Node
        The entries, in order. An entry can be more than text, e.g.
        ``["Fall ", y.strong["IV-2026-0142"]]`` (``strong`` renders as a
        slightly darker value, not bold) or a link.

    Examples
    --------
    >>> meta("Eingang 15.03.2026", "12 Seiten", "1 Feld zu prüfen")
    >>> meta(["Fall ", y.strong["IV-2026-0142"]], ["Geb. ", y.strong["14.08.1978"]])
    """
    # The spaces between the items are the line-break opportunities; the
    # dot itself is drawn after each item but the last.
    entries: list[y.Node] = []
    for index, item in enumerate(items):
        if index:
            entries.append(" ")
        entries.append(y.span(class_="hx-meta__item")[item])

    return y.span(**classnames("hx-meta", **kwargs))[entries]
