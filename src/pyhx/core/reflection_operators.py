import inspect
import types
import typing
from collections.abc import Callable, Mapping
from inspect import Parameter, Signature
from typing import (
    Any,
    Union,
    get_args,
    get_origin,
)


def ensure_parameter_type_in_signature(
    func: Callable[..., Any],
    type: type,
    default_name: str,
) -> tuple[Signature, str, bool]:
    """
    Return the signature of *func*, the name of a parameter typed *type*, and
    a flag indicating whether the parameter had to be added.

    If *func* already declares a parameter annotated with *type*, the original
    signature is returned unchanged together with that parameter's name and
    ``False``. If no such parameter exists, a new ``POSITIONAL_OR_KEYWORD``
    parameter named *default_name* with annotation *type* is appended to the
    signature and the extended signature is returned together with
    *default_name* and ``True``.

    Parameters
    ----------
    func : Callable[..., Any]
        The callable whose signature is inspected.
    type : Type
        The parameter annotation to search for.
    default_name : str
        Name given to the synthetic parameter when the type is not found.

    Returns
    -------
    signature : inspect.Signature
        The original signature (if the type was found) or an extended one.
    param_name : str
        Name of the parameter that carries *type* in the returned signature.
    added : bool
        ``True`` if a new parameter was added, ``False`` if an existing
        parameter was reused.

    Examples
    --------
    >>> from fastapi import Request
    >>> async def render(request: Request) -> PageResponse: ...
    >>> sig, name, added = ensure_parameter_type_in_signature(render, Request, "request")
    >>> name, added
    ('request', False)

    >>> async def render_no_request() -> PageResponse: ...
    >>> sig, name, added = ensure_parameter_type_in_signature(render_no_request, Request, "request")
    >>> name, added
    ('request', True)
    >>> 'request' in sig.parameters
    True
    """
    sig = inspect.signature(func)

    for param_name, param in sig.parameters.items():
        if param.annotation is type:
            return sig, param_name, False

    new_param = Parameter(
        name=default_name,
        kind=Parameter.POSITIONAL_OR_KEYWORD,
        annotation=type,
    )
    extended_sig = sig.replace(parameters=[new_param, *sig.parameters.values()])
    return extended_sig, default_name, True


def _unwrap_optional(annotation: Any) -> Any:
    # Optional[X] / Union[X, None] / X | None  ->  X. Other unions unchanged.
    is_union = get_origin(annotation) is Union or isinstance(
        annotation, types.UnionType
    )
    if not is_union:
        return annotation
    non_none = [a for a in get_args(annotation) if a is not type(None)]
    return non_none[0] if len(non_none) == 1 else annotation


def inject_parameters(
    func: Callable[..., Any],
    instances: Mapping[type[Any], Any],
) -> dict[str, Any]:
    """
    Build a ``{parameter_name: instance}`` kwargs dict for *func* by matching
    each parameter's type annotation against the keys of *instances*.

    The returned dict is safe to splat as ``**kwargs`` into *func*. Parameters
    that cannot be satisfied from *instances* are omitted, leaving the caller
    responsible for supplying the remaining arguments.

    Parameters
    ----------
    func : Callable[..., Any]
        The callable whose signature is inspected.
    instances : Mapping[Type[Any], Any]
        Mapping from a concrete type to an instance of that type. The function
        does not verify that values are instances of their keys.

    Returns
    -------
    Dict[str, Any]
        Mapping from parameter name to the instance selected for that
        parameter. Empty if no parameter matches.

    Matching rules
    --------------
    - Exact type identity in ``instances.keys()`` matches first.
    - If no exact match exists, a *single* subclass key
      (``issubclass(key, annotation)``) is accepted. Two or more subclass
      matches are treated as ambiguous and skipped.
    - ``Optional[X]`` and ``X | None`` annotations are unwrapped to ``X``
      before matching. Other parameterized generics (``List[X]``,
      ``Dict[K, V]``, multi-arg ``Union``, ``Any``, ...) are skipped.
    - String / forward-reference annotations (e.g. with
      ``from __future__ import annotations``) are resolved via
      :func:`typing.get_type_hints`. If resolution fails for the function as
      a whole, each parameter falls back to its raw annotation.
    - Only ``POSITIONAL_OR_KEYWORD`` and ``KEYWORD_ONLY`` parameters are
      considered; ``POSITIONAL_ONLY``, ``VAR_POSITIONAL`` and
      ``VAR_KEYWORD`` are skipped because they cannot be passed via
      ``**kwargs``.
    - Two parameters annotated with the same matched type both receive the
      same instance.
    - Non-runtime-checkable ``Protocol`` keys in *instances* do not cause
      errors; they are skipped during subclass scans.

    Examples
    --------
    >>> class Request: ...
    >>> class Session: ...
    >>> def handler(request: Request, session: Session) -> None: ...
    >>> req, sess = Request(), Session()
    >>> inject_parameters(handler, {Request: req, Session: sess})
    {'request': <...Request...>, 'session': <...Session...>}
    """
    sig = inspect.signature(func)
    try:
        hints = typing.get_type_hints(func, include_extras=False)
    except Exception:  # noqa: BLE001 — get_type_hints raises many types; fall back
        hints = {}

    result: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if param.kind not in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY):
            continue

        raw = hints.get(name, param.annotation)
        if raw is Parameter.empty:
            continue

        annotation = _unwrap_optional(raw)
        if not isinstance(annotation, type):
            continue  # Any, ParamSpec, unresolved ForwardRef, bare generic, etc.

        if annotation in instances:
            result[name] = instances[annotation]
            continue

        matches: list[type] = []
        for key in instances:
            if not isinstance(key, type):
                continue
            try:
                if issubclass(key, annotation):
                    matches.append(key)
            except TypeError:
                continue  # non-runtime-checkable Protocol, etc.
        if len(matches) == 1:
            result[name] = instances[matches[0]]

    return result
