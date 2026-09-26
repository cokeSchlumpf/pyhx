"""Shared route-registration surface for :class:`WebApp` and :class:`WebAppRouter`."""

from typing import Protocol

from .fragment import FragmentFactory
from .page import PageDecoratorFactory


class WebAppRoutes(Protocol):
    """The route-registration surface shared by :class:`WebApp` and
    :class:`WebAppRouter`. Any helper that needs to register pages or
    fragments against "either an app or a router" — for example a
    component that attaches its own HTMX endpoints to whatever target
    the caller provides — should type its parameter as
    :class:`WebAppRoutes` so both classes are accepted.
    """

    page: PageDecoratorFactory
    fragment: FragmentFactory
