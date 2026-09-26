"""Read form-field annotations off a Pydantic model — with sensible defaults
when none is set on the field."""

import types
from collections.abc import Callable
from datetime import UTC, date, datetime, time
from enum import Enum
from typing import Any, Literal, Union, get_args, get_origin
from zoneinfo import ZoneInfo

import htpy as y
import humanize
from babel.dates import (
    format_date as babel_format_date,
)
from babel.dates import (
    format_datetime as babel_format_datetime,
)
from babel.numbers import (
    format_compact_decimal as babel_format_compact_decimal,
)
from babel.numbers import (
    format_currency as babel_format_currency,
)
from babel.numbers import (
    format_decimal as babel_format_decimal,
)
from commons.string_operators import to_title_case
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from pyhx.core.primitives import negotiate_locale, negotiate_timezone

from ...primitives import pill
from ...view_model import Option
from ...view_model.columns import ColumnKind, Flex
from ..column import Column as RenderColumn
from ..sources.filter_type import (
    BooleanFilter as BooleanFilterType,
)
from ..sources.filter_type import (
    ChoiceFilter as ChoiceFilterType,
)
from ..sources.filter_type import (
    ChoiceFilterOption,
    FilterType,
)
from ..sources.filter_type import (
    DateFilter as DateFilterType,
)
from ..sources.filter_type import (
    ListChoiceFilter as ListChoiceFilterType,
)
from ..sources.filter_type import (
    NumericFilter as NumericFilterType,
)
from ..sources.filter_type import (
    TextFilter as TextFilterType,
)
from .column import (
    BooleanColumn,
    BooleanFilter,
    Column,
    CurrencyNumberFormat,
    DateColumn,
    DateFilter,
    DateFormat,
    DateTimeColumn,
    DateTimeFormat,
    HiddenColumn,
    IsoDateFormat,
    IsoNumberFormat,
    LocalizedDateFormat,
    LocalizedDateTimeFormat,
    LocalizedNumberFormat,
    MultipleChoiceFilter,
    NumberFormat,
    NumericColumn,
    NumericFilter,
    PatternDateFormat,
    PatternNumberFormat,
    RelativeDateFormat,
    TextChoiceFilter,
    TextColumn,
    TextFilter,
    TextListColumn,
    TextListFilter,
)
from .controls import DropdownControl, _default_to_choice_value
from .form_field import (
    BooleanField,
    DateField,
    FormField,
    HiddenField,
    IgnoreField,
    MultiselectChoiceField,
    NumericField,
    TextChoiceField,
    TextField,
    TextListField,
)


def read_form_field_annotations[T: BaseModel](model: type[T]) -> dict[str, FormField]:
    """Build a ``{field_name: FormField}`` map for every field of ``model``.

    Resolution order, per field:

    1. If the field's ``Annotated[...]`` metadata already contains a
       :data:`FormField` marker, use it verbatim.
    2. Otherwise derive one from the field's Python type:

       * ``str`` → :class:`TextField`
       * ``int`` / ``float`` → :class:`NumericField`
       * ``bool`` → :class:`BooleanField`
       * ``date`` → :class:`DateField`
       * ``Literal[…]`` or :class:`Enum` subclass → :class:`TextChoiceField`
         with options drawn from the type's members.
       * ``list``/``set``/``frozenset``/``tuple[X, ...]`` of ``Literal`` or
         ``Enum`` → :class:`MultiselectChoiceField` with the same options.

    3. **Label** for the derived field comes from a sibling :data:`Column`
       annotation's ``label`` if present; otherwise the title-cased field
       name.

    Fields whose type can't be defaulted (nested models, untyped
    containers, complex unions, …) are silently skipped — the caller
    renders them however it likes, or the model author can pin them
    explicitly with an ``Annotated[…, TextField(...)]``.

    Parameters
    ----------
    model : type[T]
        A Pydantic model class.

    Returns
    -------
    dict[str, FormField]
        One entry per field that has (or can be defaulted to) a form-field
        annotation.
    """
    result: dict[str, FormField] = {}
    for field_name, info in model.model_fields.items():
        existing = _find_form_field(info)
        if isinstance(existing, IgnoreField):
            continue
        if existing is not None:
            result[field_name] = existing
            continue

        derived = _derive_form_field(field_name, info)
        if derived is not None:
            result[field_name] = derived

    return result


