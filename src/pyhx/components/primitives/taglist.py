import json
from collections.abc import Sequence
from typing import Annotated

import htpy as y
from fastapi import Form
from pydantic import BaseModel

from pyhx.core import component
from pyhx.core.primitives import classnames, htmx

from ..view_model import Option
from .pill import pill

DROPDOWN_CLASSNAME = "hx-taglist__dropdown"


class TaglistState(BaseModel):
    """Full state of a taglist component, serialised into a name-less hidden
    input on the DOM. Every component-internal htmx request reads this blob
    from the DOM at request time (via JS in hx-vals) and reconstitutes a
    typed object server-side. Mutations are persisted by OOB-swapping the
    state-holder input with an updated value."""

    name: str
    # Input pools are immutable choice sets — canonical tuple. `selected` is
    # mutable working state (appended to / rebuilt on add/delete), so it stays
    # a list.
    known_values: tuple[Option, ...] = ()
    initial_tags: tuple[Option, ...] = ()
    selected: list[Option] = []
    allow_new_tags: bool = True
    suggestions_label: str = "Suggested Tags"
    disabled: bool = False


def _state_js(name: str) -> str:
    """JS expression: this taglist's state-holder input value, looked up by
    name-scoped selector. Used in hx-vals everywhere instead of going via
    `event.target` (which is `undefined` for delayed triggers like
    `input delay:200ms`)."""
    return f"document.querySelector('input[data-taglist-state={name}]').value"


def _query_js(name: str) -> str:
    """JS expression: this taglist's search input value, looked up by
    name-scoped selector (same reason as _state_js)."""
    return f"document.querySelector('[data-taglist-search={name}]').value"


class _Taglist:
    def __call__(
        self,
        name: str,
        known_values: Sequence[Option],
        initial_tags: Sequence[Option] | None = None,
        value: Sequence[str | Option] | None = None,
        allow_new_tags: bool = True,
        suggestions_label: str = "Suggested Tags",
        disabled: bool = False,
        **kwargs,
    ) -> y.Node:
        selected = self._dedupe([self._coerce(v) for v in (value or [])])
        state = TaglistState(
            name=name,
            known_values=tuple(known_values),
            initial_tags=tuple(initial_tags or ()),
            selected=selected,
            allow_new_tags=allow_new_tags,
            suggestions_label=suggestions_label,
            disabled=disabled,
        )
        filtered_initial = self._filter_unselected(state.initial_tags, state.selected)

        wrapper_attrs: dict = classnames("hx-taglist", **kwargs)
        wrapper_attrs["data_taglist_name"] = name
        if disabled:
            wrapper_attrs["aria_disabled"] = "true"

        return y.div(
            **wrapper_attrs,
            # Refocus the search input after any taglist-internal htmx
            # request completes. Lives on the wrapper (which survives all
            # swaps) so delete (which removes its own triggering button)
            # can still restore focus.
            **{
                "hx-on:htmx:after-request": (
                    "this.querySelector('[data-taglist-search]').focus()"
                )
            },
            **htmx(
                hx_post=suggested_tags.url(),
                hx_trigger=(
                    "input[!!event.target.hasAttribute('data-taglist-search')] delay:200ms"
                ),
                hx_target=f".{DROPDOWN_CLASSNAME}[data-taglist-name='{name}']",
                hx_swap="outerHTML",
                hx_ext="morph",
                hx_swap_oob="morph",
                hx_vals=(f"js:{{state: {_state_js(name)}, query: {_query_js(name)}}}"),
                as_dict=True,
            ),
        )[
            self.state_holder(state),
            self.search_input(state),
            self.suggestions(name, values=filtered_initial, label=suggestions_label),
            self.values(name, state.selected),
        ]

    def search_input(self, state: TaglistState, oob: bool = False) -> y.Node:
        """Render the search input. When `state.allow_new_tags` is True,
        pressing Enter commits the current input value as a new tag (the
        same code path as clicking an Add button on a suggestion). When
        False, no Enter handler is attached — the user can only add tags
        by clicking suggestions. `oob=True` adds the swap attribute so the
        OOB-emitted input replaces the existing one on the page."""
        attrs: dict = {
            "type": "text",
            "data_taglist_search": state.name,
            # Suppress the browser's native autocomplete dropdown so it
            # doesn't compete with our suggestions UI.
            "autocomplete": "off",
            "disabled": state.disabled,
        }
        if state.allow_new_tags:
            attrs.update(
                htmx(
                    hx_post=add_tag.url(),
                    hx_trigger="keydown[key=='Enter']",
                    hx_target=f".hx-taglist__value[data-taglist-name='{state.name}']",
                    hx_swap="beforeend",
                    hx_vals=(
                        f"js:{{"
                        f"state: {_state_js(state.name)}, "
                        f"label: {_query_js(state.name)}, "
                        f"value: {_query_js(state.name)}"
                        f"}}"
                    ),
                    as_dict=True,
                )
            )
            # Prevent default Enter behaviour (form submission when the
            # taglist sits inside a <form>).
            attrs["onkeydown"] = "if (event.key === 'Enter') event.preventDefault();"
        if oob:
            attrs["hx_swap_oob"] = (
                f"outerHTML:input[data-taglist-search='{state.name}']"
            )
            # htmx 2 honours `autofocus` on swapped-in elements — refocus
            # the (now-empty) input after add/Enter so the user can keep
            # typing without re-clicking.
            attrs["autofocus"] = True
        return y.input(**attrs)

    def state_holder(self, state: TaglistState, oob: bool = False) -> y.Node:
        """Render the name-less hidden input that carries the full component
        state as serialised JSON. `oob=True` adds the hx-swap-oob attribute
        so this element replaces the existing state holder on the page when
        returned from a fragment endpoint."""
        attrs: dict = {
            "type": "hidden",
            "data_taglist_state": state.name,
            "value": state.model_dump_json(),
        }
        if oob:
            attrs["hx_swap_oob"] = f"outerHTML:input[data-taglist-state='{state.name}']"
        return y.input(**attrs)

    def suggestions(
        self,
        name: str,
        values: Sequence[Option] | None = None,
        label: str = "Suggested Tags",
        oob: bool = False,
    ) -> y.Node:
        values = values or []

        div_attrs: dict = {"class_": DROPDOWN_CLASSNAME, "data_taglist_name": name}
        if oob:
            div_attrs["hx_swap_oob"] = (
                f"outerHTML:.{DROPDOWN_CLASSNAME}[data-taglist-name='{name}']"
            )

        if not values:
            return y.div(**div_attrs)
        return y.div(**div_attrs)[
            y.small[label],
            pill.container(
                [
                    pill(
                        opt.label,
                        button=pill.button(
                            aria_label="Add tag",
                            icon="plus",
                            hx_post=add_tag.url(),
                            hx_vals=(
                                f"js:{{"
                                f"state: {_state_js(name)}, "
                                f"label: {json.dumps(opt.label)}, "
                                f"value: {json.dumps(opt.value)}"
                                f"}}"
                            ),
                            hx_target=f".hx-taglist__value[data-taglist-name='{name}']",
                            hx_swap="beforeend",
                            onmousedown="event.preventDefault()",
                        ),
                        appearance="success",
                    )
                    for opt in values
                ]
            ),
        ]

    def values(self, name: str, value: Sequence[Option | str]) -> y.Node:
        return pill.container(
            [self.value(name, v) for v in value],
            class_="hx-taglist__value",
            data_taglist_name=name,
        )

    def value(self, name: str, value: str | Option) -> y.Node:
        v = self._coerce(value)
        return y.span(data_taglist_name=name, data_taglist_value=v.value)[
            pill(
                v.label,
                button=pill.button(
                    aria_label="Remove tag",
                    tabindex="-1",
                    hx_post=delete_tag.url(),
                    hx_vals=(
                        f"js:{{state: {_state_js(name)}, value: {json.dumps(v.value)}}}"
                    ),
                    hx_target=f"closest span[data-taglist-name='{name}'][data-taglist-value='{v.value}']",
                    hx_swap="delete",
                ),
            ),
            # Never disabled: a disabled taglist still submits its tags — the
            # hidden input is the only carrier of the value, so disabling it
            # would drop the selection on save. The visible search input and
            # remove buttons stay disabled/inert instead.
            y.input(type="hidden", name=name, value=v.value),
        ]

    @staticmethod
    def _coerce(value: str | Option) -> Option:
        return value if isinstance(value, Option) else Option.of(value)

    @staticmethod
    def _dedupe(value: Sequence[Option]) -> list[Option]:
        """Treat the selection as a set: drop later occurrences while
        preserving order."""
        seen: set[str] = set()
        result: list[Option] = []
        for v in value:
            if v.value not in seen:
                seen.add(v.value)
                result.append(v)
        return result

    @staticmethod
    def _filter_unselected(
        pool: Sequence[Option], selected: Sequence[Option]
    ) -> list[Option]:
        selected_ids = {o.value for o in selected}
        return [o for o in pool if o.value not in selected_ids]


