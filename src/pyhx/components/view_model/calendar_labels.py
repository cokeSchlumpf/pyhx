"""Calendar label vocabulary — localisable weekday and month names.

A :class:`CalendarLabels` holds the short weekday abbreviations and full month
names a calendar or timeline renders. Unset fields follow the language of the
request (names from Babel); set fields override them, e.g.
``CalendarLabels(monday="Mo", january="Januar")``. Look a label up for a
given :class:`datetime.date` via :meth:`weekday` / :meth:`month`.

Pure value type — frozen, hashable, equality by value; no rendering and no
dependency on ``data`` / ``primitives`` / ``layouts``.
"""

from dataclasses import dataclass
from datetime import date

from babel.dates import get_day_names, get_month_names

from pyhx.core.primitives.negotiate_locale import negotiate_locale


@dataclass(frozen=True)
class CalendarLabels:
    """Weekday and month labels, in the request language unless set.

    Weekday fields are single-letter abbreviations in :meth:`datetime.date.weekday`
    order (Monday is ``0``); month fields are full names. Unset fields (``None``)
    use the names of the request language; set fields override them, e.g.
    ``CalendarLabels(monday="Mo", january="Januar")``. Use :meth:`weekday` /
    :meth:`month` to look the label up for a given date.
    """

    monday: str | None = None
    tuesday: str | None = None
    wednesday: str | None = None
    thursday: str | None = None
    friday: str | None = None
    saturday: str | None = None
    sunday: str | None = None

    january: str | None = None
    february: str | None = None
    march: str | None = None
    april: str | None = None
    may: str | None = None
    june: str | None = None
    july: str | None = None
    august: str | None = None
    september: str | None = None
    october: str | None = None
    november: str | None = None
    december: str | None = None

    def weekday(self, day: date) -> str:
        """The single-letter label for ``day``'s weekday (Monday-first).

        Unset fields use the narrow weekday name of the request language.
        """
        label = (
            self.monday,
            self.tuesday,
            self.wednesday,
            self.thursday,
            self.friday,
            self.saturday,
            self.sunday,
        )[day.weekday()]
        if label is not None:
            return label
        return get_day_names("narrow", locale=negotiate_locale())[day.weekday()]

    def month(self, day: date) -> str:
        """The full month name for ``day``.

        Unset fields use the month name of the request language.
        """
        label = (
            self.january,
            self.february,
            self.march,
            self.april,
            self.may,
            self.june,
            self.july,
            self.august,
            self.september,
            self.october,
            self.november,
            self.december,
        )[day.month - 1]
        if label is not None:
            return label
        name = get_month_names("wide", "stand-alone", locale=negotiate_locale())[
            day.month
        ]
        # Shown as a heading: capitalized also where the language writes it
        # in lower case (it, fr).
        return name[:1].upper() + name[1:]
