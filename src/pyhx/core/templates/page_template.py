from typing import Protocol

from htpy import Node

from ..request_context import RequestContext
from .nav import AppNavFn


class PageTemplate(Protocol):
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
