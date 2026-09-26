"""Headless form controller — validation/touched/htmx wiring without layout.

:class:`DataForm` couples two concerns: the *controller* (parse the posted
form, run ``model_validate``, reduce errors to ``{field: message}``, track
which fields the user has *touched*, register the ``/validate`` + ``/submit``
HTMX fragments, and gate the submit button on validity) and the *layout* (the
generic annotation-driven ``_render_field`` family).

:class:`HeadlessForm` is the controller half on its own. It owns everything
*except* the layout, which it delegates to a caller-supplied ``render``
callback. Callers that want a bespoke layout — a multi-column grid, custom
controls, an in-table edit row — build their own markup and reach for the
:class:`FormRenderContext` helpers (``form_attrs`` / ``validate_attrs`` /
``touched_inputs``) to wire the HTMX behaviour without copying string
constants.

The controller is intentionally annotation-agnostic: it derives list-vs-scalar
parsing from the Pydantic field types, so a plain ``BaseModel`` works without
the ``@form`` / ``FormField`` annotation system that :class:`DataForm` relies
on.
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import get_origin

import htpy as y
from commons.string_operators import to_kebabcase
from fastapi import Request
from pydantic import BaseModel, ValidationError

from pyhx.core.fragment import FragmentResult
from pyhx.core.primitives import htmx
from pyhx.core.webapp_routes import WebAppRoutes

LOG = logging.getLogger("pyhx")


@dataclass
class FormRenderContext[T: BaseModel]:
    """Everything a :class:`HeadlessForm` layout callback needs to render.

    ``errors`` is the *full* error set — gate the submit button on
    ``bool(errors)`` so an invalid model keeps it disabled even before the
    user has touched anything. ``visible_errors`` is the touched-filtered
    subset — feed those to ``form_field(error_text=…)`` so untouched fields
    stay quiet. ``form`` exposes the HTMX wiring helpers.
    """

    value: T
    errors: dict[str, str]
    visible_errors: dict[str, str]
    touched: set[str]
    disabled: bool
    form: "HeadlessForm[T]"
    oob: bool = False


class HeadlessForm[T: BaseModel]:
    """Form controller bound to a Pydantic model, layout supplied by caller.

    Generic over the model type ``T``. Registers ``/validate`` and ``/submit``
    HTMX fragments and dispatches rendering to the ``render`` callback passed
    at construction. The callback receives a :class:`FormRenderContext` and
    returns the full form node (typically a ``<form>`` carrying
    :meth:`form_attrs` with an inner container carrying :meth:`validate_attrs`).
    """

    def __init__(
        self,
        *,
        routes: WebAppRoutes,
        name: str,
        type: type[T],
        render: Callable[[FormRenderContext[T]], Awaitable[y.Node]],
        handle_submit: Callable[[T], Awaitable[FragmentResult]],
        list_fields: set[str] | None = None,
    ) -> None:
        """``list_fields`` overrides which fields are parsed via ``getlist``.

        When ``None`` (the default), list fields are derived from the model:
        any field annotated as ``list[...]`` collects repeated keys. Pass an
        explicit set when the model's annotation can't be introspected that
        way (e.g. an aliased / computed shape).
        """
        self.name = to_kebabcase(name)
        self.type = type
        self._render_body = render
        self.wrapper_div_id = f"hx-headless-form__{self.name}"
        self._list_fields = (
            list_fields if list_fields is not None else self._derive_list_fields(type)
        )

        async def submit_form(request: Request) -> FragmentResult:
            raw = await self._parse_form(request)
            try:
                value = self.type.model_validate(raw)
                return await handle_submit(value)
            except ValidationError as exc:
                # Defensive — the submit button is gated on the full ``errors``
                # dict so it should already be disabled while validation fails.
                # Getting here means the click slipped past JS (race / bot /
                # button re-enabled by hand), so re-render with every field
                # marked touched so all the errors light up at once.
                errors = self._validation_errors_to_dict(exc)
                value = self.type.model_construct(**raw)
                return await self.render(
                    value,
                    errors=errors,
                    touched=set(self.type.model_fields),
                    oob=True,
                )

        async def validate_form(request: Request) -> y.Node:
            raw = await self._parse_form(request)

            form = await request.form()
            touched = await self._parse_touched(request)
            # ``hx-vals="js:{_trigger: event.target.name}"`` on the trigger
            # container pulls the bubbled field name into a synthetic
            # ``_trigger`` form field. Anything not in ``model_fields`` is
            # rejected — defensive against cross-form posts and stray ancestor
            # focusout.
            trigger = form.get("_trigger")
            if isinstance(trigger, str) and trigger in self.type.model_fields:
                touched.add(trigger)
            errors: dict[str, str] = {}
            try:
                value = self.type.model_validate(raw)
            except ValidationError as exc:
                errors = self._validation_errors_to_dict(exc)
                # ``model_construct`` bypasses validation so we can keep what
                # the user just typed even when it doesn't satisfy the schema
                # yet — the layout's per-field guards tolerate loose values.
                value = self.type.model_construct(**raw)
                LOG.warning(f"Validation error detected: {errors}.")

            # OOB re-render: the validate response *is* this form, morphing the
            # existing one in place (it already lives in the DOM).
            return await self.render(value, errors=errors, touched=touched, oob=True)

        self.submit_form_fragment = routes.fragment.add(
            f"/_components/headless-form/{self.name}/submit",
            "POST",
            submit_form,
        )
        self.validate_form_fragment = routes.fragment.add(
            f"/_components/headless-form/{self.name}/validate",
            "POST",
            validate_form,
        )

    async def render(
        self,
        value: T | None = None,
        errors: dict[str, str] | None = None,
        touched: set[str] | None = None,
        disabled: bool = False,
        oob: bool = False,
    ) -> y.Node:
        """Render the form for ``value`` via the caller's layout callback.

        ``value`` is optional — when omitted an empty instance is built via
        ``model_construct`` (bypasses validation, so even models with required
        fields render an empty form).

        ``errors`` is a ``{field: message}`` dict. When ``None`` (the typical
        initial-render path) the model is re-validated so the submit-button
        state reflects reality from the first paint. The ``/validate`` fragment
        passes an explicit dict (possibly empty), short-circuiting this.

        ``touched`` gates which errors are *visible*: only touched fields end
        up in ``visible_errors``. The full ``errors`` set still drives submit
        gating.

        ``oob`` controls whether the rendered form carries ``hx-swap-oob``.
        Leave it ``False`` (the default) for the *initial* render when the form
        is delivered as part of another HTMX swap (e.g. an edit-in-place row) —
        otherwise htmx would extract the self-OOB form from that response and
        discard it, leaving an empty slot. The ``/validate`` and ``/submit``
        re-renders pass ``True`` so the already-mounted form morphs in place.
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

        return await self._render_body(
            FormRenderContext(
                value=value,
                errors=errors,
                visible_errors=visible_errors,
                touched=touched,
                disabled=disabled,
                form=self,
                oob=oob,
            )
        )

    def form_attrs(self, *, oob: bool = False, transition: bool = False) -> dict:
        """HTMX attributes for the outer ``<form>`` element.

        Posts to the submit fragment with ``hx-swap="none"`` — the submit
        response is delivered out-of-band by its handler. Pair with
        ``id=self.wrapper_div_id`` on the same element.

        ``oob`` adds ``hx-swap-oob="morph"`` so a re-rendered form morphs the
        existing one in place. Pass ``ctx.oob`` — it is ``False`` for the
        initial render (so the form survives being delivered inside another
        swap) and ``True`` for validate/submit re-renders.

        ``transition`` adds the ``transition:true`` swap modifier. The submit's
        own swap is ``none``, but the modifier wraps the whole swap — including
        any out-of-band elements the submit handler delivers — in a View
        Transition, so an OOB refresh animates like a direct ``transition:true``
        swap would.
        """
        return htmx(
            hx_post=self.submit_form_fragment.url(),
            hx_swap="none transition:true" if transition else "none",
            hx_ext="morph",
            hx_swap_oob="morph" if oob else None,
            hx_include="[data-hx-include='always']",
            as_dict=True,
        )

    def validate_attrs(self, *, oob: bool = False) -> dict:
        """HTMX attributes for the container wrapping the validated fields.

        Triggers ``/validate`` on input (debounced) / change / focusout. Put
        this on a container that wraps the fields whose edits should trigger
        live validation. ``oob`` mirrors :meth:`form_attrs` — pass ``ctx.oob``.
        """
        return htmx(
            hx_post=self.validate_form_fragment.url(),
            hx_trigger=(
                "input[!!event.target.name] delay:1000ms, "
                "change[!!event.target.name], "
                "focusout[!!event.target.name]"
            ),
            hx_vals="js:{_trigger: event && event.target ? event.target.name : ''}",
            hx_swap="none",
            hx_ext="morph",
            hx_swap_oob="morph" if oob else None,
            as_dict=True,
        )

    def touched_inputs(self, touched: set[str]) -> list[y.Node]:
        """Hidden ``<input name="_touched">`` elements preserving the set.

        Render these inside the validated-fields container so the next
        ``/validate`` round-trip can reconstruct which fields are touched.
        """
        return [
            y.input(type="hidden", name="_touched", value=name)
            for name in sorted(touched)
        ]

    @staticmethod
    def _derive_list_fields(type: type[BaseModel]) -> set[str]:
        """Field names annotated as ``list[...]`` — parsed via ``getlist``."""
        return {
            name
            for name, info in type.model_fields.items()
            if get_origin(info.annotation) is list
        }

    async def _parse_form(self, request: Request) -> dict:
        """Convert the posted form into a dict shaped for ``model_validate``.

        - List fields collect repeated keys via ``getlist``.
        - ``bool`` fields use key-presence (unchecked checkboxes don't submit).
        - Other fields normalise ``""`` to ``None`` so ``Optional[…]`` fields
          don't see empty strings when the user clears them.
        """
        form = await request.form()
        out: dict = {}
        for name, info in self.type.model_fields.items():
            if name in self._list_fields:
                out[name] = form.getlist(name)
            elif info.annotation is bool:
                out[name] = name in form
            else:
                v = form.get(name)
                out[name] = None if v in ("", None) else v
        return out

    async def _parse_touched(self, request: Request) -> set[str]:
        """Read the touched-field set from the posted ``_touched`` keys.

        Drops anything not in ``model_fields`` so stray values from a
        different form (or a hand-crafted request) can't poison the set.
        """
        form = await request.form()
        return {
            str(name)
            for name in form.getlist("_touched")
            if name in self.type.model_fields
        }

    def _validation_errors_to_dict(self, exc: ValidationError) -> dict[str, str]:
        """Reduce a :class:`ValidationError` to one message per top-level field.

        Keeps the first error per location — the form UI shows a single
        message per control. Model-level errors (empty ``loc``) are skipped.
        """
        out: dict[str, str] = {}
        for err in exc.errors():
            loc = err.get("loc") or ()
            if loc and isinstance(loc[0], str) and loc[0] not in out:
                out[loc[0]] = err["msg"]
        return out
