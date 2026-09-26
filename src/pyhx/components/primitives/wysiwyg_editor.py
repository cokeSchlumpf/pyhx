from typing import Any

import htpy as y
import nh3
from markupsafe import Markup

from pyhx.core import component
from pyhx.core.primitives import classnames, htmx
from pyhx.core.primitives.icon_name import IconName

from .button import button

DEFAULT_COMMANDS = ("bold", "italic", "underline", "insertUnorderedList")


_COMMAND_ICONS: dict[str, IconName] = {
    "bold": "bold",
    "italic": "italic",
    "underline": "underline",
    "insertUnorderedList": "list",
}


_COMMAND_TITLES = {
    "bold": "Bold",
    "italic": "Italic",
    "underline": "Underline",
    "insertUnorderedList": "Bullet list",
}


ALLOWED_DESCRIPTION_TAGS = {
    "b",
    "strong",
    "i",
    "em",
    "u",
    "p",
    "div",
    "br",
    "ul",
    "ol",
    "li",
}


ALLOWED_DESCRIPTION_ATTRIBUTES: dict[str, set[str]] = {}


def sanitize_wysiwyg_html(value: str | None) -> str:
    """Sanitize editor HTML before rendering it back into the page."""
    return nh3.clean(
        value or "",
        tags=ALLOWED_DESCRIPTION_TAGS,
        attributes=ALLOWED_DESCRIPTION_ATTRIBUTES,
    )


@component
def wysiwyg_editor(
    *,
    name: str,
    value: str = "",
    id: str | None = None,
    commands: tuple[str, ...] = DEFAULT_COMMANDS,
    hx_post: str | None = None,
    hx_include: str | None = None,
    hx_target: str | None = None,
    hx_swap: str = "outerHTML",
    hx_vals: dict[str, Any] | None = None,
    min_height: str = "120px",
    **kwargs,
) -> y.Node:
    """Reusable lightweight WYSIWYG editor.

    Renders a toolbar, a contenteditable editor area, and a hidden input
    carrying the sanitized HTML value for normal form submission.
    """
    editor_id = id or name.replace("_", "-")
    safe_value = sanitize_wysiwyg_html(value)

    toolbar_buttons = [
        button(
            icon=_COMMAND_ICONS.get(command, "edit"),
            aria_label=_COMMAND_TITLES.get(command, command),
            title=_COMMAND_TITLES.get(command, command),
            type="button",
            appearance="neutral",
            variant="ghost",
            size="sm",
            data_wysiwyg_command=command,
            class_="hx-wysiwyg-editor__toolbar-button",
        )
        for command in commands
    ]

    hidden_attrs: dict[str, Any] = {
        "type": "hidden",
        "name": name,
        "id": f"{editor_id}__input",
        "value": safe_value,
        "data_wysiwyg_hidden": True,
    }

    if hx_post:
        hidden_attrs.update(
            htmx(
                hx_post=hx_post,
                hx_trigger="wysiwyg-refresh",
                hx_swap=hx_swap,
                as_dict=True,
            )
        )

    if hx_include:
        hidden_attrs["hx_include"] = hx_include

    if hx_target:
        hidden_attrs["hx_target"] = hx_target

    if hx_vals:
        hidden_attrs["hx_vals"] = hx_vals

    return y.div(
        id=editor_id,
        data_wysiwyg_editor=True,
        data_last_value=safe_value,
        **classnames("hx-wysiwyg-editor", **kwargs),
    )[
        y.div(class_="hx-wysiwyg-editor__toolbar")[toolbar_buttons],
        y.div(
            id=f"{editor_id}__content",
            contenteditable="true",
            role="textbox",
            aria_multiline="true",
            class_="hx-wysiwyg-editor__input",
            style=f"min-height: {min_height};",
            data_wysiwyg_input=True,
        )[Markup(safe_value)],
        y.input(**hidden_attrs),
    ]
