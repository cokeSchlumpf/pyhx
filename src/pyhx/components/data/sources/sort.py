"""Sort order primitives consumed by :class:`Query`."""

from typing import Literal

from pydantic import BaseModel

SortOrderDirection = Literal["asc", "desc"]
"""Sort direction — ascending or descending."""


class SortOrder(BaseModel):
    """One sort key applied to a query.

    A :class:`Query` carries a list of these in priority order: the first
    entry is the primary sort, the second breaks ties, and so on.

    Attributes
    ----------
    key : str
        The field name to sort by — matches the column's ``key`` attribute.
    order : SortOrderDirection
        Ascending (``"asc"``) or descending (``"desc"``).
    """

    key: str
    order: SortOrderDirection