def _find_form_field(info: FieldInfo) -> FormField | IgnoreField | None:
    """Return the first form-field or ``IgnoreField`` marker in the field's
    metadata, if any."""
    for m in info.metadata:
        if isinstance(
            m,
            (
                IgnoreField,
                HiddenField,
                TextField,
                NumericField,
                BooleanField,
                DateField,
                TextChoiceField,
                MultiselectChoiceField,
                TextListField,
            ),
        ):
            return m
    return None


def _find_column(info: FieldInfo) -> Column | None:
    """Return the first :data:`Column` marker in the field's metadata, if any."""
    for m in info.metadata:
        if isinstance(
            m,
            (
                TextColumn,
                NumericColumn,
                DateColumn,
                DateTimeColumn,
                BooleanColumn,
                TextListColumn,
                HiddenColumn,
            ),
        ):
            return m
    return None


def _derive_form_field(field_name: str, info: FieldInfo) -> FormField | None:
    """Pick a sensible :data:`FormField` for ``info`` based on its type.

    Returns ``None`` for types we don't have a primitive control for yet
    (nested models, untyped containers, complex unions, …).
    """
    label = _resolve_label(field_name, info)
    annotation = _peel_optional(info.annotation)

    # Primitives.
    if annotation is str:
        return TextField(label=label)
    if annotation is bool:
        return BooleanField(label=label)
    if annotation is int or annotation is float:
        return NumericField(label=label)
    if annotation is date:
        return DateField(label=label)

    # Single-select choices from Literal or Enum.
    options = _options_for_choice_type(annotation)
    if options is not None:
        return TextChoiceField(
            control=DropdownControl(options=options),
            label=label,
        )

    # Multi-select choices: list / set / frozenset / tuple[X, ...] of
    # Literal or Enum.
    inner = _peel_collection(annotation)
    if inner is not None:
        options = _options_for_choice_type(inner)
        if options is not None:
            return MultiselectChoiceField(
                control=DropdownControl(options=options),
                label=label,
            )
        # Free-form ``list[str]`` → taglist (open list, no constraint).
        if inner is str:
            return TextListField(label=label)

    return None


def _resolve_label(field_name: str, info: FieldInfo) -> str:
    """Use a sibling :data:`Column`'s label if present, else the title-cased name."""
    column = _find_column(info)
    if column is not None and column.label is not None:
        return column.label
    return to_title_case(field_name)


def _peel_optional(annotation):
    """If ``annotation`` is ``X | None`` (or ``Optional[X]``), return ``X``.

    Common enough to handle here — ``str | None`` should still resolve to
    a text field, not be skipped as "complex".
    """
    if get_origin(annotation) in (types.UnionType, Union):
        non_none = tuple(a for a in get_args(annotation) if a is not type(None))
        if len(non_none) == 1:
            return non_none[0]
    return annotation


def _peel_collection(annotation):
    """If ``annotation`` is a homogeneous collection, return its element type.

    Handles ``list[X]``, ``set[X]``, ``frozenset[X]``, and
    ``tuple[X, ...]``. Returns ``None`` for anything else.
    """
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in (list, set, frozenset) and len(args) == 1:
        return args[0]
    if origin is tuple and len(args) == 2 and args[1] is Ellipsis:
        return args[0]
    return None


