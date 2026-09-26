from dataclasses import dataclass
from typing import Literal

from ...view_model import OptionsProvider
from ...view_model.columns import ColumnKind, ColumnWidth, Flex
from .controls import MultiselectChoiceControl, TextChoiceControl

#
# Date formatting
#


@dataclass(frozen=True, kw_only=True)
class IsoDateFormat:
    """ISO 8601 (``YYYY-MM-DD``). Default."""


@dataclass(frozen=True, kw_only=True)
class PatternDateFormat:
    """``strftime`` pattern, e.g. ``"%d %b %Y"`` → ``"25 Apr 2024"``.

    ``%b`` / ``%B`` are locale-dependent in ``strftime`` — they read from
    the OS locale, which can drift across environments. For deterministic
    localized output, use :class:`LocalizedDateFormat` instead.
    """

    pattern: str

    @classmethod
    def short(cls) -> "PatternDateFormat":
        return cls(pattern="%d %b %Y")

    @classmethod
    def long(cls) -> "PatternDateFormat":
        return cls(pattern="%d %B %Y")

    @classmethod
    def numeric(cls) -> "PatternDateFormat":
        return cls(pattern="%d.%m.%Y")


@dataclass(frozen=True, kw_only=True)
class LocalizedDateFormat:
    """``babel``-formatted date, locale picked from the request's ``Accept-Language``.

    **Locale** resolution at render time:

    1. If ``locale`` is pinned (e.g. ``"de_CH"``), use it verbatim.
    2. Else negotiate from the current request via
       :func:`pyhx.core.primitives.negotiate_locale`.
    3. Else (no request in context, no header match) fall back to ``fallback``.

    ``width`` matches babel's CLDR vocabulary, so the same width produces
    the culturally-correct ordering, separators, and month names per locale.

    **Timezone.** A ``date`` carries no instant, so it is formatted as-is. A
    ``datetime`` *is* an instant: naive values are interpreted in
    ``source_timezone`` (``"UTC"`` by convention — we store UTC), then
    converted to the display zone before the date is taken. This matters near
    midnight — ``2024-04-25T23:00Z`` is already the 26th in ``Europe/Zurich``.

    Display-zone resolution at render time:

    1. If ``timezone`` is pinned (e.g. ``"Europe/Zurich"``), use it verbatim —
       the app/developer-specified zone always wins.
    2. Else negotiate from the request's ``hx_tz`` cookie via
       :func:`pyhx.core.primitives.negotiate_timezone`.
    3. Else fall back to the configured default (``UTC`` unless overridden).
    """

    width: Literal["short", "medium", "long", "full"] = "medium"
    locale: str | None = None
    fallback: str = "en"
    timezone: str | None = None
    source_timezone: str = "UTC"


@dataclass(frozen=True, kw_only=True)
class LocalizedDateTimeFormat:
    """``babel``-formatted date **and time**, locale picked from ``Accept-Language``.

    The date+time counterpart of :class:`LocalizedDateFormat` — it renders the
    calendar date *and* the time-of-day (``width="medium"`` includes seconds,
    ``HH:mm:ss``) via ``babel.dates.format_datetime``. Locale and timezone
    resolution are identical to :class:`LocalizedDateFormat`:

    1. Locale — pinned ``locale``, else negotiated from the request, else
       ``fallback``.
    2. Display zone — pinned ``timezone``, else the request's ``hx_tz`` cookie,
       else the configured default. A naive value is interpreted in
       ``source_timezone`` (``"UTC"`` by convention) before conversion.

    Use this on :class:`DateTimeColumn`; :class:`LocalizedDateFormat` is
    date-only and drops the time.
    """

    width: Literal["short", "medium", "long", "full"] = "medium"
    locale: str | None = None
    fallback: str = "en"
    timezone: str | None = None
    source_timezone: str = "UTC"


@dataclass(frozen=True, kw_only=True)
class RelativeDateFormat:
    """Server-rendered relative time, e.g. ``"3 hours ago"`` (via ``humanize``).

    Frozen at render time — does not auto-update in the browser.

    The reference point is always *now in UTC* (``datetime.now(timezone.utc)``),
    independent of the server's local clock. Naive stored values are
    interpreted in ``source_timezone`` (``"UTC"`` by convention) before the
    delta is taken; the resulting phrase is timezone-independent (``"3 hours
    ago"`` reads the same everywhere), so no display zone is needed.
    """

    source_timezone: str = "UTC"


DateFormat = (
    IsoDateFormat | PatternDateFormat | LocalizedDateFormat | RelativeDateFormat
)
"""Discriminated union of date-cell formatters used by :class:`DateColumn`."""


