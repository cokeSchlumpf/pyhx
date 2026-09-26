def classnames(classname: str | list[str] | dict[str, bool], **kwargs) -> dict:
    """Merge CSS class names into kwargs.

    Combines the provided class names with any existing `class_` in kwargs,
    returning a new dict with the merged classes in `class_`.

    Args:
        classname: CSS class name(s) to add. Can be:
            - A string: single class name
            - A list: multiple class names (all active)
            - A dict: class names mapped to boolean (only truthy values included)
        **kwargs: Additional attributes. If `class_` is present, its value
            is merged with the provided classnames.

    Returns:
        A copy of kwargs with `class_` set to the merged class string.

    Example:
        >>> cx("btn", class_="primary")
        {'class_': 'btn primary'}
        >>> cx({"active": True, "disabled": False})
        {'class_': 'active'}
    """
    if isinstance(classname, str):
        classname = [classname]

    if isinstance(classname, list):
        classname = {c: True for c in classname}

    classnames = str(kwargs.get("class_", "")).split()

    for name, active in classname.items():
        if active:
            classnames.append(name)

    kwargs["class_"] = " ".join(set(classnames))
    return kwargs