@component
def tags() -> y.Node:
    return y.fragment[""]


@tags.fragments.post("/suggestions")
async def suggested_tags(
    state: Annotated[str, Form()],
    query: Annotated[str, Form()] = "",
) -> y.Node:
    s = TaglistState.model_validate_json(state)
    selected_ids = {o.value for o in s.selected}

    if not query:
        matches = [o for o in s.initial_tags if o.value not in selected_ids]
    else:
        q = query.lower()
        matches = [
            o
            for o in s.known_values
            if q in o.label.lower() and o.value not in selected_ids
        ]

    return taglist.suggestions(s.name, values=matches, label=s.suggestions_label)


@tags.fragments.post("/tag")
async def add_tag(
    state: Annotated[str, Form()],
    label: Annotated[str, Form()],
    value: Annotated[str, Form()],
) -> y.Node:
    s = TaglistState.model_validate_json(state)
    selected_ids = {o.value for o in s.selected}
    is_duplicate = value in selected_ids

    if not is_duplicate:
        s.selected.append(Option(label=label, value=value))

    filtered_initial = taglist._filter_unselected(s.initial_tags, s.selected)

    return y.fragment[
        None
        if is_duplicate
        else taglist.value(s.name, Option(label=label, value=value)),
        taglist.suggestions(
            s.name, values=filtered_initial, label=s.suggestions_label, oob=True
        ),
        taglist.state_holder(s, oob=True),
        taglist.search_input(s, oob=True),
    ]


@tags.fragments.post("/tag/delete")
async def delete_tag(
    state: Annotated[str, Form()],
    value: Annotated[str, Form()],
) -> y.Node:
    s = TaglistState.model_validate_json(state)
    s.selected = [o for o in s.selected if o.value != value]
    # The chip itself is removed client-side via hx-swap="delete" on the
    # button. We only need to persist the updated state.
    return taglist.state_holder(s, oob=True)


taglist = _Taglist()