DateTimeFormat = (
    IsoDateFormat | PatternDateFormat | LocalizedDateTimeFormat | RelativeDateFormat
)
"""Discriminated union of datetime-cell formatters used by :class:`DateTimeColumn`.

Mirrors :data:`DateFormat` but swaps the date-only :class:`LocalizedDateFormat`
for :class:`LocalizedDateTimeFormat` so localized output keeps the time. The
``Iso`` / ``Pattern`` / ``Relative`` members already render ``datetime`` values
with their time component and are shared as-is."""


#
# Number formatting
#


@dataclass(frozen=True, kw_only=True)
class IsoNumberFormat:
    """Raw ``str(value)``. No separators, no locale awareness.

    Opt-in for technical / monospace contexts. UI tables almost always
    want :class:`LocalizedNumberFormat` instead.
    """


@dataclass(frozen=True, kw_only=True)
class PatternNumberFormat:
    """Python format-spec string, e.g. ``",.2f"`` → ``"1,234.56"``.

    Locale-independent — separators and grouping are whatever the spec
    says. Use :class:`LocalizedNumberFormat` for locale-aware output.
    """

    spec: str

    @classmethod
    def thousands(cls) -> "PatternNumberFormat":
        return cls(spec=",.0f")

    @classmethod
    def thousands_decimals(cls, decimals: int = 2) -> "PatternNumberFormat":
        return cls(spec=f",.{decimals}f")

    @classmethod
    def scientific(cls, decimals: int = 2) -> "PatternNumberFormat":
        return cls(spec=f".{decimals}e")

    @classmethod
    def percent(cls, decimals: int = 0) -> "PatternNumberFormat":
        return cls(spec=f".{decimals}%")


@dataclass(frozen=True, kw_only=True)
class LocalizedNumberFormat:
    """``babel``-formatted number, locale picked from ``Accept-Language``.

    Resolution mirrors :class:`LocalizedDateFormat`:

    1. If ``locale`` is pinned, use it verbatim.
    2. Else negotiate via :func:`pyhx.core.primitives.negotiate_locale`.
    3. Else fall back to ``fallback``.

    ``width="default"`` uses ``babel.numbers.format_decimal``;
    ``"compact"`` uses ``format_compact_decimal`` (``"1.2K"``).
    ``decimals=None`` lets babel pick the locale-default precision;
    a number pins it to exactly that many fraction digits.
    """

    width: Literal["default", "compact"] = "default"
    decimals: int | None = None
    locale: str | None = None
    fallback: str = "en"


@dataclass(frozen=True, kw_only=True)
class CurrencyNumberFormat:
    """``babel``-formatted currency value, locale-aware.

    Carries a unit (``currency`` — ISO 4217, e.g. ``"EUR"``, ``"USD"``,
    ``"CHF"``) on top of locale resolution. Kept distinct from
    :class:`LocalizedNumberFormat` because currency is semantically a
    different kind of value, not a plain number with a symbol slapped on.
    """

    currency: str
    locale: str | None = None
    fallback: str = "en"


NumberFormat = (
    IsoNumberFormat | PatternNumberFormat | LocalizedNumberFormat | CurrencyNumberFormat
)
"""Discriminated union of numeric-cell formatters used by :class:`NumericColumn`."""


#
# Filter controls
#
@dataclass(frozen=True, kw_only=True)
class TextFilter:
    pass


@dataclass(frozen=True, kw_only=True)
class TextChoiceFilter:
    """Single-select choice filter for a scalar column.

    Mirrors the forms pattern: ``control`` picks the widget
    (:class:`DropdownControl`, :class:`SegmentControl`,
    :class:`RadioFieldsetControl`, :class:`DrawerRadioControl`). When
    ``control`` is ``None`` the reader synthesizes a
    :class:`DropdownControl` from ``options`` — a convenience so
    ``TextChoiceFilter(options=...)`` keeps working.
    """

    control: TextChoiceControl | None = None
    options: OptionsProvider | None = None


@dataclass(frozen=True, kw_only=True)
class MultipleChoiceFilter:
    """Multi-select choice filter for a *scalar* column.

    The row's single value matches when it is *any of* the selected set
    (set membership). ``control`` picks the multi-select widget
    (:class:`CheckboxFieldsetControl`, :class:`DropdownControl`,
    :class:`DrawerSelectControl`); ``None`` synthesizes a
    :class:`DropdownControl` (rendered as a multi-select) from ``options``.
    """

    control: MultiselectChoiceControl | None = None
    options: OptionsProvider | None = None