def _options_for_choice_type(annotation) -> tuple[Option, ...] | None:
    """If ``annotation`` is ``Literal[…]`` or an :class:`Enum` subclass,
    return the corresponding :class:`Option` tuple. Otherwise ``None``.

    Uses :func:`_default_to_choice_value` so the reader-side option strings
    always match what the annotation's default ``to_choice_value`` will
    produce on the renderer side.
    """
    if get_origin(annotation) is Literal:
        return tuple(
            Option(
                label=_default_to_choice_value(v),
                value=_default_to_choice_value(v),
            )
            for v in get_args(annotation)
        )
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return tuple(
            Option(
                label=_default_to_choice_value(m),
                value=_default_to_choice_value(m),
            )
            for m in annotation
        )
    return None


#
# --- DataTable column derivation ---------------------------------------------
#


def read_column_annotations[T: BaseModel](model: type[T]) -> dict[str, RenderColumn[T]]:
    """Build a ``{field_name: Column[T]}`` map for every field of ``model``.

    Mirrors :func:`read_form_field_annotations` but produces renderable
    :class:`Column` instances instead of form fields. Resolution per field:

    1. If the field's ``Annotated[...]`` metadata carries a column marker
       (:class:`TextColumn`, :class:`NumericColumn`, :class:`DateColumn`,
       :class:`BooleanColumn`, :class:`HiddenColumn`), use it.
    2. Otherwise derive a default marker from the Python field type
       (``str`` → :class:`TextColumn`, ``int``/``float`` →
       :class:`NumericColumn`, ``bool`` → :class:`BooleanColumn`,
       ``date`` → :class:`DateColumn`, ``Literal[…]`` or :class:`Enum`
       subclass → :class:`TextColumn` with a :class:`TextChoiceFilter`).
    3. Convert the marker plus the field type into a :class:`Column`
       with a sensible default cell renderer.

    Fields whose type can't be defaulted are silently skipped — same
    contract as :func:`read_form_field_annotations`.
    """
    result: dict[str, RenderColumn[T]] = {}
    for field_name, info in model.model_fields.items():
        annotation_type = _peel_optional(info.annotation)
        marker = _find_column(info)
        if marker is None:
            marker = _derive_column_marker(annotation_type)
        if marker is None:
            continue
        result[field_name] = _build_column(field_name, info, annotation_type, marker)
    return result


def _derive_column_marker(annotation) -> Column | None:
    """Pick a default column marker for ``annotation`` based on its type."""
    if annotation is str:
        return TextColumn()
    if annotation is bool:
        return BooleanColumn()
    if annotation is int or annotation is float:
        return NumericColumn()
    # `datetime` before `date` — datetime subclasses date, so check the more
    # specific type first (identity comparison here means they never overlap,
    # but keep the order intentional).
    if annotation is datetime:
        return DateTimeColumn()
    if annotation is date:
        return DateColumn()
    options = _options_for_choice_type(annotation)
    if options is not None:
        return TextColumn(
            filter=TextChoiceFilter(options=options),
        )
    inner = _peel_collection(annotation)
    if inner is not None:
        # ``list[str]`` → free-form pills, no filter options; ``list[Literal]`` /
        # ``list[Enum]`` → pills + a closed-set intersection filter.
        inner_options = _options_for_choice_type(inner)
        if inner is str or inner_options is not None:
            return TextListColumn(
                filter=TextListFilter(options=inner_options)
                if inner_options is not None
                else TextListFilter(),
            )
    return None


def _build_column[T](
    field_name: str,
    info: FieldInfo,
    annotation_type,
    marker: Column,
) -> RenderColumn[T]:
    """Turn ``marker`` + the field's Python type into a renderable :class:`Column`."""
    label = marker.label if marker.label is not None else to_title_case(field_name)
    visible = not isinstance(marker, HiddenColumn)
    width = getattr(marker, "width", None) or Flex()
    filter_type = _filter_type_for(marker, annotation_type)
    render = _default_cell_renderer(field_name, annotation_type, marker)
    kind = getattr(marker, "kind", None) or _default_kind(annotation_type)
    return RenderColumn(
        key=field_name,
        label=label,
        header=label,
        render=render,
        width=width,
        filter_type=filter_type,
        visible=visible,
        kind=kind,
        sortable=getattr(marker, "sortable", True),
    )


