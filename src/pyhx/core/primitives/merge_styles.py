def merge_styles(style_dict: dict[str, str], **kwargs) -> dict:
    """Merge inline CSS styles into kwargs.

    Combines the provided property/value pairs with any existing ``style``
    attribute in kwargs, returning a new dict with the merged value in
    ``style``. Mirrors :func:`classnames` in shape — first positional is
    the data, ``**kwargs`` are the spread-target.

    The dict keys are used as CSS property names verbatim — write the
    standard hyphenated names (e.g. ``"background-color"``, ``"margin-top"``,
    ``"--my-var"`` for custom properties). When the same property appears
    in both an existing ``style`` string and the provided dict, the dict
    value wins: it's appended after the existing declarations, and browsers
    resolve duplicate declarations in a ``style`` attribute by taking the
    last one.

    Args:
        style_dict: dict mapping CSS property names to values.
        **kwargs: Additional attributes. If ``style`` is present, its value
            is preserved and the new declarations are appended.

    Returns:
        A copy of kwargs with ``style`` set to the merged inline-CSS string.

    Examples:
        >>> merge_styles({"background-color": "red"})
        {'style': 'background-color: red'}

        >>> merge_styles({"margin-top": "10px"}, style="color: blue;")
        {'style': 'color: blue; margin-top: 10px'}

        >>> merge_styles({"color": "red"}, style="color: blue")
        {'style': 'color: blue; color: red'}  # later wins → red applies
    """
    parts: list[str] = []

    existing = str(kwargs.get("style", "")).strip().rstrip(";").strip()
    if existing:
        parts.append(existing)

    if style_dict:
        parts.append(
            "; ".join(f"{prop}: {value}" for prop, value in style_dict.items())
        )

    kwargs["style"] = "; ".join(parts)
    return kwargs
