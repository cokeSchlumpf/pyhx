from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ..primitives import IconName, Path
from ..reflection_operators import inject_parameters
from ..request_context import RequestContext


@dataclass
class NavItem:
    label: str
    to: str | Path
    full_match: bool = True
    icon: IconName | None = None

    def is_active(self, ctx: RequestContext) -> bool:
        if ctx.request is None:
            return False
        try:
            current = Path(ctx.request.url.path)
            to = self.to if isinstance(self.to, Path) else Path(self.to)
            if self.full_match:
                return to == current

            return to.is_prefix_of(current)
        except Exception:  # noqa: BLE001 — prefix check is a guard; any failure = no match
            return False


Nav = list[NavItem] | dict[str, list[NavItem]]
NavFn = Callable[
    [RequestContext], Awaitable[Nav]
]  # TODO mw: needs to be PyHX-specific context.

AppNav = dict[str, Nav]  # Navigations for different slots (key is slot)
AppNavFn = dict[str, NavFn]  # Navigation factories for different slots (key is slit)


class NavFactory:
    def __init__(self, navigation: AppNavFn) -> None:
        self.navigation = navigation

    def __call__(
        self, slot: str = "main"
    ) -> Callable[[Callable[..., Awaitable[Nav]]], None]:
        def __call__(fn: Callable[..., Awaitable[Nav]]) -> None:
            async def __call_fn__(ctx: RequestContext) -> Nav:
                params = inject_parameters(fn, {RequestContext: ctx})
                return await fn(**params)

            self.navigation[slot] = __call_fn__

        return __call__

    def set(self, nav: Nav, slot: str = "main") -> None:
        """Sets a static navigation for the the provided slot. Default slot is `main`."""

        async def fn(_ctx: RequestContext) -> Nav:
            return nav

        self.navigation[slot] = fn