def _default_kind(annotation_type) -> ColumnKind | None:
    """Per-type cell ``kind`` default. Drives default alignment and font features."""
    if _peel_collection(annotation_type) is not None:
        return "list"
    if annotation_type is bool:
        return "boolean"
    if annotation_type is int or annotation_type is float:
        return "numeric"
    # `datetime` reuses the `"date"` cell kind (right-aligned, tabular figures).
    if annotation_type is datetime:
        return "date"
    if annotation_type is date:
        return "date"
    if annotation_type is str:
        return "text"
    if isinstance(annotation_type, type) and issubclass(annotation_type, Enum):
        return "text"
    return None


def _filter_type_for(marker: Column, annotation_type) -> FilterType | None:
    """Translate a marker's ``filter`` flag + field type into a :class:`FilterType`."""
    if isinstance(marker, TextColumn):
        if marker.filter is None:
            return None
        if isinstance(marker.filter, TextChoiceFilter):
            return _choice_filter_from_marker(
                marker.filter, multiple=False, list_semantics=False
            )
        if isinstance(marker.filter, MultipleChoiceFilter):
            return _choice_filter_from_marker(
                marker.filter, multiple=True, list_semantics=False
            )
        return _filter_type_from_python_type(annotation_type) or TextFilterType()
    if isinstance(marker, NumericColumn):
        return NumericFilterType() if marker.filter else None
    if isinstance(marker, DateColumn):
        return DateFilterType() if marker.filter else None
    if isinstance(marker, DateTimeColumn):
        return DateFilterType() if marker.filter else None
    if isinstance(marker, BooleanColumn):
        return BooleanFilterType() if marker.filter else None
    if isinstance(marker, TextListColumn):
        if marker.filter is None:
            return None
        return _choice_filter_from_marker(
            marker.filter, multiple=True, list_semantics=True
        )
    if isinstance(marker, HiddenColumn):
        match marker.filter:
            case None:
                return None
            case TextChoiceFilter():
                return _choice_filter_from_marker(
                    marker.filter, multiple=False, list_semantics=False
                )
            case MultipleChoiceFilter():
                return _choice_filter_from_marker(
                    marker.filter, multiple=True, list_semantics=False
                )
            case TextListFilter():
                return _choice_filter_from_marker(
                    marker.filter, multiple=True, list_semantics=True
                )
            case TextFilter():
                return TextFilterType()
            case NumericFilter():
                return NumericFilterType()
            case DateFilter():
                return DateFilterType()
            case BooleanFilter():
                return BooleanFilterType()
            case _:
                raise AssertionError(f"unhandled filter marker: {marker.filter!r}")
    return None


def _choice_filter_from_marker(
    marker_filter: TextChoiceFilter | MultipleChoiceFilter | TextListFilter,
    *,
    multiple: bool,
    list_semantics: bool,
) -> ChoiceFilterType | ListChoiceFilterType:
    """Build a choice / list filter view-type from a filter marker.

    Mirrors the forms pattern: the developer's ``control`` (or a
    :class:`DropdownControl` synthesized from ``options`` when absent) is
    recorded on ``_control`` for the drawer to isinstance-dispatch. Static
    option sequences are materialized eagerly into ``choices``; callable
    providers attach to ``_choices_provider`` and resolve at render time.
    ``multiple`` (single vs. multi-select) drives the operator vocabulary.
    """
    control = marker_filter.control or DropdownControl(
        options=marker_filter.options or ()
    )
    provider = control.options
    cf: ChoiceFilterType | ListChoiceFilterType = (
        ListChoiceFilterType()
        if list_semantics
        else ChoiceFilterType(multiple=multiple)
    )
    if callable(provider):
        cf._choices_provider = provider
    else:
        cf.choices = [
            ChoiceFilterOption(label=o.label, value=o.value) for o in provider
        ]
    cf._control = control
    return cf


