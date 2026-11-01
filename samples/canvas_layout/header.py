import htpy as y

from pyhx.core import RequestContext


def header_content() -> y.Node:
    """Evaluated per request: a static label, the link to the admin pages
    and the current user.

    The shell draws the separator line between the direct children.
    """
    return [
        y.span["Muster AG"],
        y.a(href="/admin", style="color: inherit; text-decoration: none;")[
            "Administration"
        ],
        y.span[RequestContext.get().user.display_name],
    ]
