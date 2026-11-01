"""Inline editing of single values — show a value, edit it in place, save it.

:class:`InlineEdit` shows one value of a record (label, value, optional hint
and source) with an edit button. The button loads a small form into the item;
saving validates the input against a Pydantic model and hands it to the app's
``save`` callback, after which the item shows the saved value again. Errors
stay at the field. Cancelling (Esc or the cancel button) drops the form in the
browser, without a request.

The form controller is a :class:`~pyhx.components.data.HeadlessForm`; this
module adds the display mode, the edit fragment and the layout. The server
keeps no state: the record's ``key`` travels in the query string of the edit
and submit requests, the open/closed state lives in the browser
(``pyhx.inline-edit.js``).

Only one item of a group is in edit mode at a time: opening one cancels the
open one. A group is the nearest ancestor carrying
``data-hx-inline-edit-group``; items without one share the page.
"""

import datetime
import re
import types
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any, Union, get_args, get_origin

import htpy as y
from commons.string_operators import to_kebabcase, to_title_case
from fastapi import HTTPException
from pydantic import BaseModel

from pyhx.core.fragment import FragmentResponse
from pyhx.core.primitives import htmx
from pyhx.core.primitives.lazy_text import Text
from pyhx.core.request_context import RequestContext
from pyhx.core.webapp_routes import WebAppRoutes
from pyhx.i18n import _, _l

from ..primitives.button import button
from ..primitives.form_field import form_field
from .headless_form import FormRenderContext, HeadlessForm

_SAVE = _l("Save")
_CANCEL = _l("Cancel")
_SHORTCUTS = _l("Esc cancels · ↵ saves")

_UNSAFE_ID_CHARS = re.compile(r"[^A-Za-z0-9_-]")


def _id_part(key: str) -> str:
    """Encode ``key`` for an element id: unsafe characters become ``_<hex>_``,
    so different keys never share an id."""
    return _UNSAFE_ID_CHARS.sub(lambda m: f"_{ord(m.group()):x}_", key)


def _unwrap_optional(annotation: Any) -> Any:
    """``X | None`` → ``X``; other annotations unchanged."""
    if get_origin(annotation) in (Union, types.UnionType):
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _input_type(annotation: Any) -> str:
    """HTML input type for a field annotation: number, date or text."""
    annotation = _unwrap_optional(annotation)
    if annotation is bool:
        return "text"
    if isinstance(annotation, type) and issubclass(annotation, int | float | Decimal):
        return "number"
    if annotation is datetime.date:
        return "date"
    return "text"


def _input_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)


