"""
Static file handling for PyHX web framework.

This module provides static file serving capabilities:

- `PYHX_STATIC_DIR`: Path to built-in PyHX static assets
- `MultiStaticFiles`: Static file handler supporting fallback directories
"""

import os
from pathlib import Path

from fastapi.staticfiles import StaticFiles

PYHX_STATIC_DIR = Path(__file__).parent.parent / "static"
"""Path to PyHX's built-in static assets (CSS, JS, fonts)."""


class MultiStaticFiles(StaticFiles):
    """
    A StaticFiles handler that searches multiple directories for assets.

    This extends Starlette's StaticFiles to support fallback directories.
    When a file is requested, it searches through the directories in order
    and returns the first match found.

    `PYHX_STATIC_DIR` is always appended last as a final fallback, so
    callers only need to supply their app-specific directories.

    This allows app-specific static files to override PyHX defaults, while
    still falling back to built-in assets (CSS framework, JS libraries, fonts).

    Parameters
    ----------
    directories : list[Path]
        App-specific directories to search, in priority order.
        The first directory containing the requested file wins.
        ``PYHX_STATIC_DIR`` is appended automatically.
    **kwargs
        Additional arguments passed to StaticFiles base class.

    Example
    -------
    >>> static = MultiStaticFiles([
    ...     Path("app/static"),      # App-specific overrides (checked first)
    ... ])
    >>> # Request for /static/css/custom.css checks app/static first,
    >>> # then falls back to PYHX_STATIC_DIR if not found

    See Also
    --------
    fastapi.staticfiles.StaticFiles : Base class
    """

    def __init__(self, directories: list[Path], **kwargs) -> None:
        """
        Initialize MultiStaticFiles with a list of directories to search.

        ``PYHX_STATIC_DIR`` is appended automatically as the final fallback,
        so callers only pass their app-specific directories.

        Parameters
        ----------
        directories : list[Path]
            App-specific directories to search, in priority order.
        **kwargs
            Additional arguments for the StaticFiles base class.
        """
        self.directories = [*directories, PYHX_STATIC_DIR]
        super().__init__(**kwargs)

    def lookup_path(self, path: str) -> tuple[str, os.stat_result | None]:
        """
        Look up a file path across all configured directories.

        Searches each directory in order and returns the first match.
        This enables the fallback behavior where app files override defaults.

        Parameters
        ----------
        path : str
            The relative path to the requested file (e.g., "css/style.css").

        Returns
        -------
        tuple[str, os.stat_result | None]
            A tuple of (full_path, stat_result) if found, or ("", None) if
            the file doesn't exist in any directory.
        """
        for directory in self.directories:
            full_path = directory / path
            try:
                return str(full_path), full_path.stat()
            except (FileNotFoundError, OSError):
                continue
        return "", None
