from typing import Literal, Protocol

from htpy import Node

from ..request_context import RequestContext
from .nav import AppNavFn

Design = Literal["plain", "default", "canvas"]
"""Visual design a page template renders its components in.

- ``plain`` — the bare :class:`Skeleton`; components keep their default look.
- ``default`` — the :class:`~pyhx.page_templates.AppShell` design.
- ``canvas`` — white cards on a grey canvas with a top bar (``CanvasShell``).

Read it with :meth:`RequestContext.get_design` (components) or ``hx.design``
(app code). Branch only on designs that render differently and let every other
value fall through to the default rendering::

    if RequestContext.get_design() == "canvas":
        ...
"""


class PageTemplate(Protocol):
    design: Design = "plain"
    """The design this template renders in. Read via :meth:`RequestContext.get_design`."""

    async def __call__(
        self,
        *,
        request: RequestContext,
        app_title: str,
        page_title: str | None,
        body: Node,
        navigation: AppNavFn,
    ) -> Node:
        """
        app_title : the application's title.
        page_title: the page's title. May be omitted by page.
        body: The content of the page.
        navigation: The app's navigation, key's are slot names. E.g., `main`, `secondary`, ....
        """
        ...
