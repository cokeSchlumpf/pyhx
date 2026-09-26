"""Sample app showcasing pyhx components and their variants.

Run from the repo root, e.g.::

    uvicorn samples.components.main:app --reload

Each page demos one component at all of its variants. Pages are declared
in sibling modules under :mod:`samples.components.pages` and attached
via :class:`WebAppRouter`.
"""

import htpy as y
import pyhx.components as c

from pyhx.core import WebApp
from pyhx.page_templates import AppShell

from samples.components.pages import (
    bubble,
    buttons,
    conditional_select,
    data_table,
    drawer_radio,
    drawer_select,
    dropdown,
    file_dropzone,
    focus_list,
    forms,
    gantt,
    grid,
    icons,
    messages,
    metric_tile,
    notification_badge,
    notifications,
    pills,
    segment_control,
    table,
    taglist,
    text_diff,
    wysiwyg_editor,
)


hx = WebApp(title="Components", default_page_template=AppShell(mode="app"))

hx.include_router(pills.router)
hx.include_router(bubble.router)
hx.include_router(notification_badge.router)
hx.include_router(buttons.router)
hx.include_router(grid.router)
hx.include_router(icons.router)
hx.include_router(data_table.router)
hx.include_router(segment_control.router)
hx.include_router(table.router)
hx.include_router(dropdown.router)
hx.include_router(file_dropzone.router)
hx.include_router(drawer_select.router)
hx.include_router(drawer_radio.router)
hx.include_router(conditional_select.router)
hx.include_router(focus_list.router)
hx.include_router(forms.router)
hx.include_router(gantt.router)
hx.include_router(taglist.router)
hx.include_router(messages.router)
hx.include_router(metric_tile.router)
hx.include_router(text_diff.router)
hx.include_router(notifications.router)
hx.include_router(wysiwyg_editor.router)


@hx.page("/", title="Home")
async def home() -> y.Node:
    return c.container(
        y.article[
            y.h1["Components"],
            y.p[
                "Simple showcase of the components shipped with pyhx. ",
                "Each page below renders one component at every supported variant.",
            ],
            y.ul[
                y.li[
                    y.a(href=pills.pills_page.url())["Pill"],
                    " — short status label (1 axis: ",
                    y.code["appearance"],
                    ")",
                ],
                y.li[
                    y.a(href=notification_badge.notification_badge_page.url())[
                        "Notification Badge"
                    ],
                    " — count bubble overlaid on any wrapped element.",
                ],
                y.li[
                    y.a(href=bubble.bubble_page.url())["Bubble"],
                    " — full-width rounded container with a tinted surface ",
                    "(1 axis: ",
                    y.code["appearance"],
                    "; ",
                    y.code["color"],
                    " / ",
                    y.code["text_color"],
                    " overrides)",
                ],
                y.li[
                    y.a(href=buttons.buttons_page.url())["Button"],
                    " — actions (3 axes: ",
                    y.code["appearance"],
                    " × ",
                    y.code["variant"],
                    " × ",
                    y.code["size"],
                    " + icons)",
                ],
                y.li[
                    y.a(href=grid.grid_page.url())["Grid"],
                    " — CSS layout utility for any container (",
                    y.code["hx-grid"],
                    " + span / align helpers)",
                ],
                y.li[
                    y.a(href=icons.icons_page.url())["Icon"],
                    " — every feather icon name in the ",
                    y.code["IconName"],
                    " literal union",
                ],
                y.li[
                    y.a(href=data_table.data_table_page.url())["Data Table"],
                    " — stub component, exercises the ",
                    y.code["WebAppRoutes"],
                    " registration flow",
                ],
                y.li[
                    y.a(href=segment_control.segment_control_page.url())[
                        "Segment Control"
                    ],
                    " — radio-group as a connected button bar (1 axis: ",
                    y.code["size"],
                    ")",
                ],
                y.li[
                    y.a(href=dropdown.dropdown_page.url())["Dropdown"],
                    " — single-select dropdown built on ",
                    y.code["<details>"],
                    " + radio inputs",
                ],
                y.li[
                    y.a(href=file_dropzone.file_dropzone_page.url())[
                        "File Dropzone"
                    ],
                    " — drag-and-drop file picker with a click-to-browse fallback",
                ],
                y.li[
                    y.a(href=drawer_select.drawer_select_page.url())[
                        "Drawer Select"
                    ],
                    " — multi-select for long option pools via a filterable ",
                    "drawer",
                ],
                y.li[
                    y.a(href=drawer_radio.drawer_radio_page.url())[
                        "Drawer Radio"
                    ],
                    " — single-select sibling; click-to-commit in the drawer",
                ],
                y.li[
                    y.a(href=conditional_select.conditional_select_page.url())[
                        "Conditional Select"
                    ],
                    " — toggle between all/none and a specific set; reveals a ",
                    "configurable picker (",
                    y.code["drawer"],
                    " / ",
                    y.code["dropdown"],
                    " / ",
                    y.code["checkbox"],
                    ")",
                ],
                y.li[
                    y.a(href=focus_list.focus_list_page.url())["Focus List"],
                    " — single-focus list; select one row to lift it while the ",
                    "rest dim and lock (2 variants: ",
                    y.code["cards"],
                    " / ",
                    y.code["plain"],
                    ")",
                ],
                y.li[
                    y.a(href=forms.forms_page.url())["Forms"],
                    " — skeleton page for form-component experiments",
                ],
                y.li[
                    y.a(href=gantt.gantt_page.url())["Gantt"],
                    " — blank scaffold page for the ",
                    y.code["gantt"],
                    " skeleton component",
                ],
                y.li[
                    y.a(href=messages.messages_page.url())["Messages"],
                    " — inline alert / callout box (1 axis: ",
                    y.code["appearance"],
                    "); buttons inside adopt the message colour",
                ],
                y.li[
                    y.a(href=metric_tile.metric_tile_page.url())["Metric Tile"],
                    " — single dashboard metric as a ",
                    y.code["<dl>"],
                    " (1 axis: ",
                    y.code["appearance"],
                    ", plus ",
                    y.code["purple"],
                    ")",
                ],
                y.li[
                    y.a(href=notifications.notifications_page.url())["Notifications"],
                    " — floating toast stack appended via HTMX OOB ",
                    y.code["beforeend:#hx-notifications"],
                ],
                y.li[
                    y.a(href=table.table_page.url())["Table"],
                    " — blank scaffold page for the ",
                    y.code["table"],
                    " component",
                ],
                y.li[
                    y.a(href=taglist.taglist_page.url())["Taglist"],
                    " — free-text tag input composed from ",
                    y.code["pill.container"],
                    " + ",
                    y.code["pill.button"],
                ],
            ],
        ]
    )


