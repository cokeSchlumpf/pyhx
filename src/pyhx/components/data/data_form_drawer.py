from collections.abc import Awaitable, Callable

import htpy as y
from pydantic import BaseModel

from pyhx.core.fragment import FragmentResult
from pyhx.core.primitives import htmx
from pyhx.core.webapp_routes import WebAppRoutes
from pyhx.i18n import _

from ..layouts import DRAWER_CONTENT_ID, close_drawer, drawer_content
from ..primitives import button
from ..variants import FormSize, LabelPosition
from .data_form import DataForm


def _resolve(label: str | Callable[[], str] | None) -> str | None:
    return label() if callable(label) else label


class DataFormDrawer[T: BaseModel]:
    def __init__(
        self,
        *,
        routes: WebAppRoutes,
        name: str,
        type: type[T],
        handle_submit: Callable[[T], Awaitable[FragmentResult]],
        submit_label: str | Callable[[], str] | None = None,
        field_order: list[str] | None = None,
        cancel_label: str | Callable[[], str] | None = None,
        dialog_title: str | Callable[[], str] | None = None,
        size: FormSize | None = None,
        label_position: LabelPosition | None = None,
    ) -> None:
        """A :class:`DataForm` in a drawer, with cancel and a delete slot.

        ``size`` is passed to the :class:`DataForm`: ``None`` (default) sizes
        it by its place, which in the canvas design makes it compact like
        every form in a drawer; ``"md"`` keeps the full size.
        ``label_position`` is passed to the :class:`DataForm` as well.
        """
        # Kept unresolved: a callable or a default is resolved at render time,
        # in the language of the request.
        self.cancel_label = cancel_label
        self.dialog_title = dialog_title

        self.form = DataForm[T](
            routes=routes,
            name=name,
            type=type,
            handle_submit=handle_submit,
            submit_label=submit_label,
            field_order=field_order,
            size=size,
            label_position=label_position,
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
        cancel_label = cancel_label or _resolve(self.cancel_label) or _("Cancel")
        # Translators: default title of the drawer with the edit form.
        dialog_title = dialog_title or _resolve(self.dialog_title) or _("Edit")

        # The classes let the canvas design lay the form out as a scrolling
        # body above a fixed footer (data_form.css); the submit button stays
        # inside the form, so validation keeps its disabled state current.
        return drawer_content(
            y.div(class_="hx-data-form-drawer")[
                await self.form.render(value),
                y.div(class_="hx-data-form__actions hx-data-form-drawer__actions")[
                    y.div(class_="hx-data-form-drawer__cancel")[
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
                        y.div(class_="hx-data-form-drawer__delete")[delete_button],
                    ]
                    if delete_button is not None
                    else None,
                ],
            ],
            title=dialog_title,
        )
