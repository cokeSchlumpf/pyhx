"""Type-safe builder for htmx attributes.

Spread the result of :func:`htmx` into an htpy element to get htmx
behaviour with IDE autocomplete and type-checked attribute names::

    y.button(**htmx(hx_get="/api/items", hx_target="#list", hx_swap="outerHTML"))[
        "Refresh"
    ]

Only kwargs you pass non-``None`` values for end up in the resulting dict.
``bool`` values are stringified to ``"true"`` / ``"false"``; ``dict`` values
are JSON-encoded; everything else is passed through as-is.

For attributes not covered here (or attributes added in future htmx
versions), add them directly to the element — both styles compose::

    y.button(**htmx(hx_get="/foo"), hx_ext="json-enc")["Save"]

Full attribute reference: https://htmx.org/reference/#attributes
"""

import json
from typing import Any, Literal, TypedDict, cast, overload

HxSwap = Literal[
    "innerHTML",
    "outerHTML",
    "textContent",
    "beforebegin",
    "afterbegin",
    "beforeend",
    "afterend",
    "delete",
    "none",
]
"""Base ``hx-swap`` values. Modifiers (``show:top``, ``scroll:bottom``,
``settle:200ms``, etc.) can be appended in a plain ``str`` —
e.g. ``hx_swap="outerHTML show:top"``."""


class HtmxAttrs(TypedDict, total=False):
    """Default return type of :func:`htmx`.

    Every key is optional (``total=False``) because :func:`htmx` only
    includes the attributes the caller actually passes. Values are strings
    — booleans and dicts get coerced before they land here.

    Returning a ``TypedDict`` (rather than plain ``dict[str, str]``) keeps
    Pyright/Pylance honest at call sites that mix htmx attributes with
    other typed kwargs::

        button(appearance="primary", **htmx(hx_post="/save"))

    Pyright enumerates the spread keys against the receiver's named
    parameters. Because ``HtmxAttrs`` constrains the key set to
    ``hx_*`` only, none of the spread keys collide with ``appearance``,
    ``variant``, etc., so they all flow into the receiver's ``**kwargs``
    cleanly.

    When the receiver is an htpy element (signature ``**kwargs: Attribute``
    with no named params), Pyright widens TypedDict spread to
    ``dict[str, object]`` and rejects it against ``Attribute``. For that
    case call :func:`htmx` with ``as_dict=True`` to get a plain
    ``dict[str, str]`` instead::

        y.div(**htmx(hx_get="/poll", as_dict=True))
    """

    hx_get: str
    hx_post: str
    hx_put: str
    hx_patch: str
    hx_delete: str
    hx_target: str
    hx_swap: str
    hx_swap_oob: str
    hx_select: str
    hx_select_oob: str
    hx_trigger: str
    hx_vals: str
    hx_include: str
    hx_params: str
    hx_headers: str
    hx_encoding: str
    hx_indicator: str
    hx_disabled_elt: str
    hx_confirm: str
    hx_prompt: str
    hx_sync: str
    hx_validate: str
    hx_push_url: str
    hx_replace_url: str
    hx_history: str
    hx_history_elt: str
    hx_boost: str
    hx_ext: str
    hx_disinherit: str
    hx_inherit: str


@overload
def htmx(
    *,
    as_dict: Literal[True],
    hx_get: str | None = None,
    hx_post: str | None = None,
    hx_put: str | None = None,
    hx_patch: str | None = None,
    hx_delete: str | None = None,
    hx_target: str | None = None,
    hx_swap: HxSwap | str | None = None,
    hx_swap_oob: str | bool | None = None,
    hx_select: str | None = None,
    hx_select_oob: str | None = None,
    hx_trigger: str | None = None,
    hx_vals: str | dict[str, Any] | None = None,
    hx_include: str | None = None,
    hx_params: str | None = None,
    hx_headers: str | dict[str, str] | None = None,
    hx_encoding: Literal["multipart/form-data"] | None = None,
    hx_indicator: str | None = None,
    hx_disabled_elt: str | None = None,
    hx_confirm: str | None = None,
    hx_prompt: str | None = None,
    hx_sync: str | None = None,
    hx_validate: bool | None = None,
    hx_push_url: bool | str | None = None,
    hx_replace_url: bool | str | None = None,
    hx_history: Literal[False] | None = None,
    hx_history_elt: bool | None = None,
    hx_boost: bool | None = None,
    hx_ext: str | None = None,
    hx_disinherit: str | None = None,
    hx_inherit: str | None = None,
) -> dict[str, str]: ...


