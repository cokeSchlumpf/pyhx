"""Taglist demo page."""

from functools import partial

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from pyhx.core import WebAppRouter
from pyhx.components.view_model import Option
from samples.components._snippets import snippets

src = snippets(__file__)


# docs:start known_tags
KNOWN_TAGS: list[Option] = [
    Option(label="Bug", value="bug"),
    Option(label="Feature", value="feature"),
    Option(label="Documentation", value="docs"),
    Option(label="Performance", value="performance"),
    Option(label="Security", value="security"),
    Option(label="Refactor", value="refactor"),
    Option(label="Testing", value="testing"),
    Option(label="Accessibility", value="a11y"),
    Option(label="Design", value="design"),
    Option(label="Infrastructure", value="infra"),
]
# docs:end known_tags


router = WebAppRouter()


@router.page("/taglist", title="Taglist")
async def taglist_page() -> y.Node:
    return c.container(
        y.article[
            y.h1["Taglist"],
            y.p[
                "Free-text tag input composed from existing primitives: a ",
                y.code["pill.container"],
                " of removable ",
                y.code["pill"],
                "s plus a text input for entering new tags. As the user ",
                "types, matching entries from ",
                y.code["known_values"],
                " surface as suggestions; the user can also commit ",
                "arbitrary new strings.",
            ],
            y.h2["Empty"],
            y.p[
                "No ",
                y.code["initial_tags"],
                " — starts with an empty pill list.",
            ],
            c.example(
                # docs:start empty
                y.div(style="margin-block: 1rem;")[
                    c.taglist(name="tags-empty", known_values=KNOWN_TAGS),
                ],
                # docs:end empty
                code=[
                    ("code", src.text("empty"), "python"),
                    ("imports", src.text("imports"), "python"),
                ],
            ),
            y.h2["Pre-filled"],
            y.p[
                "Passing ",
                y.code["initial_tags"],
                " seeds the taglist with existing pills on first render.",
            ],
            c.example(
                # docs:start prefilled
                y.div(style="margin-block: 1rem;")[
                    c.taglist(
                        name="tags-prefilled",
                        known_values=KNOWN_TAGS,
                        initial_tags=[
                            Option(label="Bug", value="bug"),
                            Option(label="Performance", value="performance"),
                        ],
                    ),
                ],
                # docs:end prefilled
                code=[("code", src.text("prefilled"), "python")],
            ),
            y.h2["With value (from known_values)"],
            y.p[
                "Passing ",
                y.code["value"],
                " as a list of ",
                y.code["Option"],
                " renders the current selection as pills next to the ",
                "input. Use this when the selection is bound to known ",
                "values with stable identifiers.",
            ],
            c.example(
                # docs:start value_known
                y.div(style="margin-block: 1rem;")[
                    c.taglist(
                        name="tags-known",
                        known_values=KNOWN_TAGS,
                        value=[
                            Option(label="Bug", value="bug"),
                            Option(label="Security", value="security"),
                            Option(label="Testing", value="testing"),
                        ],
                    ),
                ],
                # docs:end value_known
                code=[("code", src.text("value_known"), "python")],
            ),
            y.h2["With value (mixed strings + Options)"],
            y.p[
                y.code["value"],
                " also accepts plain strings for free-text tags that ",
                "aren't part of ",
                y.code["known_values"],
                " — the component normalises them via ",
                y.code["Option.of(...)"],
                ". Useful when the data stores ad-hoc user-typed tags ",
                "alongside the curated pool.",
            ],
            c.example(
                # docs:start value_mixed
                y.div(style="margin-block: 1rem;")[
                    c.taglist(
                        name="tags-mixed",
                        known_values=KNOWN_TAGS,
                        value=[
                            Option(label="Feature", value="feature"),
                            "experimental",
                            "client-XYZ",
                            Option(label="Documentation", value="docs"),
                        ],
                    ),
                ],
                # docs:end value_mixed
                code=[("code", src.text("value_mixed"), "python")],
            ),
            y.h2["Closed list (allow_new_tags=False)"],
            y.p[
                "When ",
                y.code["allow_new_tags=False"],
                ", the Enter-commits-typed-text path is disabled — the ",
                "user can only add tags by clicking suggestions. The ",
                "selection is restricted to ",
                y.code["known_values"],
                ".",
            ],
            y.p[
                "Best practice in this mode: pass the full pool as ",
                y.code["initial_tags"],
                " so every allowed tag is visible on first focus, without ",
                "the user having to type to surface it. Typing then filters ",
                "this same set down. Otherwise the user is stuck guessing ",
                "what they're allowed to type, with no Enter escape hatch.",
            ],
            c.example(
                # docs:start closed
                y.div(style="margin-block: 1rem;")[
                    c.taglist(
                        name="tags-closed",
                        known_values=KNOWN_TAGS,
                        initial_tags=KNOWN_TAGS,
                        allow_new_tags=False,
                        suggestions_label="Available Tags",
                    ),
                ],
                # docs:end closed
                code=[("code", src.text("closed"), "python")],
            ),
            y.h2["Inside a form_field"],
            y.p[
                y.code["c.taglist"],
                " plugs into ",
                y.code["c.form_field"],
                " via ",
                y.code["functools.partial"],
                " — same pattern as ",
                y.code["dropdown_checkbox"],
                ". The partial pre-binds ",
                y.code["known_values"],
                " (and any other render-time options) so the result conforms ",
                "to the ",
                y.code["InputFactory"],
                " protocol (kwargs-only at call time). ",
                y.code["c.form_field"],
                " then forwards ",
                y.code["name"],
                ", ",
                y.code["disabled"],
                ", ",
                y.code["value"],
                ", ",
                y.code["aria_invalid"],
                ", and any other ",
                y.code["**kwargs"],
                " automatically — the taglist visually reflects the disabled ",
                "and error/success states.",
            ],
            y.p[
                "Uncomment ",
                y.code["error_text"],
                " in the source to see the search input turn red; ",
                "uncomment ",
                y.code["disabled=True"],
                " to see the whole taglist dim and stop accepting input ",
                "(and the per-tag hidden inputs stop submitting).",
            ],
            c.example(
                # docs:start form_field_demo
                y.div(style="margin-block: 1rem;")[
                    c.form_field(
                        "tags-form",
                        "Tags",
                        partial(
                            c.taglist,
                            known_values=KNOWN_TAGS,
                            initial_tags=KNOWN_TAGS,
                        ),
                        value=[Option(label="Bug", value="bug")],
                        help_text="Type to search the pool or commit free text with Enter.",
                        required=True,
                        # error_text="At least one tag is required",
                        # disabled=True,
                    ),
                ],
                # docs:end form_field_demo
                code=[("code", src.text("form_field_demo"), "python")],
            ),
            y.h2["Known values"],
            y.p[
                "The pool of suggestions passed to the component on this ",
                "page — typing any substring of these labels (e.g. ",
                y.code["bug"],
                ", ",
                y.code["doc"],
                ", ",
                y.code["a11"],
                ") should match.",
            ],
            c.code([("code", src.text("known_tags"), "python")]),
        ]
    )