def _filter_type_from_python_type(annotation_type) -> FilterType | None:
    """Default :class:`FilterType` for a bare Python field type."""
    options = _options_for_choice_type(annotation_type)
    if options is not None:
        return ChoiceFilterType(
            choices=[ChoiceFilterOption(label=o.label, value=o.value) for o in options],
        )
    if annotation_type is str:
        return TextFilterType()
    if annotation_type is int or annotation_type is float:
        return NumericFilterType()
    if annotation_type is datetime:
        return DateFilterType()
    if annotation_type is date:
        return DateFilterType()
    if annotation_type is bool:
        return BooleanFilterType()
    return None


def _default_cell_renderer(
    field_name: str, annotation_type, marker: Column
) -> Callable[[Any], y.Node]:
    """Build a row → ``y.Node`` callable that formats one field value.

    Dispatches on the marker for type-specific config (currently only
    :class:`DateColumn.format`) and falls back to a plain per-type value
    renderer otherwise.
    """
    if isinstance(marker, (DateColumn, DateTimeColumn)):
        value_renderer = _date_value_renderer(marker.format)
    elif isinstance(marker, NumericColumn):
        value_renderer = _number_value_renderer(marker.format)
    elif isinstance(marker, TextListColumn):
        value_renderer = _list_value_renderer()
    else:
        value_renderer = _value_renderer_for(annotation_type)

    def render(row: Any) -> y.Node:
        return value_renderer(getattr(row, field_name, None))

    return render


def _value_renderer_for(annotation_type) -> Callable[[Any], y.Node]:
    """Per-type value formatter used by the default cell renderer."""
    if annotation_type is bool:
        return lambda v: y.span["yes" if v else "no"]
    if annotation_type is datetime:
        return lambda v: y.span[v.isoformat() if v is not None else ""]
    if annotation_type is date:
        return lambda v: y.span[v.isoformat() if v is not None else ""]
    if isinstance(annotation_type, type) and issubclass(annotation_type, Enum):
        return lambda v: y.span[str(v.value) if v is not None else ""]
    return lambda v: y.span[str(v) if v is not None else ""]


def _list_value_renderer() -> Callable[[Any], y.Node]:
    """Render a list-valued cell as a row of pills.

    Each element is stringified via :func:`_default_to_choice_value` so an
    ``Enum`` member's ``.value`` (not its ``repr``) shows on the pill, matching
    the labels the intersection filter offers. ``None`` / empty → an empty
    pill container.
    """

    def render(v: Any) -> y.Node:
        if not v:
            return pill.container()
        return pill.container(*[pill(_default_to_choice_value(item)) for item in v])

    return render