@overload
def htmx(
    *,
    as_dict: Literal[False] = False,
    hx_get: str | None = None,
    hx_post: str | None = None,
    hx_put: str | None = None,
    hx_patch: str | None = None,
    hx_delete: str | None = None,
    hx_target: str | None = None,
    hx_swap: HxSwap | str | None = None,
    hx_swap_oob: str | bool | None = None,
    hx_select: str | None = None,
    hx_select_oob: str | None = None,
    hx_trigger: str | None = None,
    hx_vals: str | dict[str, Any] | None = None,
    hx_include: str | None = None,
    hx_params: str | None = None,
    hx_headers: str | dict[str, str] | None = None,
    hx_encoding: Literal["multipart/form-data"] | None = None,
    hx_indicator: str | None = None,
    hx_disabled_elt: str | None = None,
    hx_confirm: str | None = None,
    hx_prompt: str | None = None,
    hx_sync: str | None = None,
    hx_validate: bool | None = None,
    hx_push_url: bool | str | None = None,
    hx_replace_url: bool | str | None = None,
    hx_history: Literal[False] | None = None,
    hx_history_elt: bool | None = None,
    hx_boost: bool | None = None,
    hx_ext: str | None = None,
    hx_disinherit: str | None = None,
    hx_inherit: str | None = None,
) -> HtmxAttrs: ...


