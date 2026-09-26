import htpy as y
from htpy import a, div, h3, li, nav, ul

from ..request_context import RequestContext
from .nav import AppNavFn, NavItem


class NavRenderer:
    """Helper for rendering a navigation slot.

    Subclass and override any of the hooks (``render_item``, ``render_group``,
    ``render_flat``, ``render_root``, ``render_empty``) to customize the
    markup. The base class ships working defaults that produce simple
    ``<nav>…</nav>`` HTML.

    When the navigation factory returns a dict, each ``(label, items)`` entry
    is rendered as a labeled group — except when ``label`` is an empty
    string (``""``), in which case those items are rendered as a flat,
    ungrouped list (no ``<h3>``, no group wrapper). This lets a dict mix
    ungrouped and grouped items in the same navigation; ungrouped items
    appear in their natural dict position relative to the groups.
    """

    async def __call__(
        self,
        *,
        slot: str,
        ctx: RequestContext,
        navigation: AppNavFn,
    ) -> y.Node:
        factory = navigation.get(slot)
        if factory is None:
            return self.render_empty(slot=slot)

        resolved = await factory(ctx)

        if isinstance(resolved, dict):
            sections: list[y.Node] = []
            for label, items in resolved.items():
                in_group = bool(label)
                # Compute active state once per item; reused for the group's
                # has_active flag below.
                active_states = [item.is_active(ctx) for item in items]
                rendered = [
                    self.render_item(
                        item=item,
                        is_active=is_active,
                        in_group=in_group,
                    )
                    for item, is_active in zip(items, active_states)
                ]
                # Empty-string label is the convention for "ungrouped" items:
                # render them as a flat list (no <h3>, no group wrapper).
                if in_group:
                    sections.append(
                        self.render_group(
                            label=label,
                            items=rendered,
                            has_active=any(active_states),
                        )
                    )
                else:
                    sections.append(self.render_flat(items=rendered))
        else:
            sections = [
                self.render_flat(
                    items=[
                        self.render_item(
                            item=item,
                            is_active=item.is_active(ctx),
                            in_group=False,
                        )
                        for item in resolved
                    ],
                )
            ]

        return self.render_root(slot=slot, sections=sections)

    def render_item(
        self,
        *,
        item: NavItem,
        is_active: bool,
        in_group: bool,
    ) -> y.Node:
        return li[
            a(
                href=str(item.to),
                class_="active" if is_active else None,
            )[item.label]
        ]

    def render_group(
        self,
        *,
        label: str,
        items: list[y.Node],
        has_active: bool,
    ) -> y.Node:
        return div[h3[label], ul[items]]

    def render_flat(self, *, items: list[y.Node]) -> y.Node:
        return ul[items]

    def render_root(self, *, slot: str, sections: list[y.Node]) -> y.Node:
        return nav[sections]

    def render_empty(self, *, slot: str) -> y.Node:
        return y.fragment[[]]