hx.navigation.set(
    [
        hx.nav_item(home, icon="home", full_match=True),
        hx.nav_item(pills.pills_page, icon="circle"),
        hx.nav_item(bubble.bubble_page, icon="message-circle"),
        hx.nav_item(notification_badge.notification_badge_page, icon="bell"),
        hx.nav_item(buttons.buttons_page, icon="square"),
        hx.nav_item(grid.grid_page, icon="grid"),
        hx.nav_item(icons.icons_page, icon="star"),
        hx.nav_item(data_table.data_table_page, icon="list"),
        hx.nav_item(segment_control.segment_control_page, icon="toggle-left"),
        hx.nav_item(table.table_page, icon="columns"),
        hx.nav_item(dropdown.dropdown_page, icon="chevron-down"),
        hx.nav_item(file_dropzone.file_dropzone_page, icon="upload-cloud"),
        hx.nav_item(drawer_select.drawer_select_page, icon="sliders"),
        hx.nav_item(drawer_radio.drawer_radio_page, icon="disc"),
        hx.nav_item(conditional_select.conditional_select_page, icon="filter"),
        hx.nav_item(focus_list.focus_list_page, icon="layers"),
        hx.nav_item(forms.forms_page, icon="edit-3"),
        hx.nav_item(gantt.gantt_page, icon="bar-chart-2"),
        hx.nav_item(messages.messages_page, icon="message-square"),
        hx.nav_item(metric_tile.metric_tile_page, icon="activity"),
        hx.nav_item(notifications.notifications_page, icon="bell"),
        hx.nav_item(taglist.taglist_page, icon="tag"),
        hx.nav_item(text_diff.text_diff_page, icon="git-pull-request"),
        hx.nav_item(wysiwyg_editor.wysiwyg_editor_page, icon="edit-3"),
    ]
)


app = hx.create_app()