def htmx(
    *,
    as_dict: bool = False,
    # --- HTTP verbs: the request URL ---
    hx_get: str | None = None,
    hx_post: str | None = None,
    hx_put: str | None = None,
    hx_patch: str | None = None,
    hx_delete: str | None = None,
    # --- Targeting ---
    hx_target: str | None = None,
    hx_swap: HxSwap | str | None = None,
    hx_swap_oob: str | bool | None = None,
    hx_select: str | None = None,
    hx_select_oob: str | None = None,
    # --- Trigger ---
    hx_trigger: str | None = None,
    # --- Request payload / behaviour ---
    hx_vals: str | dict[str, Any] | None = None,
    hx_include: str | None = None,
    hx_params: str | None = None,
    hx_headers: str | dict[str, str] | None = None,
    hx_encoding: Literal["multipart/form-data"] | None = None,
    # --- UI feedback ---
    hx_indicator: str | None = None,
    hx_disabled_elt: str | None = None,
    hx_confirm: str | None = None,
    hx_prompt: str | None = None,
    # --- Sync / validation ---
    hx_sync: str | None = None,
    hx_validate: bool | None = None,
    # --- History ---
    hx_push_url: bool | str | None = None,
    hx_replace_url: bool | str | None = None,
    hx_history: Literal[False] | None = None,
    hx_history_elt: bool | None = None,
    # --- Boost / inheritance / extensions ---
    hx_boost: bool | None = None,
    hx_ext: str | None = None,
    hx_disinherit: str | None = None,
    hx_inherit: str | None = None,
) -> HtmxAttrs | dict[str, str]:
    """Build a dict of htmx attributes for spreading into an htpy element.

    Parameters
    ----------
    as_dict : bool, default False
        When ``False`` (default), return an :class:`HtmxAttrs` ``TypedDict``
        — preferred for spreading into functions that declare named
        parameters (custom components, our own ``button``, etc.), because
        Pyright keeps the per-key types and routes only ``hx_*`` keys to
        ``**kwargs``. When ``True``, return a plain ``dict[str, str]``
        — needed for spreading directly into htpy elements
        (``y.div``, ``y.button``, …) whose ``**kwargs: Attribute``
        receiver would otherwise reject the widened TypedDict spread.
    hx_get, hx_post, hx_put, hx_patch, hx_delete : str, optional
        URL that the element issues a request against on its trigger.
        At most one HTTP verb should be set per element.
    hx_target : str, optional
        CSS selector identifying which element should be updated with the
        response. Accepts htmx extended selectors (``this``, ``closest …``,
        ``find …``, ``next``, ``previous``).
    hx_swap : HxSwap or str, optional
        How the response replaces the target. Common values are surfaced as
        :data:`HxSwap`; a plain ``str`` can supply modifiers such as
        ``"outerHTML show:top"``.
    hx_swap_oob : str or bool, optional
        Marks the response as an out-of-band swap (used on response
        fragments, not on the triggering element).
    hx_select : str, optional
        CSS selector applied to the response to pick a subset before it is
        swapped.
    hx_select_oob : str, optional
        Same as ``hx_select`` but for out-of-band fragments.
    hx_trigger : str, optional
        Event(s) that issue the request. Supports htmx's trigger DSL —
        e.g. ``"click"``, ``"every 2s"``, ``"keyup changed delay:500ms"``.
    hx_vals : str or dict, optional
        Additional values sent with the request. A ``dict`` is JSON-encoded
        for you.
    hx_include : str, optional
        CSS selector for extra elements whose values should be included.
    hx_params : str, optional
        Filter the parameters sent — e.g. ``"*"``, ``"none"``,
        ``"not foo,bar"``.
    hx_headers : str or dict, optional
        Custom request headers. A ``dict`` is JSON-encoded for you.
    hx_encoding : "multipart/form-data", optional
        Override the request encoding (needed for file uploads).
    hx_indicator : str, optional
        CSS selector of the loading indicator to toggle during the request.
    hx_disabled_elt : str, optional
        CSS selector of element(s) to disable during the request.
    hx_confirm : str, optional
        Message shown in a confirm dialog before the request fires.
    hx_prompt : str, optional
        Message shown in a prompt; the user's response is sent in the
        ``HX-Prompt`` header.
    hx_sync : str, optional
        Synchronisation strategy — e.g. ``"closest form:abort"``.
    hx_validate : bool, optional
        Force HTML5 form validation before the request.
    hx_push_url : bool or str, optional
        Push a URL onto history. ``True`` pushes the request URL;
        a ``str`` pushes that exact URL; ``False`` disables pushing.
    hx_replace_url : bool or str, optional
        Like ``hx_push_url`` but uses ``history.replaceState``.
    hx_history : False, optional
        Pass ``False`` to mark the page as not stored in the history cache
        (useful for sensitive pages). The only valid value besides absence.
    hx_history_elt : bool, optional
        Marks the element as the root for history snapshots.
    hx_boost : bool, optional
        Progressively enhance descendant ``<a>`` / ``<form>`` so they issue
        AJAX requests with history support.
    hx_ext : str, optional
        Enable one or more htmx extensions — comma-separated.
    hx_disinherit : str, optional
        Names of inherited htmx attributes to ignore on this element /
        subtree.
    hx_inherit : str, optional
        Names of htmx attributes that descendants should explicitly
        inherit (when extensions disable default inheritance).

    Returns
    -------
    HtmxAttrs or dict[str, str]
        Mapping of ``hx_*`` keys to their string-coerced values. Only kwargs
        explicitly set to a non-``None`` value appear in the result. Concrete
        type depends on ``as_dict`` — see Parameters. htpy converts the
        underscores to hyphens when rendering.

    Examples
    --------
    >>> button(**htmx(hx_get="/items", hx_target="#list"))["Load"]
    >>> y.div(**htmx(hx_get="/poll", hx_trigger="every 2s", as_dict=True))[…]
    """
    raw: dict[str, Any] = {
        "hx_get": hx_get,
        "hx_post": hx_post,
        "hx_put": hx_put,
        "hx_patch": hx_patch,
        "hx_delete": hx_delete,
        "hx_target": hx_target,
        "hx_swap": hx_swap,
        "hx_swap_oob": hx_swap_oob,
        "hx_select": hx_select,
        "hx_select_oob": hx_select_oob,
        "hx_trigger": hx_trigger,
        "hx_vals": hx_vals,
        "hx_include": hx_include,
        "hx_params": hx_params,
        "hx_headers": hx_headers,
        "hx_encoding": hx_encoding,
        "hx_indicator": hx_indicator,
        "hx_disabled_elt": hx_disabled_elt,
        "hx_confirm": hx_confirm,
        "hx_prompt": hx_prompt,
        "hx_sync": hx_sync,
        "hx_validate": hx_validate,
        "hx_push_url": hx_push_url,
        "hx_replace_url": hx_replace_url,
        "hx_history": hx_history,
        "hx_history_elt": hx_history_elt,
        "hx_boost": hx_boost,
        "hx_ext": hx_ext,
        "hx_disinherit": hx_disinherit,
        "hx_inherit": hx_inherit,
    }

    result = {key: _stringify(value) for key, value in raw.items() if value is not None}
    if as_dict:
        return result
    # The dict-comprehension above narrows to dict[str, str]; reassure the type
    # checker that the keys are the TypedDict's known set.
    return cast(HtmxAttrs, result)


def _stringify(value: Any) -> str:
    """Coerce a Python value into the string htmx expects."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)
