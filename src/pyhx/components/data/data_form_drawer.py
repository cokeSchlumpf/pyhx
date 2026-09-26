from collections.abc import Awaitable, Callable

import htpy as y
from pydantic import BaseModel

from pyhx.core.fragment import FragmentResult
from pyhx.core.primitives import htmx, styles
from pyhx.core.webapp_routes import WebAppRoutes

from ..layouts import DRAWER_CONTENT_ID, close_drawer, drawer_content
from ..primitives import button
from .data_form import DataForm


class DataFormDrawer[T: BaseModel]:
    def __init__(
        self,
        *,
        routes: WebAppRoutes,
        name: str,
        type: type[T],
        handle_submit: Callable[[T], Awaitable[FragmentResult]],
        submit_label: str | None = None,
        field_order: list[str] | None = None,
        cancel_label: str | None = None,
        dialog_title: str | None = None,
    ) -> None:
        self.cancel_label = cancel_label or "Cancel"
        self.dialog_title = dialog_title or "Edit"

        self.form = DataForm[T](
            routes=routes,
            name=name,
            type=type,
            handle_submit=handle_submit,
            submit_label=submit_label,
            field_order=field_order,
        )

    async def render_drawer(
        self,
        value: T | None = None,
        delete_button: y.Node | None = None,
        cancel_label: str | None = None,
        dialog_title: str | None = None,
    ) -> y.Node:
        """Render the form inside a drawer, with Cancel and an optional delete slot.

        ``delete_button`` is a fully-rendered node supplied by the caller (who
        owns the data source and knows how to wire deletion) — this component
        only places it, the same way ``DataForm.render``'s own ``actions``
        slot works. ``None`` (default) omits the divider and the slot entirely.
        """
        cancel_label = cancel_label or self.cancel_label
        dialog_title = dialog_title or self.dialog_title

        return drawer_content(
            y.div(**styles("px-md", "items-stretch", "flex-col"))[
                await self.form.render(value),
                y.div(class_="hx-data-form__actions")[
                    y.div(**styles("mt-sm"))[
                        button(
                            cancel_label,
                            **htmx(
                                hx_post=close_drawer.url(),
                                hx_target=f"#{DRAWER_CONTENT_ID}",
                                hx_swap="none",
                                hx_vals={"id": DRAWER_CONTENT_ID},
                            ),
                        )
                    ],
                    y.fragment[
                        y.hr,
                        y.div(**styles("mt-sm"))[delete_button],
                    ]
                    if delete_button is not None
                    else None,
                ],
            ],
            title=dialog_title,
        )