def _date_value_renderer(fmt: DateFormat | DateTimeFormat) -> Callable[[Any], y.Node]:
    """Date/datetime-cell value formatter, dispatched on the format marker.

    Handles both :data:`DateFormat` (:class:`DateColumn`) and
    :data:`DateTimeFormat` (:class:`DateTimeColumn`); the two unions share the
    ``Iso`` / ``Pattern`` / ``Relative`` members and differ only in the
    localized variant (:class:`LocalizedDateFormat` renders the date,
    :class:`LocalizedDateTimeFormat` the date **and** time).

    For the localized variants the locale is resolved at *render time* (not
    column-build time) — each request can have a different ``Accept-Language``.
    """
    if isinstance(fmt, IsoDateFormat):
        return lambda v: y.span[v.isoformat() if v is not None else ""]
    if isinstance(fmt, PatternDateFormat):
        pattern = fmt.pattern
        return lambda v: y.span[v.strftime(pattern) if v is not None else ""]
    if isinstance(fmt, LocalizedDateFormat):
        width = fmt.width
        pinned_locale = fmt.locale
        fallback = fmt.fallback
        pinned_tz = fmt.timezone
        source_tz = fmt.source_timezone

        def render_localized(v: Any) -> y.Node:
            if v is None:
                return y.span[""]
            locale = pinned_locale or negotiate_locale(fallback=fallback)
            value = v
            # A bare `date` has no instant — format as-is. Only a `datetime`
            # represents a point in time that must be moved into the user's
            # zone before the calendar date is taken (off-by-one near midnight).
            if isinstance(v, datetime):
                aware = (
                    v if v.tzinfo is not None else v.replace(tzinfo=ZoneInfo(source_tz))
                )
                display_tz = pinned_tz or negotiate_timezone()
                value = aware.astimezone(ZoneInfo(display_tz))
            return y.span[babel_format_date(value, format=width, locale=locale)]

        return render_localized
    if isinstance(fmt, LocalizedDateTimeFormat):
        width = fmt.width
        pinned_locale = fmt.locale
        fallback = fmt.fallback
        pinned_tz = fmt.timezone
        source_tz = fmt.source_timezone

        def render_localized_datetime(v: Any) -> y.Node:
            if v is None:
                return y.span[""]
            locale = pinned_locale or negotiate_locale(fallback=fallback)
            # Promote a bare `date` to midnight so babel always gets a datetime;
            # a real `datetime` instant is moved into the display zone first.
            moment = v if isinstance(v, datetime) else datetime.combine(v, time.min)
            aware = (
                moment
                if moment.tzinfo is not None
                else moment.replace(tzinfo=ZoneInfo(source_tz))
            )
            display_tz = pinned_tz or negotiate_timezone()
            value = aware.astimezone(ZoneInfo(display_tz))
            return y.span[babel_format_datetime(value, format=width, locale=locale)]

        return render_localized_datetime
    if isinstance(fmt, RelativeDateFormat):
        source_tz = fmt.source_timezone

        def render_relative(v: Any) -> y.Node:
            if v is None:
                return y.span[""]
            # humanize.naturaltime requires a datetime; bare date → midnight.
            moment = v if isinstance(v, datetime) else datetime.combine(v, time.min)
            # Anchor both sides to UTC so the delta is independent of the
            # server's local clock: naive values are read as `source_timezone`
            # (UTC by convention), the reference is always now-in-UTC.
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=ZoneInfo(source_tz))
            return y.span[humanize.naturaltime(moment, when=datetime.now(UTC))]

        return render_relative
    raise AssertionError(f"unhandled DateFormat: {fmt!r}")


def _number_value_renderer(fmt: NumberFormat) -> Callable[[Any], y.Node]:
    """Numeric-cell value formatter, dispatched on :data:`NumberFormat`.

    For :class:`LocalizedNumberFormat` and :class:`CurrencyNumberFormat` the
    locale is resolved at *render time* (not column-build time) — each
    request can have a different ``Accept-Language``.
    """
    if isinstance(fmt, IsoNumberFormat):
        return lambda v: y.span[str(v) if v is not None else ""]

    if isinstance(fmt, PatternNumberFormat):
        spec = fmt.spec
        return lambda v: y.span[format(v, spec) if v is not None else ""]

    if isinstance(fmt, LocalizedNumberFormat):
        width = fmt.width
        decimals = fmt.decimals
        pinned = fmt.locale
        fallback = fmt.fallback

        def render_localized_number(v: Any) -> y.Node:
            if v is None:
                return y.span[""]
            locale = pinned or negotiate_locale(fallback=fallback)
            if width == "compact":
                return y.span[
                    babel_format_compact_decimal(v, format_type="short", locale=locale)
                ]
            decimal_format = f"#,##0.{'0' * decimals}" if decimals is not None else None
            return y.span[babel_format_decimal(v, format=decimal_format, locale=locale)]

        return render_localized_number

    if isinstance(fmt, CurrencyNumberFormat):
        currency = fmt.currency
        pinned = fmt.locale
        fallback = fmt.fallback

        def render_currency(v: Any) -> y.Node:
            if v is None:
                return y.span[""]
            locale = pinned or negotiate_locale(fallback=fallback)
            return y.span[babel_format_currency(v, currency, locale=locale)]

        return render_currency

    raise AssertionError(f"unhandled NumberFormat: {fmt!r}")