@dataclass(frozen=True, kw_only=True)
class TextListFilter:
    """Multi-select filter for a *list-valued* column (:class:`TextListColumn`).

    A row matches when its ``list`` value *intersects* the selected set.
    ``control`` picks the multi-select widget exactly like
    :class:`MultipleChoiceFilter`.
    """

    control: MultiselectChoiceControl | None = None
    options: OptionsProvider | None = None


@dataclass(frozen=True, kw_only=True)
class NumericFilter:
    pass


@dataclass(frozen=True, kw_only=True)
class DateFilter:
    pass


@dataclass(frozen=True, kw_only=True)
class BooleanFilter:
    pass


#
# Column annotations
#


@dataclass(frozen=True, kw_only=True)
class TextColumn:
    label: str | None = None
    tooltip: str | None = None
    width: ColumnWidth = Flex()
    kind: ColumnKind | None = None
    sortable: bool = True
    filter: TextFilter | TextChoiceFilter | MultipleChoiceFilter | None = TextFilter()


@dataclass(frozen=True, kw_only=True)
class NumericColumn:
    label: str | None = None
    tooltip: str | None = None
    width: ColumnWidth = Flex()
    kind: ColumnKind | None = None
    sortable: bool = True
    filter: bool = True
    format: NumberFormat = LocalizedNumberFormat()


@dataclass(frozen=True, kw_only=True)
class DateColumn:
    label: str | None = None
    tooltip: str | None = None
    width: ColumnWidth = Flex()
    kind: ColumnKind | None = None
    sortable: bool = True
    filter: bool = True
    format: DateFormat = LocalizedDateFormat(width="short")


@dataclass(frozen=True, kw_only=True)
class DateTimeColumn:
    """A ``datetime.datetime`` column — renders date **and** time-of-day.

    The instant-aware counterpart of :class:`DateColumn`. Auto-derived for
    ``datetime``-typed fields and defaults to :class:`RelativeDateFormat`
    (``"3 hours ago"``). For localized calendar+clock output use
    :class:`LocalizedDateTimeFormat`; :class:`LocalizedDateFormat` is date-only
    and is intentionally not accepted here.

    Filtering is day-granularity (the drawer's date picker yields a ``date``):
    a datetime cell is compared by its calendar date.
    """

    label: str | None = None
    tooltip: str | None = None
    width: ColumnWidth = Flex()
    kind: ColumnKind | None = None
    sortable: bool = True
    filter: bool = True
    format: DateTimeFormat = RelativeDateFormat()


@dataclass(frozen=True, kw_only=True)
class BooleanColumn:
    label: str | None = None
    tooltip: str | None = None
    width: ColumnWidth = Flex()
    kind: ColumnKind | None = None
    sortable: bool = True
    filter: bool = True


@dataclass(frozen=True, kw_only=True)
class HiddenColumn:
    """Marker for a field that should not render as a visible column.

    The derived :class:`Column` still participates in the filter drawer
    and can be sorted — it just never produces ``<th>`` / ``<td>`` cells.
    Use when a field is useful as a sort/filter key but cluttery in the
    table body (e.g. internal ids, timestamps, soft-delete flags).

    ``filter`` takes a filter marker (``TextFilter``, ``TextChoiceFilter``,
    ``MultipleChoiceFilter``, ``TextListFilter``, ``NumericFilter``,
    ``DateFilter``, or ``BooleanFilter``) to opt the hidden field into that
    filter kind in the drawer; ``None`` (default) leaves it unfilterable.
    """

    label: str | None = None
    sortable: bool = False
    filter: (
        TextFilter
        | TextChoiceFilter
        | MultipleChoiceFilter
        | TextListFilter
        | NumericFilter
        | DateFilter
        | BooleanFilter
        | None
    ) = None


@dataclass(frozen=True, kw_only=True)
class TextListColumn:
    """A ``list[str]`` / ``list[Literal]`` / ``list[Enum]`` column.

    Renders each element as a :func:`pill` in a pill container. Its natural
    filter is a multi-select :class:`TextListFilter` whose match semantics
    are *set intersection* — a row matches when its list shares any value
    with the selected set.
    """

    label: str | None = None
    tooltip: str | None = None
    width: ColumnWidth = Flex()
    kind: ColumnKind | None = None
    sortable: bool = False
    filter: TextListFilter | None = TextListFilter()


Column = (
    TextColumn
    | NumericColumn
    | DateColumn
    | DateTimeColumn
    | BooleanColumn
    | TextListColumn
    | HiddenColumn
)
