"""Dev-mode detection.

Single source of truth for whether the framework is running in
development mode. Currently consulted by :class:`WebApp` when no
explicit ``is_dev`` value is passed; addons (e.g. the user-session
addon) can use it to gate dev-only behavior or quiet warnings that
are expected during development.

Detection order:

1. ``PYHX_DEBUG`` environment variable (explicit override; accepts
   ``1``/``true``/``yes`` or ``0``/``false``/``no``).
2. Command line contains ``dev`` or any arg with ``--reload``
   (e.g. ``fastapi dev`` / ``uvicorn --reload``).
"""

import os
import sys


def is_dev_mode() -> bool:
    """Return whether the app is running in development mode."""
    debug_env = os.environ.get("PYHX_DEBUG", "").lower()
    if debug_env in ("1", "true", "yes"):
        return True
    if debug_env in ("0", "false", "no"):
        return False

    for arg in sys.argv:
        if arg == "dev" or "--reload" in arg:
            return True

    return False


__all__ = ["is_dev_mode"]
