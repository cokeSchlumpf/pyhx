"""``@form`` class decorator — attaches a :class:`FormConfig` to a Pydantic model.

The decorated class gets a ``__form__`` class attribute carrying the layout
config the data-form builder consumes. Models that aren't decorated render
with ``FormConfig()`` defaults — the decorator is for *overriding* those.

Example
-------
>>> from pydantic import BaseModel
>>> from typing import Annotated
>>> from pyhx.components.annotations import form, TextField
>>>
>>> @form(columns=2, submit_label="Create issue")
... class IssueForm(BaseModel):
...     title: Annotated[str, TextField(help_text="Be specific")]
...     description: str
"""

from collections.abc import Callable
from dataclasses import dataclass

SubmitLabel = str | Callable[[], str]
"""Either a literal label or a zero-argument callable returning one.

A callable is evaluated lazily at render time — useful for i18n (the
locale active at *render* time wins) or for labels that depend on
runtime state (``lambda: "Update" if is_editing() else "Create"``).
"""


@dataclass(frozen=True, kw_only=True)
class FormConfig:
    """Layout + behaviour metadata attached to a form-driving Pydantic model.

    Attached at class-decoration time via :func:`form` and read back by the
    data-form builder via ``getattr(model, "__form__", FormConfig())``.

    ``submit_label`` is *always* a callable internally — the :func:`form`
    decorator wraps plain strings in a lambda before constructing the
    config. Consumers can therefore call it unconditionally
    (``cfg.submit_label()``) without checking for the string case.

    Attributes
    ----------
    columns : int, default 2
        Number of columns in the rendered ``hx-grid`` form. Each form-field
        and fieldset occupies one cell; pick ``1`` for a strictly stacked
        layout or ``3+`` for denser layouts. Ignored when ``template_areas``
        is set (the template defines the column count).
    template_areas : list[str] | None, default None
        Explicit CSS-Grid placement, addressed **by field name**. Each list
        item is one grid row of space-separated field keys (use ``"."`` for an
        empty cell), exactly like CSS ``grid-template-areas`` rows. A key
        repeated across cells spans those columns/rows::

            template_areas=[
                "title    title",
                "summary  author",
                "summary  tags",
            ]

        When set, every field is placed by its key and the per-field
        ``columns`` / ``rows`` spans are ignored. Names must be valid CSS
        idents — model field names (snake_case) qualify.
    template_columns : list[str] | None, default None
        Explicit column **widths**, one CSS track size per column
        (``"2fr"``, ``"1fr"``, ``"minmax(0, 20rem)"``, ``"auto"``, …) →
        ``grid-template-columns``. When omitted, columns are equal
        (``repeat(N, 1fr)``). Works with or without ``template_areas``; its
        length should match the grid's column count.
    template_rows : list[str] | None, default None
        Explicit row **heights**, one CSS track size per row →
        ``grid-template-rows``. Optional; rows are ``auto`` by default.
    submit_label : Callable[[], str], default lambda returning "Save"
        Zero-argument callable returning the submit button's label. Lazy
        evaluation makes it natural for i18n (the locale active at *render*
        time wins) or for state-dependent labels like
        ``lambda: "Update" if is_editing() else "Create"``.
    field_order : list[str] | None, default None
        Authoritative whitelist and order, keyed by field name. When set,
        any field whose name is absent is dropped from the rendered form
        and ignored on submit/validate. An explicit ``field_order`` passed
        to :class:`DataForm` overrides this value; if neither is set,
        fields render in model field order.
        Hidden fields (``HiddenField``) are auto-included even when absent from
        this list, so their values still submit; use ``IgnoreField`` on a field to
        exclude it from the form entirely.
    """

    columns: int = 2
    template_areas: list[str] | None = None
    template_columns: list[str] | None = None
    template_rows: list[str] | None = None
    submit_label: Callable[[], str] = lambda: "Save"
    field_order: list[str] | None = None


def form[T](
    *,
    columns: int = 2,
    template_areas: list[str] | None = None,
    template_columns: list[str] | None = None,
    template_rows: list[str] | None = None,
    submit_label: SubmitLabel = "Save",
    field_order: list[str] | None = None,
) -> Callable[[T], T]:
    """Class decorator that attaches a :class:`FormConfig` to ``cls.__form__``.

    The decoration is a runtime side-effect — static type checkers don't see
    the new attribute. The :class:`DataForm` builder reads it back via
    ``getattr(model, "__form__", FormConfig())``, so un-decorated models
    render with defaults rather than raising.

    Generic over the decorated class so the type checker keeps the original
    identity (``LoginForm`` stays ``type[LoginForm]``, not bare ``type``) —
    that's what lets :class:`DataForm` infer its model parameter at call
    sites like ``DataForm(name="x", routes=webapp, type=LoginForm,
    handle_submit=submit)``.

    Parameters
    ----------
    columns : int, default 2
        Number of columns in the rendered grid. Ignored when
        ``template_areas`` is set.
    template_areas : list[str] | None, default None
        Explicit CSS-Grid placement addressed by field name — one
        space-separated row of field keys per list item (``"."`` = empty
        cell). See :class:`FormConfig` for details and an example.
    template_columns : list[str] | None, default None
        Explicit column widths (CSS track sizes) → ``grid-template-columns``.
        Defaults to equal columns.
    template_rows : list[str] | None, default None
        Explicit row heights (CSS track sizes) → ``grid-template-rows``.
    submit_label : SubmitLabel, default "Save"
        Submit button label. Either a literal ``str`` or a
        ``Callable[[], str]`` evaluated at render time.
    field_order : list[str] | None, default None
        Authoritative whitelist and order, keyed by field name. When set,
        any field whose name is absent is dropped from the rendered form.
        Overridden by an explicit ``field_order`` on :class:`DataForm`.
        Hidden fields (``HiddenField``) are auto-included even when absent from
        this list, so their values still submit; use ``IgnoreField`` on a field to
        exclude it from the form entirely.

    Returns
    -------
    Callable[[T], T]
        A decorator that sets ``cls.__form__`` and returns the class
        unchanged with its original type preserved.

    Example
    -------
    >>> @form(columns=2, submit_label="Create issue")
    ... class IssueForm(BaseModel):
    ...     title: Annotated[str, TextField()]
    """
    submit_label_fn: Callable[[], str] = (
        submit_label if callable(submit_label) else (lambda: submit_label)
    )
    cfg = FormConfig(
        columns=columns,
        template_areas=template_areas,
        template_columns=template_columns,
        template_rows=template_rows,
        submit_label=submit_label_fn,
        field_order=field_order,
    )

    def decorator(cls: T) -> T:
        cls.__form__ = cfg  # type: ignore[attr-defined]
        return cls

    return decorator