class InlineEdit[T: BaseModel]:
    """A single value of a record, shown with an edit button and edited in place.

    Generic over the model ``T`` that holds the value: one field, or a few
    that belong together (e.g. a degree and a date). One instance per kind of
    value; the record is chosen per render by its ``key``.

    Parameters
    ----------
    routes : WebAppRoutes
        App or router the edit and submit fragments are registered on.
    name : str
        Unique name of the value; part of the fragment paths and element ids.
    type : type[T]
        Pydantic model the input is validated against.
    label : Text
        Visible label of the value.
    load : Callable[[str], Awaitable[T]]
        Returns the current value of the record ``key``; called when the edit
        form opens and by :meth:`render` without a value.
    save : Callable[[str, T], Awaitable[T]]
        Saves the validated value of the record ``key`` and returns the value
        to display. May raise :class:`pydantic.ValidationError`; its messages
        are shown at the fields.
    display : Callable[[T], y.Node], optional
        Formats the value in display mode. Default: the field's value (the
        values joined by ", " for several fields), "–" when empty.
    source : Callable[[str, T], y.Node], optional
        Where the value comes from (e.g. a link to the page of a document),
        shown below the value.
    hint : Callable[[str, T], y.Node], optional
        A short remark next to the label (e.g. "uncertain reading"); return
        ``None`` for no hint.
    fields : Callable[[FormRenderContext[T]], y.Node], optional
        Renders the controls of the form. Default: one ``form_field`` per
        model field with a text, number or date input. Show the errors with
        ``form_field(error_text=ctx.visible_errors.get(name))``.
    save_label, cancel_label : Text
        Labels of the save and cancel buttons; translated by default.
    edit_label : Text, optional
        Accessible name of the edit button. Default: "Edit <label>",
        translated.
    shortcuts_hint : Text | None
        Keyboard hint below the form, translated by default; ``None`` hides
        it.
    """

    def __init__(
        self,
        *,
        routes: WebAppRoutes,
        name: str,
        type: type[T],
        label: Text,
        load: Callable[[str], Awaitable[T]],
        save: Callable[[str, T], Awaitable[T]],
        display: Callable[[T], y.Node] | None = None,
        source: Callable[[str, T], y.Node] | None = None,
        hint: Callable[[str, T], y.Node] | None = None,
        fields: Callable[[FormRenderContext[T]], y.Node] | None = None,
        save_label: Text = _SAVE,
        cancel_label: Text = _CANCEL,
        edit_label: Text | None = None,
        shortcuts_hint: Text | None = _SHORTCUTS,
    ) -> None:
        self.name = to_kebabcase(name)
        self.type = type
        self.label = label
        self._load = load
        self._save = save
        self._display = display
        self._source = source
        self._hint = hint
        self._fields = fields
        self.save_label = save_label
        self.cancel_label = cancel_label
        self.edit_label = edit_label
        self.shortcuts_hint = shortcuts_hint

        async def handle_submit(value: T) -> FragmentResponse:
            key = self._request_key()
            saved = await self._save(key, value)
            return FragmentResponse(node=self._render_display(key, saved, oob=True))

        self.form = HeadlessForm[T](
            routes=routes,
            name=f"inline-edit-{self.name}",
            type=type,
            render=self._render_form,
            handle_submit=handle_submit,
        )

        async def edit(key: str) -> y.Node:
            return await self.form.render(await self._load(key))

        self.edit_fragment = routes.fragment.add(
            f"/_components/inline-edit/{self.name}/edit", "GET", edit
        )

    async def render(self, key: str, value: T | None = None) -> y.Node:
        """The value of the record ``key`` in display mode.

        Without ``value`` it is loaded with ``load(key)``.
        """
        if value is None:
            value = await self._load(key)
        return self._render_display(key, value)

    def item_id(self, key: str) -> str:
        """Element id of the item for the record ``key``."""
        return f"hx-inline-edit--{self.name}--{_id_part(key)}"

    @staticmethod
    def _request_key() -> str:
        key = RequestContext.get_request().query_params.get("key")
        if key is None:
            raise HTTPException(status_code=400, detail="Missing query parameter key")
        return key

    def _render_display(self, key: str, value: T, *, oob: bool = False) -> y.Node:
        item_id = self.item_id(key)
        hint = self._hint(key, value) if self._hint else None
        source = self._source(key, value) if self._source else None
        return y.div(
            class_="hx-inline-edit",
            id=item_id,
            hx_swap_oob="outerHTML" if oob else None,
        )[
            y.span(class_="hx-inline-edit__heading")[
                y.span(class_="hx-inline-edit__label", id=f"{item_id}__label")[
                    self.label
                ],
                y.span(class_="hx-inline-edit__hint")[hint]
                if hint is not None
                else None,
            ],
            y.span(class_="hx-inline-edit__value")[self._display_value(value)],
            y.span(class_="hx-inline-edit__source")[source]
            if source is not None
            else None,
            button(
                icon="pencil",
                variant="ghost",
                size="sm",
                type="button",
                class_="hx-inline-edit__edit",
                aria_label=str(self.edit_label)
                if self.edit_label is not None
                # Translators: accessible name of the edit button; {label} is
                # the label of the value, e.g. "Start of incapacity".
                else _("Edit {label}", label=str(self.label)),
                **htmx(
                    hx_get=self.edit_fragment.url(query={"key": key}),
                    hx_target=f"#{item_id}",
                    hx_swap="beforeend",
                ),
            ),
        ]

    def _display_value(self, value: T) -> y.Node:
        if self._display is not None:
            return self._display(value)
        values = [getattr(value, f, None) for f in self.type.model_fields]
        text = ", ".join(str(v) for v in values if v not in (None, ""))
        return text or "–"

    async def _render_form(self, ctx: FormRenderContext[T]) -> y.Node:
        key = self._request_key()
        item_id = self.item_id(key)
        attrs = ctx.form.form_attrs(oob=ctx.oob)
        attrs["hx_post"] = ctx.form.submit_form_fragment.url(query={"key": key})
        # The form posts only its own fields; HeadlessForm's include of
        # page-wide fields (drawer pickers) has nothing to find here.
        attrs.pop("hx_include", None)
        return y.form(
            class_="hx-inline-edit__form",
            id=f"{item_id}__form",
            aria_labelledby=f"{item_id}__label",
            **attrs,
        )[
            y.div(class_="hx-inline-edit__fields")[
                self._fields(ctx) if self._fields else self._default_fields(ctx)
            ],
            y.div(class_="hx-inline-edit__actions")[
                button(self.save_label, appearance="primary", type="submit"),
                button(
                    self.cancel_label,
                    variant="link",
                    type="button",
                    data_hx_inline_edit_cancel=True,
                ),
                y.small(class_="hx-inline-edit__shortcuts")[self.shortcuts_hint]
                if self.shortcuts_hint
                else None,
            ],
        ]

    def _default_fields(self, ctx: FormRenderContext[T]) -> y.Node:
        model_fields = self.type.model_fields
        single = len(model_fields) == 1
        item_id = self.item_id(self._request_key())
        nodes = []
        for name, info in model_fields.items():
            # A single control is labelled by the item's visible label; with
            # several, each gets its own label from the field's title.
            label = "" if single else (info.title or to_title_case(name))
            nodes.append(
                form_field(
                    name,
                    label,
                    y.input,
                    type=_input_type(info.annotation),
                    step="any" if _input_type(info.annotation) == "number" else None,
                    value=_input_value(getattr(ctx.value, name, None)),
                    error_text=ctx.visible_errors.get(name),
                    disabled=ctx.disabled,
                    aria_labelledby=f"{item_id}__label" if single else None,
                )
            )
        return nodes
