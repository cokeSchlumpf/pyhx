import htpy as y

from pyhx.core import component
from pyhx.core.primitives import classnames

from .button import button


@component
def dropdown_tags() -> y.Node:
    return y.details(**classnames(["dropdown", "hx-dropown-tags"]))[
        y.summary(id="summary_id")[y.span["Tag 1, Tag 2, Tag 3"]],
        y.div[y.div[y.input(type="text"), button("Add", appearance="primary")]],
    ]
