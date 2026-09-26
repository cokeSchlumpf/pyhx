"""URL path templates with named variables.

Templates use the syntax ``/static/{variable}`` (inspired by RFC 6570). Segments
and variable names are restricted to ``[a-z0-9_-]`` (variables must start with a
letter). Trailing slashes are not permitted.

Examples
--------
>>> t = PathTemplate("/users/{user_id}/posts/{post_id}")
>>> t.expand(user_id=42, post_id="abc")
'/users/42/posts/abc'
>>> t.match("/users/42/posts/abc")
{'user_id': '42', 'post_id': 'abc'}
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import overload
from urllib.parse import urlencode


def encode_query(query: Mapping[str, object]) -> str:
    """Render a mapping of query parameters as a URL query string.

    Keys whose value is ``None`` are omitted. Sequence values (``list`` or
    ``tuple``) expand into repeated parameters (``{"t": ["a", "b"]}`` becomes
    ``?t=a&t=b``), with ``None`` elements skipped. All keys and values are
    URL-escaped. Insertion order is preserved.

    Parameters
    ----------
    query : Mapping[str, object]
        The query parameters to encode.

    Returns
    -------
    str
        The query string prefixed with ``"?"``, or an empty string when the
        mapping is empty (or every value is ``None``).

    Examples
    --------
    >>> encode_query({"param": 123, "foo": "bar"})
    '?param=123&foo=bar'
    >>> encode_query({})
    ''
    """
    items: list[tuple[str, object]] = []
    for key, value in query.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            items.extend((key, element) for element in value if element is not None)
        else:
            items.append((key, value))
    if not items:
        return ""
    return "?" + urlencode(items)


_PATH_PATTERN = re.compile(r"^(?:/|(?:/(?:[a-z0-9_-]+|\{[a-z][a-z0-9_]*\}))+)$")
_STATIC_PATH_PATTERN = re.compile(r"^(?:/|(?:/[a-z0-9_-]+)+)$")
_VARIABLE_PATTERN = re.compile(r"^\{([a-z][a-z0-9_]*)\}$")


def _concat_path_strings(left: str, right: str) -> str:
    """Concatenate two slash-rooted paths into a single slash-rooted path.

    Single slash between, no trailing slash (except for the root path itself).
    """
    combined = left.rstrip("/") + "/" + right.lstrip("/")
    return combined.rstrip("/") or "/"


@dataclass
class StaticSegment:
    """A literal path segment.

    Attributes
    ----------
    value : str
        The segment text (e.g. ``"users"``).
    """

    value: str

    def __str__(self) -> str:
        return self.value


@dataclass
class VariableSegment:
    """A named variable placeholder in a path template.

    Attributes
    ----------
    value : str
        The variable name (e.g. ``"user_id"``), without braces.
    """

    value: str

    def __str__(self) -> str:
        return f"{{{self.value}}}"


PathSegment = StaticSegment | VariableSegment


class PathTemplate:
    """A parsed URL path template with named variables.

    Instances are immutable, hashable, and comparable by their string form.

    Examples
    --------
    >>> t = PathTemplate("/users/{user_id}")
    >>> t.expand(user_id=1)
    '/users/1'
    >>> t.match("/users/1")
    {'user_id': '1'}
    """

    def __init__(self, value: str) -> None:
        """Parse a template string.

        Parameters
        ----------
        value : str
            The template, e.g. ``"/users/{user_id}"`` or ``"/"``.

        Raises
        ------
        ValueError
            If ``value`` is not a syntactically valid template, or if the same
            variable name appears more than once.
        """
        if not _PATH_PATTERN.fullmatch(value):
            raise ValueError(f"Invalid path template: `{value}`")

        segments: list[PathSegment] = []
        variables: set[str] = set()

        raw_segments = [s for s in value.split("/") if s]
        for raw_segment in raw_segments:
            if (m := _VARIABLE_PATTERN.fullmatch(raw_segment)) is not None:
                name = m.group(1)
                if name in variables:
                    raise ValueError(
                        f"Duplicate variable `{name}` in path template `{value}`."
                    )

                variables.add(name)
                segments.append(VariableSegment(name))
            else:
                segments.append(StaticSegment(raw_segment))

        self._segments = segments
        self._variables = variables

        if segments:
            pattern = "".join(
                rf"/(?P<{s.value}>[a-z0-9_-]+)"
                if isinstance(s, VariableSegment)
                else f"/{re.escape(s.value)}"
                for s in segments
            )
        else:
            pattern = "/"
        self._match_pattern = re.compile(f"^{pattern}$")

    def expand(self, **values: object) -> "Path":
        """Substitute variable values into the template.

        Parameters
        ----------
        **values
            One value per template variable. Values are converted to strings
            via ``str()``.

        Returns
        -------
        Path
            The rendered path, e.g. ``Path("/users/42")``.

        Raises
        ------
        ValueError
            If any template variable is missing from ``values``, or if
            ``values`` contains keys that are not template variables.
        """
        provided = set(values)
        missing = self._variables - provided
        if missing:
            raise ValueError(f"Missing variables: {sorted(missing)}")
        unexpected = provided - self._variables
        if unexpected:
            raise ValueError(f"Unexpected variables: {sorted(unexpected)}")

        parts: list[str] = []
        for segment in self._segments:
            if isinstance(segment, VariableSegment):
                parts.append(str(values[segment.value]))
            else:
                parts.append(segment.value)
        return Path("/" + "/".join(parts))

    def format(self, **values: object) -> "Path":
        """Alias for :meth:`expand`."""
        return self.expand(**values)

    def is_parameterized(self) -> bool:
        """Return whether the template contains any variables.

        Returns
        -------
        bool
            ``True`` if at least one variable segment is present, else
            ``False``.
        """
        return bool(self._variables)

    def match(self, path: str) -> dict[str, str] | None:
        """Match a concrete path against the template.

        Parameters
        ----------
        path : str
            A concrete path to test, e.g. ``"/users/42"``.

        Returns
        -------
        dict of str to str, or None
            A mapping of variable name to matched value if ``path`` matches
            the template, otherwise ``None``. For a template with no
            variables, a successful match returns ``{}``.
        """
        m = self._match_pattern.fullmatch(path)
        if m is None:
            return None
        return m.groupdict()

    def join(self, other: "PathTemplate | Path") -> "PathTemplate":
        """Concatenate ``other`` onto this template, returning a new template.

        Adding a static :class:`Path` to a template keeps it a template, so
        the result is always a :class:`PathTemplate`. Slash boundaries are
        normalized: ``PathTemplate("/").join(PathTemplate("/x"))`` is
        ``"/x"``, not ``"//x"``.
        """
        return PathTemplate(_concat_path_strings(str(self), str(other)))

    def __truediv__(self, other: "PathTemplate | Path") -> "PathTemplate":
        return self.join(other)

    def __str__(self) -> str:
        return "/" + "/".join([f"{s}" for s in self._segments])

    def __repr__(self) -> str:
        return f"PathTemplate({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PathTemplate):
            return NotImplemented

        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))


class Path:
    """A parsed static URL path with no variable segments.

    Instances are immutable, hashable, and comparable by their string form.

    Examples
    --------
    >>> p = Path("/users/42")
    >>> str(p)
    '/users/42'
    >>> Path("/users/{id}")
    Traceback (most recent call last):
        ...
    ValueError: Invalid path: `/users/{id}`
    """

    def __init__(self, value: str) -> None:
        if not _STATIC_PATH_PATTERN.fullmatch(value):
            raise ValueError(f"Invalid path: `{value}`")
        self._value = value

    def is_prefix_of(self, other: "Path") -> bool:
        """Return True if this path is a path-element prefix of ``other``.

        A path is considered a prefix when each of its ``/``-delimited
        segments matches the corresponding leading segment of ``other``.
        Comparison is segment-based, so ``/users`` is **not** a prefix of
        ``/users-admin``. Equal paths are prefixes of each other, and the
        root path ``/`` is a prefix of every path.

        Parameters
        ----------
        other : Path
            The path to test against.

        Returns
        -------
        bool
            ``True`` if ``self``'s segments are a (possibly equal) leading
            slice of ``other``'s segments.

        Examples
        --------
        >>> Path("/a").is_prefix_of(Path("/a/b"))
        True
        >>> Path("/a").is_prefix_of(Path("/a"))
        True
        >>> Path("/").is_prefix_of(Path("/x"))
        True
        >>> Path("/users").is_prefix_of(Path("/users-admin"))
        False
        """
        self_segments = [s for s in self._value.split("/") if s]
        other_segments = [s for s in other._value.split("/") if s]
        if len(self_segments) > len(other_segments):
            return False
        return self_segments == other_segments[: len(self_segments)]

    @overload
    def join(self, other: "Path") -> "Path": ...
    @overload
    def join(self, other: "PathTemplate") -> "PathTemplate": ...
    def join(self, other: "Path | PathTemplate") -> "Path | PathTemplate":
        """Concatenate ``other`` onto this path, returning a new path.

        Joining with a :class:`Path` keeps the result concrete; joining with
        a :class:`PathTemplate` widens the result to a template. Slash
        boundaries are normalized.
        """
        combined = _concat_path_strings(str(self), str(other))
        if isinstance(other, PathTemplate):
            return PathTemplate(combined)
        return Path(combined)

    @overload
    def __truediv__(self, other: "Path") -> "Path": ...
    @overload
    def __truediv__(self, other: "PathTemplate") -> "PathTemplate": ...
    def __truediv__(self, other: "Path | PathTemplate") -> "Path | PathTemplate":
        return self.join(other)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Path({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Path):
            return self._value == other._value
        if isinstance(other, str):
            return self._value == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)
