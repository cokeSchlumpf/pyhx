from typing import Any, overload

from .page import Page
from .primitives import IconName, Path
from .templates import NavItem


@overload
def nav_item(
    page: Page,
    *,
    label: str | None = None,
    full_match: bool = False,
    params: dict[str, Any] | None = None,
    icon: IconName | None = None,
) -> NavItem: ...


@overload
def nav_item(
    label: str,
    *,
    to: str | Path,
    full_match: bool = False,
    icon: IconName | None = None,
) -> NavItem: ...


def nav_item(*args: Any, **kwargs: Any) -> NavItem:
    if args and isinstance(args[0], str):
        return _nav_item(*args, **kwargs)

    return _nav_item_from_page(*args, **kwargs)


def _nav_item_from_page(
    page: Page,
    *,
    label: str | None = None,
    full_match: bool = False,
    params: dict[str, Any] | None = None,
    icon: IconName | None = None,
) -> NavItem:
    return NavItem(
        label=label or page.title,
        to=page.path.format(**(params or {})),
        full_match=full_match,
        icon=icon or page.icon,
    )


def _nav_item(
    label: str, to: str | Path, full_match: bool = False, icon: IconName | None = None
) -> NavItem:
    return NavItem(label=label, to=to, full_match=full_match, icon=icon)
