"""Calendar label vocabulary — localisable weekday and month names.

A :class:`CalendarLabels` holds the short weekday abbreviations and full month
names a calendar or timeline renders, so the display strings can be localised
without touching the rendering code. Override any field to translate, e.g.
``CalendarLabels(monday="Mo", january="Januar")``, and look a label up for a
given :class:`datetime.date` via :meth:`weekday` / :meth:`month`.

Pure value type — frozen, hashable, equality by value; no rendering and no
dependency on ``data`` / ``primitives`` / ``layouts``.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CalendarLabels:
    """Localisable weekday and month labels.

    Weekday fields are single-letter abbreviations in :meth:`datetime.date.weekday`
    order (Monday is ``0``); month fields are full names. Override any field to
    localise, e.g. ``CalendarLabels(monday="Mo", january="Januar")``. Use
    :meth:`weekday` / :meth:`month` to look the label up for a given date.
    """

    monday: str = "M"
    tuesday: str = "T"
    wednesday: str = "W"
    thursday: str = "T"
    friday: str = "F"
    saturday: str = "S"
    sunday: str = "S"

    january: str = "January"
    february: str = "February"
    march: str = "March"
    april: str = "April"
    may: str = "May"
    june: str = "June"
    july: str = "July"
    august: str = "August"
    september: str = "September"
    october: str = "October"
    november: str = "November"
    december: str = "December"

    def weekday(self, day: date) -> str:
        """The single-letter label for ``day``'s weekday (Monday-first)."""
        return (
            self.monday,
            self.tuesday,
            self.wednesday,
            self.thursday,
            self.friday,
            self.saturday,
            self.sunday,
        )[day.weekday()]

    def month(self, day: date) -> str:
        """The full month name for ``day``."""
        return (
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
