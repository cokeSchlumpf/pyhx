"""Page header component with optional secondary navigation.

A horizontal header that sits at the top of a page's main column. It carries
breadcrumbs and the page title on the left, page-level actions on the right,
and optionally a secondary navigation row below them.

The secondary navigation is intended for switching between related pages
within the same application area. It is rendered inside the page header so
the header's bottom border remains below the navigation.

The component renders inside a ``container(width="wide")`` so it aligns with
the page's main content column.

Designed to pair with :class:`pyhx.page_templates.AppShell`: the underlying
CSS makes the header sticky to the top of the viewport, offset by the
application-shell header.
"""

import htpy as y

from .container import ContainerWidth, container


class _PageHeader:
    """Callable and helper methods for the page-header component.

    Instantiated once below as the module-level :data:`page_header`.

    Call it like a function to render the complete header. Use
    :meth:`breadcrumbs` to build a breadcrumb trail and :meth:`navigation`
    to render the secondary navigation independently when required.
    """

    def __call__(
        self,
        *,
        breadcrumbs: y.Node | None = None,
        title: y.Node,
        actions: y.Node | None = None,
        navigation: y.Node | None = None,
        width: ContainerWidth = "wide",
    ) -> y.Node:
        """Render the page header.

        Parameters
        ----------
        breadcrumbs : Node, optional
            Breadcrumb trail rendered above the title. Build it with
            :meth:`breadcrumbs`. ``None`` omits the breadcrumb trail.
        title : Node
            Page title, typically an ``y.h1[...]`` element.
        actions : Node, optional
            Page-level actions rendered on the right side of the header.
            ``None`` omits the actions area content.
        navigation : Node, optional
            Secondary navigation rendered below the title row. Build it with
            :meth:`navigation` and :meth:`nav_item`.
            ``None`` omits the navigation row.
        width : ContainerWidth
            Width preset used to align the header with the page content.

        Examples
        --------
        >>> page_header(
        ...     title=y.h1["Page title"],
        ...     navigation=page_header.navigation(
        ...         page_header.nav_item(
        ...             "Overview",
        ...             href="/overview",
        ...             active=True,
        ...         ),
        ...         page_header.nav_item(
        ...             "Details",
        ...             href="/details",
        ...         ),
        ...         aria_label="Example views",
        ...     ),
        ... )
        """

        return y.div(class_="hx-page-header")[
            container(
                y.fragment[
                    y.div(class_="hx-page-header__header")[breadcrumbs, title],
                    y.div(class_="hx-page-header__actions")[actions],
                    navigation,
                ],
                width=width,
            )
        ]

    def breadcrumbs(self, *items: y.Node) -> y.Node:
        """Render the breadcrumb trail for the page header.

        Wraps the items in a ``<nav aria-label="Breadcrumb">`` and ``<ul>``
        following the W3C breadcrumb pattern. Each item becomes an ``<li>``.
        The visual separator between items is supplied by CSS, so screen
        readers do not announce it.

        Parameters
        ----------
        *items : Node
            Breadcrumb entries in order, from the topmost ancestor to the
            current page. Use anchors for navigable entries and plain text
            for the current page.

        Examples
        --------
        >>> page_header.breadcrumbs(
        ...     y.a(href="/")["Home"],
        ...     y.a(href="/library")["Library"],
        ...     "Current page",
        ... )
        """
        return y.nav(aria_label="Breadcrumb")[
            y.ul(class_="hx-page-header__breadcrumbs")[*[y.li[item] for item in items]]
        ]

    def navigation(
        self,
        *items: y.Node,
        aria_label: str = "Page navigation",
    ) -> y.Node:
        """Render the page header's secondary navigation."""

        return y.nav(
            class_="hx-page-header__navigation",
            aria_label=aria_label,
        )[y.ul(class_="hx-page-header__navigation-list")[*items,]]

    def nav_item(
        self,
        label: y.Node,
        *,
        href: str,
        active: bool = False,
        **kwargs: y.Attribute,
    ) -> y.Node:
        """Render one navigation link.

        Extra HTML and HTMX attributes are forwarded to the anchor.
        """

        if active:
            kwargs["aria_current"] = "page"

        return y.li(class_="hx-page-header__navigation-item")[
            y.a(
                href=href,
                **kwargs,
            )[label]
        ]


page_header = _PageHeader()
"""The page-header component singleton.

Call it like a function to render the complete header. Use
``page_header.breadcrumbs(...)`` for breadcrumbs and
``page_header.navigation(...)`` with
``page_header.nav_item(...)`` for secondary navigation.
"""
