import logging
from collections.abc import Awaitable, Callable, Iterable, Sequence
from datetime import datetime
from functools import partial

import htpy as y
from commons.string_operators import to_kebabcase, to_title_case
from fastapi import Request
from pydantic import BaseModel, ValidationError

from pyhx.core.fragment import FragmentResult
from pyhx.core.primitives import htmx
from pyhx.core.webapp_routes import WebAppRoutes

from ..primitives import (
    button,
    checkbox_fieldset,
    drawer_radio,
    drawer_select,
    dropdown_checkbox,
    dropdown_radio,
    form_field,
    radio_fieldset,
    segment_control,
    taglist,
    wysiwyg_editor,
)
from ..view_model import Option, resolve_options
from .annotations.form import FormConfig
from .annotations.form_field import (
    BooleanCheckboxFieldsetControl,
    BooleanField,
    BooleanRadioFieldsetControl,
    BooleanSegmentControl,
    CheckboxFieldsetControl,
    DateField,
    DrawerRadioControl,
    DrawerSelectControl,
    DropdownControl,
    FormField,
    HiddenField,
    InputControl,
    MultiselectChoiceField,
    NumericField,
    RadioFieldsetControl,
    SegmentControl,
    TaglistControl,
    TextareaControl,
    TextChoiceField,
    TextField,
    TextListField,
    WYSIWYGControl,
)
from .annotations.reader import read_form_field_annotations

LOG = logging.getLogger("pyhx")


def _span_class(annotation: FormField) -> str:
    """Grid-span classes for ``annotation.columns`` / ``annotation.rows``, or ``""``.

    Emits ``hx-grid-span-{n}`` for a column span and ``hx-grid-row-span-{n}``
    for a row span — either, both, or neither — space-joined. Returned as
    ``""`` (not ``None``) so call sites can pass it through ``class_=``
    unconditionally without triggering the ``"None"`` string edge case in
    :func:`classnames`.

    Note: a ``template_areas`` layout (see :class:`FormConfig`) places fields
    explicitly and ignores these spans.
    """
    columns = getattr(annotation, "columns", None)
    rows = getattr(annotation, "rows", None)
    classes = []
    if columns:
        classes.append(f"hx-grid-span-{columns}")
    if rows:
        classes.append(f"hx-grid-row-span-{rows}")
    return " ".join(classes)


class DataForm[T: BaseModel]:
    """Renderable form bound to a Pydantic model.

    Generic over the model type ``T``. Layout and submit-button label are
    pulled from the model's ``__form__`` attribute (set via
    :func:`form` decorator); un-decorated models fall back to a default
    :class:`FormConfig`.
    """

    def __init__(
        self,
        *,
        routes: WebAppRoutes,
        name: str,
        type: type[T],
        handle_submit: Callable[[T], Awaitable[FragmentResult]],
        submit_label: str | None = None,
        field_order: list[str] | None = None,
    ) -> None:
        """``field_order`` is the authoritative whitelist and order when set:
        any field whose name is absent is dropped from the rendered form
        and ignored on submit/validate. Hidden fields (``HiddenField``) are
        the exception — they are auto-included even when absent from the list
        (appended in model order) so their values still submit; use
        ``IgnoreField`` on a field to exclude it from the form entirely. When
        ``None``, the value falls back to :attr:`FormConfig.field_order` from
        the model's ``@form`` decoration; if that is also ``None``, fields
        render in model field order.
        """
        self.name = to_kebabcase(name)
        self.type = type
        self.form_config: FormConfig = getattr(type, "__form__", FormConfig())
        form_fields = read_form_field_annotations(type)
        effective_order = (
            field_order if field_order is not None else self.form_config.field_order
        )
        if effective_order is not None:
            ordered = {k: form_fields[k] for k in effective_order if k in form_fields}
            # Hidden fields carry values that must still submit, so they are
            # auto-included even when absent from the order whitelist —
            # appended (in model field order) after the named fields. Use
            # IgnoreField to drop one entirely.
            hidden_extras = {
                k: f
                for k, f in form_fields.items()
                if k not in ordered and isinstance(f, HiddenField)
            }
            form_fields = {**ordered, **hidden_extras}
        self.form_fields: dict[str, FormField] = form_fields
        self.submit_label = submit_label

        self.wrapper_div_id = f"hx-data-form__{self.name}"

        async def submit_form(request: Request) -> FragmentResult:
            raw = await self._parse_form(request)
            try:
                value = self.type.model_validate(raw)
                return await handle_submit(value)
            except ValidationError as exc:
                # Defensive — the submit button is gated on the full ``errors``
                # dict so it should already be disabled while validation fails.
                # Getting here means the click slipped past JS (race / bot /
                # button re-enabled by hand), so re-render the form with every
                # field marked touched so all the errors light up at once.
                errors = self._validation_errors_to_dict(exc)
                value = self.type.model_construct(**raw)
                return await self.render(
                    value,
                    errors=errors,
                    touched=set(self.form_fields.keys()),
                )

        async def validate_form(request: Request) -> y.Node:
            raw = await self._parse_form(request)

            form = await request.form()
            touched = await self._parse_touched(request)
            # htmx's built-in ``HX-Trigger-Name`` header reflects the *element
            # carrying the hx-* attributes*, which here is the inner ``<div>``
            # and has no ``name``. We work around it with ``hx-vals="js:..."``
            # on that same div, which evaluates at request-build time and pulls
            # the bubbled ``event.target.name`` into a synthetic ``_trigger``
            # form field. Anything not in :attr:`form_fields` is rejected —
            # defensive against cross-form posts and stray ancestor focusout.
            trigger = form.get("_trigger")
            if isinstance(trigger, str) and trigger in self.form_fields:
                touched.add(trigger)
            errors: dict[str, str] = {}
            try:
                value = self.type.model_validate(raw)
            except ValidationError as exc:
                errors = self._validation_errors_to_dict(exc)
                # ``model_construct`` bypasses validation so we can keep what
                # the user just typed in the form even when it doesn't satisfy
                # the schema yet. The renderer's per-type guards tolerate the
                # loose values (strings where ints were expected, etc.).
                value = self.type.model_construct(**raw)

                LOG.warning(f"Validation error detected: {errors}.")

            return await self.render(value, errors=errors, touched=touched)

        self.submit_form_fragment = routes.fragment.add(
            f"/_components/data-form/{self.name}/submit",
            "POST",
            submit_form,
        )

        self.validate_form_fragment = routes.fragment.add(
            f"/_components/data-form/{self.name}/validate",
            "POST",
            validate_form,
        )

    async def render(
        self,
        value: T | None = None,
        errors: dict[str, str] | None = None,
        touched: set[str] | None = None,
        disabled: bool = False,
        disable_actions: bool = False,
        actions: y.Node | None = None,
    ) -> y.Node:
        """Render the form for ``value``.

        Iterates ``self.type.model_fields`` and dispatches each one through
        :meth:`_render_field`, which picks the right primitive based on
        the field's :data:`FormField` annotation (explicit or derived).
        Fields with no annotation are silently skipped.

        ``value`` is optional — when omitted, an empty instance is built via
        :meth:`BaseModel.model_construct`, which bypasses validation so even
        models with required fields can render an empty new-record form. The
        per-type ``isinstance`` guards in :meth:`_render_field` tolerate the
        missing / loose attributes that result.

        ``errors`` is a ``{field_name: message}`` dict produced by
        :meth:`_validation_errors_to_dict`. When ``errors`` is ``None`` (the
        typical caller path — initial render without a prior validate
        round-trip), the renderer re-validates ``value`` against the model so
        the submit-button enabled state reflects reality from the very first
        paint. The ``/validate`` fragment passes an explicit dict (possibly
        empty), which short-circuits this re-validation.

        ``touched`` gates *which* errors are visible to the user. Only fields
        the user has interacted with (via ``change`` or ``focusout``) end up
        in the set, and only their errors render as ``form_field(error_text=
        ...)`` — untouched fields stay quiet even when invalid. The set is
        serialised into hidden ``<input name="_touched">`` elements so the
        next ``/validate`` round-trip can reconstruct it. The submit button,
        however, is gated on the **full** ``errors`` dict so an invalid model
        keeps it disabled even before the user has touched anything.

        ``disabled`` is a render-time switch. When True, every primitive the
        form dispatches to (``form_field``, ``radio_fieldset``,
        ``checkbox_fieldset``) receives ``disabled=True`` — disabled cascades
        all the way down to the underlying ``<input>`` / ``<details>`` /
        ``<fieldset>``. The submit button is also disabled. Hidden fields
        stay live (their values still submit). The flag is not persisted
        across validate/submit round-trips by design — disabled forms can't
        emit those events anyway.

        ``disable_actions`` skips both the ``<hr>`` divider and the entire
        ``<div class="hx-data-form__actions">`` wrapper — including the
        submit button. Use it for read-only embeds where neither the
        divider nor any control below the fields makes sense.

        ``actions`` is a slot for secondary controls (Cancel, Reset,
        "Save as draft", …). Accepts a single ``y.Node`` or a
        ``y.fragment[…]`` for multiple. On a normal page they render
        left of the submit button. Inside a drawer they stack
        vertically below the submit in reverse insertion order, so the
        action closest to submit on the page sits closest to it in the
        drawer. ``disable_actions=True`` overrides this slot.
        """
        if value is None:
            value = self.type.model_construct()
        if errors is None:
            try:
                self.type.model_validate(value.__dict__)
                errors = {}
            except ValidationError as exc:
                errors = self._validation_errors_to_dict(exc)
        touched = touched if touched is not None else set()
        visible_errors = {f: msg for f, msg in errors.items() if f in touched}

        return y.form(
            id=self.wrapper_div_id,
            **htmx(
                hx_post=self.submit_form_fragment.url(),
                hx_swap="none",
                hx_ext="morph",
                hx_swap_oob="morph",
                hx_include="[data-hx-include='always']",
                as_dict=True,
            ),
        )[
            y.div(
                class_="hx-grid hx-data-form",
                style=self._grid_style(),
                **htmx(
                    hx_post=self.validate_form_fragment.url(),
                    hx_trigger=(
                        "input[!!event.target.name] delay:1000ms, "
                        "change[!!event.target.name], "
                        "focusout[!!event.target.name]"
                    ),
                    hx_vals="js:{_trigger: event && event.target ? event.target.name : ''}",
                    hx_swap="none",
                    hx_ext="morph",
                    hx_swap_oob="morph",
                    as_dict=True,
                ),
            )[
                *[
                    self._place_field(
                        field,
                        await self._render_field(
                            field,
                            value,
                            visible_errors.get(field),
                            disabled=disabled,
                        ),
                    )
                    for field in self.form_fields
                ],
                *[
                    y.input(type="hidden", name="_touched", value=name)
                    for name in sorted(touched)
                ],
            ],
            *(
                []
                if disable_actions
                else [
                    y.hr,
                    y.div(class_="hx-data-form__actions")[
                        y.div[
                            actions,
                            button(
                                self.submit_label or self.form_config.submit_label(),
                                appearance="primary",
                                type="submit",
                                disabled=disabled or bool(errors),
                            ),
                        ]
                    ],
                ]
            ),
        ]

    def _grid_style(self) -> str:
        """Inline ``style`` for the ``hx-grid`` container, from the form config.

        With no template config this is just ``--hx-grid-columns: {columns}``
        (feeding the stylesheet's ``repeat(var(--hx-grid-columns), 1fr)``).
        Otherwise it composes the relevant CSS-Grid track / area declarations:

        - ``template_columns`` → inline ``grid-template-columns`` (overrides the
          stylesheet's equal-columns default); else the column count is derived
          from ``template_areas`` (widest row) or falls back to ``columns``.
        - ``template_rows`` → ``grid-template-rows``.
        - ``template_areas`` → ``grid-template-areas`` (rows quoted).
        """
        cfg = self.form_config
        parts: list[str] = []

        if cfg.template_columns:
            parts.append(f"grid-template-columns: {' '.join(cfg.template_columns)}")
        elif cfg.template_areas:
            n = max(len(row.split()) for row in cfg.template_areas)
            parts.append(f"--hx-grid-columns: {n}")
        else:
            parts.append(f"--hx-grid-columns: {cfg.columns}")

        if cfg.template_rows:
            parts.append(f"grid-template-rows: {' '.join(cfg.template_rows)}")

        if cfg.template_areas:
            # Single-quote each row: CSS accepts it, and single quotes need no
            # HTML escaping inside the double-quoted ``style="…"`` attribute.
            areas = " ".join(f"'{row}'" for row in cfg.template_areas)
            parts.append(f"grid-template-areas: {areas}")

        return "; ".join(parts)

    def _place_field(self, field: str, node: y.Node | None) -> y.Node | None:
        """Place a rendered field into its named grid area, in template mode.

        With a ``template_areas`` layout the form is a named CSS grid; each
        visible field's cell is positioned by its key via ``grid-area``. Without
        a template (or for hidden fields, which don't occupy a cell — assigning
        an area would create a stray implicit track) the node passes through
        unchanged.
        """
        if node is None or not self.form_config.template_areas:
            return node
        if isinstance(self.form_fields.get(field), HiddenField):
            return node
        return y.div(class_="hx-data-form__cell", style=f"grid-area: {field}")[node]

    async def _parse_form(self, request: Request) -> dict:
        """Convert the posted form into a dict shaped for ``model_validate``.

        - Multi-select fields collect repeated keys via ``getlist``.
        - Boolean fields use key-presence (unchecked checkboxes don't submit).
        - Other fields normalise ``""`` to ``None`` so ``Optional[…]`` fields
          don't see empty strings when the user clears them.
        """
        form = await request.form()
        out: dict = {}
        for name, ff in self.form_fields.items():
            if isinstance(ff, (MultiselectChoiceField, TextListField)):
                out[name] = form.getlist(name)
            elif isinstance(ff, BooleanField):
                out[name] = name in form
            else:
                v = form.get(name)
                out[name] = None if v in ("", None) else v
        return out

    async def _parse_touched(self, request: Request) -> set[str]:
        """Read the touched-field set from the posted ``_touched`` keys.

        Defensive — drops anything not in :attr:`form_fields` so stray values
        from a different form (or a hand-crafted request) can't poison the
        set. Returns a fresh set even when no ``_touched`` keys are present.
        """
        form = await request.form()
        return {
            str(name) for name in form.getlist("_touched") if name in self.form_fields
        }

    def _validation_errors_to_dict(self, exc: ValidationError) -> dict[str, str]:
        """Reduce a :class:`ValidationError` to one message per top-level field.

        The form-field UI shows a single ``<small>`` per control, so we keep
        the first error per location. Model-level errors (empty ``loc``) are
        skipped — surfacing those needs a separate UI slot.
        """
        out: dict[str, str] = {}
        for err in exc.errors():
            loc = err.get("loc") or ()
            if loc and isinstance(loc[0], str) and loc[0] not in out:
                out[loc[0]] = err["msg"]
        return out

    async def _render_field(
        self,
        field: str,
        value: T,
        error: str | None = None,
        *,
        disabled: bool = False,
    ) -> y.Node:
        """Dispatch one field through the right rendering primitive.

        Returns ``None`` (no DOM output) when the field has no resolved
        :data:`FormField` annotation — the reader skipped it (complex
        type) and the model author didn't pin it explicitly.

        ``disabled`` is the form-level flag from :meth:`render`. It's
        passed verbatim to whichever leaf primitive this field dispatches
        to; hidden fields stay live so their values still submit.

        When the field annotation sets ``columns=n`` / ``rows=n``, the
        rendered cell gets a ``hx-grid-span-{n}`` / ``hx-grid-row-span-{n}``
        class so it spans ``n`` columns / rows of the enclosing ``hx-grid``.
        Hidden fields skip this — they don't occupy a grid cell. A
        ``template_areas`` layout places fields explicitly (see
        :meth:`_place_field`) and supersedes these spans.
        """
        annotation = self.form_fields.get(field)
        if annotation is None:
            return None

        current_value = getattr(value, field, None)
        current_value_str = str(current_value) if current_value else ""

        if isinstance(annotation, HiddenField):
            return y.input(type="hidden", name=field, value=current_value_str)

        label = annotation.label or to_title_case(field)
        help_text = annotation.help_text
        required = self.type.model_fields[field].is_required()
        span_class = _span_class(annotation)

        if isinstance(annotation, TextField):
            return self._render_text(
                field,
                label,
                annotation.control,
                current_value_str,
                help_text,
                required,
                error,
                disabled=disabled,
                class_=span_class,
            )

        elif isinstance(annotation, NumericField):
            return form_field(
                field,
                label,
                y.input,
                type="number",
                value=current_value_str,
                help_text=help_text,
                required=required,
                error_text=error,
                disabled=disabled,
                class_=span_class,
            )

        elif isinstance(annotation, DateField) and isinstance(current_value, datetime):
            return form_field(
                field,
                label,
                y.input,
                type="date",
                value=current_value.isoformat(),
                help_text=help_text,
                required=required,
                error_text=error,
                disabled=disabled,
                class_=span_class,
            )

        elif isinstance(annotation, BooleanField) and isinstance(current_value, bool):
            return self._render_boolean(
                field,
                label,
                annotation.control,
                current_value,
                help_text,
                required,
                error,
                disabled=disabled,
                class_=span_class,
            )

        elif isinstance(annotation, TextChoiceField):
            options = await resolve_options(annotation.control.options)
            return self._render_text_choice(
                field,
                label,
                annotation.control,
                options,
                ""
                if current_value is None
                else annotation.to_choice_value(current_value),
                help_text,
                required,
                error,
                disabled=disabled,
                class_=span_class,
            )

        elif (
            isinstance(annotation, MultiselectChoiceField)
            and isinstance(current_value, Iterable)
            and not isinstance(current_value, (str, bytes))
        ):
            options = await resolve_options(annotation.control.options)
            return self._render_multiselect_choice(
                field,
                label,
                annotation.control,
                options,
                [annotation.to_choice_value(s) for s in current_value],
                help_text,
                required,
                error,
                disabled=disabled,
                class_=span_class,
            )

        elif isinstance(annotation, TextListField) and isinstance(
            annotation.control, TaglistControl
        ):
            current_list = (
                [str(s) for s in current_value]
                if isinstance(current_value, Iterable)
                and not isinstance(current_value, (str, bytes))
                else []
            )
            known_values = await resolve_options(annotation.control.known_values)
            initial_tags = (
                await resolve_options(annotation.control.initial_tags)
                if annotation.control.initial_tags is not None
                else None
            )
            return self._render_taglist(
                field,
                label,
                annotation.control,
                known_values,
                initial_tags,
                current_list,
                help_text,
                required,
                error,
                disabled=disabled,
                class_=span_class,
            )

        return None

    def _render_text(
        self,
        field: str,
        label: str,
        control: InputControl | TextareaControl | WYSIWYGControl,
        current_value: str,
        help_text: str | None,
        required: bool,
        error: str | None = None,
        *,
        disabled: bool = False,
        class_: str = "",
    ) -> y.Node:
        if isinstance(control, InputControl):
            return form_field(
                field,
                label,
                y.input,
                value=current_value,
                help_text=help_text,
                required=required,
                error_text=error,
                disabled=disabled,
                class_=class_,
                **control.attributes,  # type: ignore
            )
        if isinstance(control, TextareaControl):
            attrs = control.attributes

            def textarea_factory(**kwargs) -> y.Node:
                return y.textarea(**{**attrs, **kwargs})[current_value]

            return form_field(
                field,
                label,
                textarea_factory,
                help_text=help_text,
                required=required,
                error_text=error,
                disabled=disabled,
                class_=class_,
            )

        if isinstance(control, WYSIWYGControl):

            def wysiwyg_factory(**kwargs) -> y.Node:
                name = str(kwargs.pop("name"))
                value = str(kwargs.pop("value", current_value))

                return wysiwyg_editor(
                    name=name,
                    value=value,
                    **kwargs,
                )

            return form_field(
                field,
                label,
                wysiwyg_factory,
                value=current_value,
                help_text=help_text,
                required=required,
                error_text=error,
            )

    def _render_boolean(
        self,
        field: str,
        label: str,
        control: BooleanSegmentControl
        | BooleanCheckboxFieldsetControl
        | BooleanRadioFieldsetControl,
        current_value: bool,
        help_text: str | None,
        required: bool,
        error: str | None = None,
        *,
        disabled: bool = False,
        class_: str = "",
    ) -> y.Node:
        if isinstance(control, BooleanSegmentControl):
            options = [
                Option(label=control.true_label, value="true"),
                Option(label=control.false_label, value="false"),
            ]

            return form_field(
                field,
                label,
                partial(segment_control, options=options),
                value="true" if current_value else "false",
                help_text=help_text,
                required=required,
                error_text=error,
                disabled=disabled,
                class_=class_,
            )

        if isinstance(control, BooleanCheckboxFieldsetControl):
            return checkbox_fieldset(
                label,
                field,
                (Option(label=control.label, value="true"),),
                value=("true",) if current_value else (),
                disabled=disabled,
                class_=class_,
            )

        if isinstance(control, BooleanRadioFieldsetControl):
            boolean_options = (
                Option(label=control.true_label, value="true"),
                Option(label=control.false_label, value="false"),
            )
            return radio_fieldset(
                label,
                field,
                boolean_options,
                value="true" if current_value else "false",
                orientation=control.orientation,
                disabled=disabled,
                class_=class_,
            )

        return None

    def _render_text_choice(
        self,
        field: str,
        label: str,
        control: (
            SegmentControl | RadioFieldsetControl | DropdownControl | DrawerRadioControl
        ),
        options: tuple[Option, ...],
        current_value: str,
        help_text: str | None,
        required: bool,
        error: str | None = None,
        *,
        disabled: bool = False,
        class_: str = "",
    ) -> y.Node:
        if isinstance(control, SegmentControl):
            return form_field(
                field,
                label,
                partial(segment_control, options=list(options)),
                value=current_value,
                help_text=help_text,
                required=required,
                error_text=error,
                disabled=disabled,
                class_=class_,
            )

        if isinstance(control, RadioFieldsetControl):
            return radio_fieldset(
                label,
                field,
                options,
                value=current_value,
                orientation=control.orientation,
                disabled=disabled,
                class_=class_,
            )

        if isinstance(control, DropdownControl):
            return form_field(
                field,
                label,
                partial(dropdown_radio, options=options),
                value=current_value,
                help_text=help_text,
                required=required,
                error_text=error,
                disabled=disabled,
                class_=class_,
            )

        if isinstance(control, DrawerRadioControl):
            # help / error text are intentionally omitted: drawer_radio is a
            # self-contained control (its own value display, clear, and trigger)
            # and ignores the aria-invalid wiring form_field would emit, so a
            # help / error <small> would dangle without affecting it.
            return form_field(
                field,
                label,
                partial(drawer_radio, options=options, labels=control.labels),
                value=current_value or None,
                required=required,
                disabled=disabled,
                class_=class_,
                wrapper="div",
            )

        return None

    def _render_multiselect_choice(
        self,
        field: str,
        label: str,
        control: CheckboxFieldsetControl | DropdownControl | DrawerSelectControl,
        options: tuple[Option, ...],
        current: Sequence[str],
        help_text: str | None,
        required: bool,
        error: str | None = None,
        *,
        disabled: bool = False,
        class_: str = "",
    ) -> y.Node:
        if isinstance(control, CheckboxFieldsetControl):
            return checkbox_fieldset(
                label,
                field,
                options,
                value=current,
                orientation=control.orientation,
                disabled=disabled,
                class_=class_,
            )

        if isinstance(control, DropdownControl):
            return form_field(
                field,
                label,
                partial(dropdown_checkbox, options=options),
                value=current,
                help_text=help_text,
                required=required,
                error_text=error,
                disabled=disabled,
                class_=class_,
            )

        if isinstance(control, DrawerSelectControl):
            # help / error text are intentionally omitted: drawer_select is a
            # self-contained control (its own column header, Select button, and
            # labels) and ignores the aria-invalid wiring form_field would emit,
            # so a help / error <small> would dangle without affecting it.
            return form_field(
                field,
                label,
                partial(drawer_select, options=options, labels=control.labels),
                value=list(current),
                required=required,
                disabled=disabled,
                class_=class_,
                wrapper="div",
            )

        return None

    def _render_taglist(
        self,
        field: str,
        label: str,
        control: TaglistControl,
        known_values: tuple[Option, ...],
        initial_tags: tuple[Option, ...] | None,
        current: Sequence[str],
        help_text: str | None,
        required: bool,
        error: str | None = None,
        *,
        disabled: bool = False,
        class_: str = "",
    ) -> y.Node:
        return form_field(
            field,
            label,
            partial(
                taglist,
                known_values=list(known_values),
                initial_tags=list(initial_tags) if initial_tags is not None else None,
                allow_new_tags=control.allow_new_tags,
                suggestions_label=control.suggestions_label,
            ),
            value=list(current),
            help_text=help_text,
            required=required,
            error_text=error,
            disabled=disabled,
            class_=class_,
        )
