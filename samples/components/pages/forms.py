"""Forms demo page.

Walks through every :func:`form_field` shape — plain text inputs with the
help / error / success affordances, plus the dropdown and segment-control
primitives plugged in via :func:`functools.partial`. Closes with a short
explainer on *why* ``partial`` is the right adapter for multi-arg controls.
"""

# docs:start imports
import htpy as y
import pyhx.components as c
# docs:end imports

from datetime import date
from enum import Enum
from functools import partial
from pydantic import BaseModel, Field
from typing import Annotated, Literal

from pyhx.core import WebAppRouter
from pyhx.core.primitives import classnames, styles
from pyhx.components import annotations as a
from pyhx.components.view_model import Option
from samples.components._snippets import snippets

src = snippets(__file__)


PRIORITY_OPTIONS = (
    Option(label="Low",      value="low"),
    Option(label="Medium",   value="medium"),
    Option(label="High",     value="high"),
    Option(label="Critical", value="critical"),
)

TYPE_OPTIONS = [
    Option(label="Bug",      value="bug"),
    Option(label="Feature",  value="feature"),
    Option(label="Question", value="question"),
]

LABEL_OPTIONS = (
    Option(label="Backend",  value="backend"),
    Option(label="Frontend", value="frontend"),
    Option(label="Docs",     value="docs"),
    Option(label="Infra",    value="infra"),
)

# A deliberately long pool — the kind of list a drawer_select handles better
# than an inline checkbox fieldset or a multi-select dropdown.
COMPONENT_OPTIONS = (
    Option(label="API Gateway",   value="api-gateway"),
    Option(label="Authentication", value="auth"),
    Option(label="Billing",       value="billing"),
    Option(label="Caching",       value="caching"),
    Option(label="CLI",           value="cli"),
    Option(label="Database",      value="database"),
    Option(label="Email",         value="email"),
    Option(label="Frontend",      value="frontend"),
    Option(label="Logging",       value="logging"),
    Option(label="Metrics",       value="metrics"),
    Option(label="Notifications", value="notifications"),
    Option(label="Payments",      value="payments"),
    Option(label="Scheduler",     value="scheduler"),
    Option(label="Search",        value="search"),
    Option(label="Storage",       value="storage"),
    Option(label="Webhooks",      value="webhooks"),
)

# ----------------------------------------------------------
# Models used by the DataForm demos below
# ----------------------------------------------------------

# docs:start issue_report_model
@a.form(columns=2, submit_label="Create issue")
class IssueReport(BaseModel):
    """Decorated model — explicit ``@form`` + explicit field annotations."""

    title: Annotated[
        str,
        Field(min_length=5),
        a.TextField(
            control=a.InputControl(placeholder="Short summary"),
            help_text="The title of the issue.",
        ),
    ]

    issue_type: Annotated[
        Literal["bug", "feature", "question"],
        a.TextChoiceField(control=a.DropdownControl(options=tuple(TYPE_OPTIONS))),
    ] = "bug"

    description: Annotated[
        str,
        Field(min_length=10, max_length=160),
        a.TextField(
            control=a.TextareaControl(rows="4"),
            help_text="Write something nice. Max. 160 characters.",
        ),
    ]
# docs:end issue_report_model


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# docs:start preferences_model


@a.form(columns=2, submit_label="Save profile")
class ProfileCard(BaseModel):
    """Per-field row span — a tall ``bio`` cell beside two stacked inputs.

    ``rows=n`` adds a ``hx-grid-row-span-{n}`` class so the field occupies
    ``n`` rows of the grid (the column counterpart of ``columns=``); combine
    the two for a 2-D span. With the default auto-flow, ``bio`` (``rows=2``)
    takes the right column across both rows while ``display_name`` and
    ``location`` stack down the left column.
    """

    display_name: Annotated[str, a.TextField()]
    bio: Annotated[
        str,
        a.TextField(control=a.TextareaControl(rows="5"), rows=2),
    ]
    location: Annotated[str, a.TextField()]


@a.form(
    submit_label="Publish",
    template_areas=[
        "headline headline",
        "body     author",
        "body     tags",
    ],
    template_columns=["2fr", "1fr"],
)
class BlogPost(BaseModel):
    """Field-keyed CSS-Grid layout via ``template_areas``.

    Each field is placed by its **key**: ``headline`` spans the top row,
    ``body`` spans two rows down the wide left column, and ``author`` / ``tags``
    stack in the narrow right column. ``template_columns=["2fr", "1fr"]`` makes
    the body column twice as wide as the sidebar. With a template, per-field
    ``columns`` / ``rows`` are ignored — placement comes entirely from the grid.
    """

    headline: Annotated[
        str,
        a.TextField(control=a.InputControl(placeholder="Post title")),
    ]
    body: Annotated[str, a.TextField(control=a.TextareaControl(rows="8"))]
    author: Annotated[str, a.TextField()]
    tags: Annotated[list[str], a.TextListField(label="Tags")]

class UserPreferences(BaseModel):
    """Un-decorated model — every field uses the reader's auto-derived defaults.

    Demonstrates how ``DataForm`` picks sensible controls from the Python
    type alone (no ``Annotated[…]`` markers):

    * ``str``                              → text input
    * ``int``                              → number input
    * ``bool``                             → single checkbox
    * ``date``                             → date picker
    * ``Enum``                             → dropdown_radio (via the
                                             default :func:`to_choice_value`)
    * ``list[Literal[...]]``               → multi-select dropdown_checkbox
    """

    display_name: str = "Anonymous"
    follower_count: int = 0
    subscribed: bool = True
    severity: Severity = Severity.MEDIUM
    digest_day: Literal["monday", "wednesday", "friday"] = "monday"
    interests: list[Literal["news", "sports", "tech", "music"]] = Field(
        default_factory=lambda: ["news", "tech"]
    )
    joined_on: date = date(2026, 1, 1)
# docs:end preferences_model


# docs:start triage_model
@a.form(columns=1, submit_label="Save triage")
class IssueTriage(BaseModel):
    """Both drawer controls — multi-select and single-select — for long pools.

    ``DrawerSelectControl`` (multi) and ``DrawerRadioControl`` (single) open a
    filterable drawer instead of listing every option inline, which scales to
    long lists where a checkbox fieldset or a dropdown becomes unwieldy. Both
    are self-contained, so the fields show just their label — no help or error
    text.
    """

    summary: Annotated[
        str,
        a.TextField(control=a.InputControl(placeholder="Short summary")),
    ]
    components: Annotated[
        list[str],
        a.MultiselectChoiceField(
            label="Affected components",
            control=a.DrawerSelectControl(
                options=COMPONENT_OPTIONS,
                labels=c.DrawerSelectLabels(
                    value_column="Component",
                    select_items_button="Add components",
                    drawer_title="Select components",
                    query_label="Filter components",
                    available_items_column="All components",
                    selected_items_column="Selected components",
                    no_items_available="No components match your filter.",
                    no_items_selected="No components selected yet.",
                ),
            ),
        ),
    ] = Field(default_factory=lambda: ["auth", "frontend"])
    primary_component: Annotated[
        str,
        a.TextChoiceField(
            label="Primary component",
            control=a.DrawerRadioControl(
                options=COMPONENT_OPTIONS,
                labels=c.DrawerRadioLabels(
                    value_label="Component",
                    select_item_button="Choose component",
                    clear_item="Clear primary component",
                    drawer_title="Select primary component",
                    query_label="Filter components",
                    available_items_column="All components",
                    no_items_available="No components match your filter.",
                    no_item_selected="No primary component chosen yet.",
                ),
            ),
        ),
    ] = "auth"
# docs:end triage_model


# docs:start article_model
@a.form(columns=2, submit_label="Save article")
class ArticleDraft(BaseModel):
    """Mixed-span layout — title spans the full row, the textarea too.

    Demonstrates the per-field ``columns=`` parameter: each field that
    sets it gets a ``hx-grid-span-{n}`` class so it occupies more than a
    single cell of the enclosing ``hx-grid``.
    """

    title: Annotated[
        str,
        Field(min_length=3),
        a.TextField(
            control=a.InputControl(placeholder="Article title"),
            columns=2,
        ),
    ]
    author: Annotated[str, a.TextField()]
    published_on: Annotated[date, a.DateField()]
    summary: Annotated[
        str,
        a.TextField(control=a.TextareaControl(rows="3"), columns=2),
    ]
# docs:end article_model


class ContactRequest(BaseModel):
    """Plain model for the :class:`HeadlessForm` demo — no ``@a.form`` / no
    ``Annotated[…]`` markers.

    ``HeadlessForm`` never reads form annotations (the *layout* is hand-written
    by the caller), so a bare ``BaseModel`` with ordinary ``Field`` constraints
    is all it needs. Defaults of ``""`` let an empty form render and access
    every attribute directly, while the ``min_length`` / ``pattern`` rules make
    it invalid until filled — so the submit button starts disabled.
    """

    first_name: str = Field("", min_length=1)
    last_name: str = Field("", min_length=1)
    email: str = Field("", pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    message: str = Field("", min_length=10)


router = WebAppRouter()


def _success_banner(form_id: str, message: str) -> y.Node:
    """OOB-swap the entire form with a green success banner.

    The form was rendered with ``id=hx-data-form__<name>``; targeting the
    same id with ``hx-swap-oob="outerHTML"`` replaces it in place. Pick the
    swap style that fits the real submit handler — a redirect via the
    ``HX-Redirect`` response header (returned through the view's response
    headers, not the body) is the other common pattern.
    """
    return y.div(id=form_id, **{"hx-swap-oob": "outerHTML"})[
        y.article(class_="success")[
            y.h3["Saved"],
            y.p[message],
        ],
    ]


async def _handle_issue_submit(value: IssueReport) -> y.Node:
    return _success_banner(
        "hx-data-form__issue-report",
        f"Issue “{value.title}” ({value.issue_type}) created.",
    )


async def _handle_preferences_submit(value: UserPreferences) -> y.Node:
    return _success_banner(
        "hx-data-form__user-preferences",
        f"Preferences updated for {value.display_name}.",
    )


async def _handle_blank_issue_submit(value: IssueReport) -> y.Node:
    return _success_banner(
        "hx-data-form__blank-issue-report",
        f"New issue “{value.title}” filed.",
    )


async def _handle_drawer_issue_submit(value: IssueReport) -> y.Node:
    return _success_banner(
        "hx-data-form__drawer-issue-report",
        f"Drawer issue “{value.title}” saved.",
    )


# docs:start issue_form
_issue_form = c.DataForm[IssueReport](
    name="issue-report",
    routes=router,
    type=IssueReport,
    handle_submit=_handle_issue_submit,
)
# docs:end issue_form

# docs:start preferences_form
_preferences_form = c.DataForm[UserPreferences](
    name="user-preferences",
    routes=router,
    type=UserPreferences,
    handle_submit=_handle_preferences_submit,
)
# docs:end preferences_form


async def _handle_triage_submit(value: IssueTriage) -> y.Node:
    return _success_banner(
        "hx-data-form__issue-triage",
        f"Triaged “{value.summary}” → "
        f"{', '.join(value.components) or 'no components'} "
        f"(primary: {value.primary_component}).",
    )


# docs:start triage_form
_triage_form = c.DataForm[IssueTriage](
    name="issue-triage",
    routes=router,
    type=IssueTriage,
    handle_submit=_handle_triage_submit,
)
# docs:end triage_form


async def _handle_article_submit(value: ArticleDraft) -> y.Node:
    return _success_banner(
        "hx-data-form__article-draft",
        f"Article “{value.title}” saved.",
    )


# docs:start article_form
_article_form = c.DataForm[ArticleDraft](
    name="article-draft",
    routes=router,
    type=ArticleDraft,
    handle_submit=_handle_article_submit,
)

# docs:end article_form

async def _handle_profile_submit(value: ProfileCard) -> y.Node:
    return _success_banner(
        "hx-data-form__profile-card",
        f"Profile saved for {value.display_name}.",
    )


_profile_form = c.DataForm[ProfileCard](
    name="profile-card",
    routes=router,
    type=ProfileCard,
    handle_submit=_handle_profile_submit,
)


async def _handle_blog_submit(value: BlogPost) -> y.Node:
    return _success_banner(
        "hx-data-form__blog-post",
        f"Published “{value.headline}”.",
    )


_blog_form = c.DataForm[BlogPost](
    name="blog-post",
    routes=router,
    type=BlogPost,
    handle_submit=_handle_blog_submit,
)

# Same model as ``_issue_form``, but rendered below without an initial value
# to demonstrate the "new record" path: ``model_construct()`` produces an
# instance with required fields unset, the renderer auto-validates, and the
# resulting errors disable the submit button until the user fills the form.
_blank_issue_form = c.DataForm[IssueReport](
    name="blank-issue-report",
    routes=router,
    type=IssueReport,
    handle_submit=_handle_blank_issue_submit,
)

# Dedicated form instance for the drawer demo so its htmx fragment routes
# don't collide with the page-level ``_issue_form`` above.
_drawer_issue_form = c.DataForm[IssueReport](
    name="drawer-issue-report",
    routes=router,
    type=IssueReport,
    handle_submit=_handle_drawer_issue_submit,
)

# Triage form (drawer_select + drawer_radio) rendered inside a drawer. The
# pickers open in the popup drawer, stacked on top of this one, instead of
# replacing the form — its own fragment routes are kept separate from the
# page-level ``_triage_form``.
_drawer_triage_form = c.DataForm[IssueTriage](
    name="drawer-issue-triage",
    routes=router,
    type=IssueTriage,
    handle_submit=_handle_triage_submit,
)


# ----------------------------------------------------------
# HeadlessForm — same controller engine as DataForm, custom layout
# ----------------------------------------------------------


def _textarea(**kwargs) -> y.Node:
    """``form_field`` factory for a ``<textarea>``.

    A textarea has no ``value`` attribute — its text lives between the tags —
    so pull ``value`` out of the forwarded kwargs and render it as the child.
    Without this the content would be lost every time the form re-renders.
    """
    value = str(kwargs.pop("value", "") or "")
    return y.textarea(**kwargs)[value]


# docs:start contact_render
async def _render_contact_form(ctx: c.FormRenderContext[ContactRequest]) -> y.Node:
    """Hand-written layout for a :class:`HeadlessForm`.

    The controller (``ctx.form``) owns validation, touched-tracking and the
    HTMX submit/validate wiring; this callback only decides how the fields are
    arranged. It reaches for three helpers off ``ctx.form``:

    * ``form_attrs(oob=…)``     → the ``<form>`` HTMX wiring (submit endpoint).
    * ``validate_attrs(oob=…)`` → live-validate wiring for the field container.
    * ``touched_inputs(…)``     → hidden ``<input name="_touched">`` markers.

    Per field, ``ctx.visible_errors`` drives the inline error text (only for
    touched fields) while the full ``ctx.errors`` set gates the submit button.
    ``ctx.oob`` is threaded into the helpers so the *initial* render omits
    ``hx-swap-oob`` (it would otherwise be discarded when delivered inside
    another swap) and only the validate/submit re-renders morph in place.
    """
    v = ctx.value
    return y.form(id=ctx.form.wrapper_div_id, **ctx.form.form_attrs(oob=ctx.oob))[
        y.div(
            **styles("hx-grid"),
            style="--hx-grid-columns: 2",
            **ctx.form.validate_attrs(oob=ctx.oob),
        )[
            # First / last name share a row; email and message span both cells.
            c.form_field(
                "first_name",
                "First name",
                y.input,
                value=v.first_name,
                error_text=ctx.visible_errors.get("first_name"),
                disabled=ctx.disabled,
            ),
            c.form_field(
                "last_name",
                "Last name",
                y.input,
                value=v.last_name,
                error_text=ctx.visible_errors.get("last_name"),
                disabled=ctx.disabled,
            ),
            c.form_field(
                "email",
                "Email",
                y.input,
                type="email",
                value=v.email,
                placeholder="you@example.com",
                error_text=ctx.visible_errors.get("email"),
                disabled=ctx.disabled,
                class_="hx-grid-span-2",
            ),
            c.form_field(
                "message",
                "Message",
                _textarea,
                value=v.message,
                help_text="At least 10 characters.",
                error_text=ctx.visible_errors.get("message"),
                disabled=ctx.disabled,
                class_="hx-grid-span-2",
            ),
            *ctx.form.touched_inputs(ctx.touched),
        ],
        y.div(**styles("flex", "gap-sm", "justify-end", "mt-md"))[
            c.button("Reset", variant="outline", type="reset"),
            c.button(
                "Send message",
                appearance="primary",
                type="submit",
                disabled=ctx.disabled or bool(ctx.errors),
            ),
        ],
    ]
# docs:end contact_render


async def _handle_contact_submit(value: ContactRequest) -> y.Node:
    return _success_banner(
        "hx-headless-form__contact-request",
        f"Thanks {value.first_name} — we'll reply to {value.email}.",
    )


# docs:start contact_form
_contact_form = c.HeadlessForm[ContactRequest](
    name="contact-request",
    routes=router,
    type=ContactRequest,
    render=_render_contact_form,
    handle_submit=_handle_contact_submit,
)
# docs:end contact_form


# docs:start drawer_form_fragment
@router.fragment.get("/forms/drawer-form")
async def _drawer_form_fragment() -> y.Node:
    """Drawer-content fragment rendered when the trigger button is clicked.

    The form is rendered with ``actions=...`` to demonstrate the drawer-
    context layout: ``drawer.css`` flips the actions row to a vertical
    column with the submit pinned to the top via ``order: -1``, so the
    secondary buttons stack below the primary CTA.
    """
    return c.drawer_content(
        await _drawer_issue_form.render(
            value=IssueReport(
                title="Drawer-rendered issue",
                issue_type="feature",
                description="Edit this and click Save. Cancel closes the drawer.",
            ),
            actions=y.fragment[
                c.button("Cancel", variant="outline"),
                c.button("Save draft", variant="ghost"),
            ],
        ),
        title="Edit issue",
    )
# docs:end drawer_form_fragment


@router.fragment.get("/forms/drawer-triage-form")
async def _drawer_triage_fragment() -> y.Node:
    """Drawer-content fragment for a form that itself contains drawer pickers.

    The form's ``drawer_select`` / ``drawer_radio`` controls open the popup
    drawer, which stacks on top of this one — so picking components no longer
    replaces the form.
    """
    return c.drawer_content(
        await _drawer_triage_form.render(),
        title="Triage in drawer",
    )


@router.page("/forms", title="Forms")
async def forms_page() -> y.Node:
    return c.container(
        y.article[
            c.markdown("""
                # Forms

                The `form_field` primitive wraps a single input-like control with a label,
                optional help / error / success text, and the right ARIA wiring. The `input`
                parameter is any callable that takes `**kwargs` and returns an htpy node —
                typically `y.input`, but any of the dropdown or segment primitives can plug
                in via `functools.partial` (explained below).

                ## Generating a form from a Pydantic model

                `DataForm[T]` takes a Pydantic model and renders every field through the
                right primitive. Fields with an `Annotated[…]` marker (`a.TextField`,
                `a.TextChoiceField`, …) use that marker verbatim. Fields without one are
                auto-derived from the Python type by the annotations `reader`:

                - `str` → text input
                - `int` / `float` → number input
                - `bool` → single checkbox
                - `date` → date picker
                - `Literal` / `Enum` → choice dropdown
                - `list[Literal]` / `list[Enum]` → multi-select

                Layout and submit-button label come from the class-level `@a.form(...)`
                decorator (falling back to `FormConfig()` defaults when absent).

                ### Decorated model — explicit annotations

                `IssueReport` carries `@a.form(columns=2, …)` plus explicit `a.TextField` /
                `a.TextChoiceField` annotations on each field — the renderer uses them
                verbatim.
            """),
            await _issue_form.render(),
            c.code([
                ("model", src.text("issue_report_model"), "python"),
                ("form", src.text("issue_form"), "python"),
                ("imports", src.text("imports"), "python"),
            ]),

            c.markdown("""
                ### Un-decorated model — every control auto-derived

                `UserPreferences` has no `@a.form` decorator and no `Annotated[…]` markers.
                Each control below was derived purely from the Python type: the `Severity`
                enum becomes a dropdown (with the default `to_choice_value` unwrapping
                `.value`), the `list[Literal]` becomes a multi-select dropdown, the `date`
                becomes a date picker, etc. The submit button label and column count come
                from `FormConfig()`'s defaults (`"Save"`, 2 columns).
            """),
            await _preferences_form.render(),
            c.code([
                ("model", src.text("preferences_model"), "python"),
                ("form", src.text("preferences_form"), "python"),
            ]),

            c.markdown("""
                ### Choosing from a drawer — for long option pools

                When the option list is long enough that listing every choice
                inline would overwhelm the form, render it through a drawer
                control. A `MultiselectChoiceField` uses `DrawerSelectControl`
                (multi-select); a `TextChoiceField` uses `DrawerRadioControl`
                (single-select). The on-page control shows only the current
                selection; a button opens a filterable drawer. Both controls are
                self-contained, so each field renders with just its label (no help
                or error text), and their user-facing strings come from
                `DrawerSelectLabels` / `DrawerRadioLabels`.

                The form below pairs both: *Affected components* (multi) and
                *Primary component* (single).
            """),
            await _triage_form.render(),
            c.code([
                ("model", src.text("triage_model"), "python"),
                ("form", src.text("triage_form"), "python"),
            ]),

            c.markdown("""
                ### Per-field column span

                Fields can opt into a wider grid cell with the `columns=n`
                parameter on their annotation. The renderer adds a
                `hx-grid-span-{n}` class to the wrapping element so the
                field occupies `n` cells of the enclosing `hx-grid`. Below,
                `title` and `summary` both set `columns=2`, so they take
                the full row on a 2-column form; `author` and
                `published_on` keep the default single-cell layout.
            """),
            await _article_form.render(),
            c.code([
                ("model", src.text("article_model"), "python"),
                ("form", src.text("article_form"), "python"),
            ]),
            c.markdown("""
                ### Per-field row span

                The column counterpart `rows=n` makes a field taller: the
                renderer adds a `hx-grid-row-span-{n}` class so the cell
                occupies `n` rows of the enclosing `hx-grid`. Combine it with
                `columns=` for a 2-D span. Below, `bio` sets `rows=2`, so on a
                2-column form it takes the right column across both rows while
                `display_name` and `location` stack down the left.
            """),
            await _profile_form.render(),

            c.markdown("""
                ### Field-keyed layout (`template_areas`)

                For precise placement, pass a full CSS-Grid layout on the
                `@a.form(...)` decorator, addressed **by field name**.
                `template_areas` lists the rows (`"."` = empty cell); a key
                repeated across cells spans those columns/rows. Add
                `template_columns` to size the tracks. Here `headline` spans
                the top row, `body` spans two rows down a `2fr` column, and
                `author` / `tags` stack in the `1fr` sidebar. When a template
                is set, per-field `columns` / `rows` are ignored.
            """),
            await _blog_form.render(),

            c.markdown("""
                ### Read-only / disabled form

                Passing ``disabled=True`` to ``DataForm.render(...)`` propagates the
                flag through every dispatched primitive — text inputs, dropdowns,
                segment controls, fieldsets, *and* the submit button — so the entire
                form renders as read-only with the consistent muted look. Hidden
                fields stay live (their values still submit), but since the submit
                button is also disabled there's nothing for a user to trigger.
            """),
            await _issue_form.render(
                value=IssueReport(
                    title="Read-only view",
                    issue_type="bug",
                    description="This whole form is rendered with disabled=True.",
                ),
                disabled=True,
            ),

            c.markdown("""
                ### Extra actions next to Save

                ``DataForm.render(actions=...)`` takes a single ``y.Node`` (or a
                ``y.fragment[...]`` for multiple) and inserts it inside the same
                flex row as the primary submit button — on a normal page that
                means *left of* Save, since the row is right-aligned. Use it for
                Cancel, Reset, "Save as draft", etc.
            """),
            await _issue_form.render(
                value=IssueReport(
                    title="With extra actions",
                    issue_type="bug",
                    description="Cancel and Save-as-draft sit to the left of Save.",
                ),
                actions=y.fragment[
                    c.button("Cancel", variant="outline"),
                    c.button("Save draft", variant="ghost"),
                ],
            ),

            c.markdown("""
                ### `disable_actions=True` — no divider, no buttons

                For read-only embeds or fragments owned by an outer page, pass
                ``disable_actions=True`` to skip the ``<hr>`` *and* the entire
                actions wrapper (including the submit button). Hidden form
                fields stay live, but with no submit button there's no way to
                post the form from the UI.
            """),
            await _issue_form.render(
                value=IssueReport(
                    title="No actions area",
                    issue_type="question",
                    description="The hr divider and the actions row are both gone.",
                ),
                disable_actions=True,
            ),

            c.markdown("""
                ### Inside a drawer — Save on top, secondary actions below

                The same form rendered inside ``drawer_content`` — ``drawer.css``
                flips ``.hx-data-form__actions`` to ``flex-direction:
                column-reverse``. Submit ends up at the top of the column and
                the secondary actions stack below it **in reverse DOM order**,
                so the button that was closest to Submit on the page
                (rightmost extra) becomes the first one below Submit in the
                drawer.

                Above, the page-level demo renders ``[Cancel, Save draft, Save]``
                left-to-right. The drawer demo below renders the same fragment
                top-to-bottom as ``[Save, Save draft, Cancel]``.
            """),
            c.button(
                "Open form in drawer",
                **c.open_drawer_htmx_attributes(_drawer_form_fragment.url()),
            ),
            c.code([("fragment", src.text("drawer_form_fragment"), "python")]),

            c.markdown("""
                ### Drawer pickers inside a drawer form

                A form rendered in the drawer can itself contain
                ``drawer_select`` / ``drawer_radio`` controls. These open the
                **popup drawer** — a second drawer instance stacked on top of
                this one — so picking components layers over the form instead of
                replacing it. Closing or confirming the picker returns to the
                form with the drawer still intact.
            """),
            c.button(
                "Open triage form in drawer",
                **c.open_drawer_htmx_attributes(_drawer_triage_fragment.url()),
            ),

            c.markdown("""
                ### New-record form — no initial value, invalid from the start

                Calling `render()` with no `value` builds an empty instance via
                `model_construct()` (validation bypassed), then re-validates it to
                determine the submit-button state. Required fields without defaults
                surface their Pydantic errors immediately, the submit button stays
                disabled, and the `/validate` round-trip clears each error as the user
                fills the corresponding field. Try typing a 4-character title — the
                error swaps to *"String should have at least 5 characters"* on the
                next change; a 5-character title clears it and re-enables submit once
                the description is long enough too.
            """),
            await _blank_issue_form.render(),

            c.markdown("""
                ## Custom layouts with `HeadlessForm`

                `DataForm` renders a model through a *fixed* annotation-driven grid.
                When you need a layout it can't express — fields grouped into bespoke
                columns, custom controls between them, or a form embedded as an
                edit-in-place table row — reach for `HeadlessForm[T]` instead. It is
                the **same controller engine** (form parsing, `model_validate`, error
                reduction, touched-tracking, the `/validate` + `/submit` HTMX
                fragments, submit gating) with the *layout* handed back to you.

                You pass a `render` callback `(ctx: FormRenderContext[T]) -> y.Node`
                that builds the markup. Wire the HTMX behaviour with three helpers off
                `ctx.form` — no string constants to copy:

                - `form_attrs(oob=ctx.oob)` on the `<form>` (plus `id=ctx.form.wrapper_div_id`)
                - `validate_attrs(oob=ctx.oob)` on the container wrapping the validated fields
                - `touched_inputs(ctx.touched)` inside that container

                Per field, read `ctx.visible_errors.get("name")` for inline error text
                (touched fields only) and gate the submit button on the full
                `bool(ctx.errors)`. Parsing is derived from the model's field types
                (`list[...]` → repeated keys, `bool` → checkbox presence), so a plain
                `BaseModel` works without the `@a.form` / `Annotated[…]` system.

                The form below uses a hand-written render callback: first / last name
                share a row, email and message span both columns, and the actions row is
                hand-placed. Validation, inline errors and submit gating behave just
                like `DataForm` — type a too-short message or a malformed email and
                blur to see the error; fill every field to enable **Send message**.

                > `ctx.oob` matters when a `HeadlessForm` is delivered *inside another
                > HTMX swap* (e.g. an edit row morphed into a table): the initial
                > render must omit `hx-swap-oob` or htmx would extract and discard the
                > form. The helpers handle this for you — just thread `ctx.oob`
                > through. On a plain page like this one it is always `False` on first
                > paint and `True` for the live validate/submit re-renders.
            """),
            await _contact_form.render(),
            c.code([
                ("render", src.text("contact_render"), "python"),
                ("form", src.text("contact_form"), "python"),
            ]),

            y.h2["Issue report (live example)"],
            c.example(
                # docs:start live_form
                y.form(
                    **classnames("hx-grid", **styles()),
                    style="--hx-grid-columns: 2",
                )[
                    # Row 1 — text input alongside a horizontal radio_fieldset.
                    c.form_field(
                        "title",
                        "Title",
                        y.input,
                        required=True,
                        placeholder="Short summary",
                    ),
                    c.radio_fieldset(
                        "Type (horizontal)",
                        "type_fs_horizontal",
                        tuple(TYPE_OPTIONS),
                        value="bug",
                        orientation="horizontal",
                    ),

                    # Row 2 — text input alongside a horizontal checkbox_fieldset.
                    c.form_field(
                        "description",
                        "Description",
                        y.input,
                        help_text="What were you trying to do? What happened instead?",
                        placeholder="Steps to reproduce …",
                    ),
                    c.checkbox_fieldset(
                        "Labels (horizontal)",
                        "labels_fs_horizontal",
                        LABEL_OPTIONS,
                        value=("backend",),
                        orientation="horizontal",
                    ),

                    # Row 3 — dropdown_radio + segment_control via partial.
                    c.form_field(
                        "priority",
                        "Priority",
                        partial(c.dropdown_radio, options=PRIORITY_OPTIONS),
                        help_text="How urgent is it?",
                        error_text="That's strange!"
                    ),
                    c.form_field(
                        "type",
                        "Type",
                        partial(c.segment_control, options=TYPE_OPTIONS),
                        help_text="Huhu!"
                    ),

                    # Row 4 — dropdown_checkbox + email success.
                    c.form_field(
                        "labels",
                        "Labels",
                        partial(c.dropdown_checkbox, options=LABEL_OPTIONS),
                        help_text="Pick any that apply",
                    ),
                    c.form_field(
                        "email",
                        "Email",
                        y.input,
                        type="email",
                        value="me@example.com",
                        success_text="That looks like a valid email.",
                    ),

                    # Row 5 — email error + vertical radio_fieldset.
                    c.form_field(
                        "email_bad",
                        "Email (with error)",
                        y.input,
                        type="email",
                        value="not-an-email",
                        error_text="That doesn't look like a valid email.",
                    ),
                    c.radio_fieldset(
                        "Priority (fieldset)",
                        "priority_fs",
                        PRIORITY_OPTIONS,
                        value="medium",
                    ),

                    # Row 6 — vertical checkbox_fieldset (paired with the
                    # vertical radio above by grid flow).
                    c.checkbox_fieldset(
                        "Labels (fieldset)",
                        "labels_fs",
                        LABEL_OPTIONS,
                        value=("backend", "docs"),
                    ),
                ],
                # docs:end live_form
                code=[("code", src.text("live_form"), "python")],
            ),

            c.markdown("""
                ## Disabled state

                Every form primitive accepts `disabled: bool = False`. The
                native implementations use the HTML `disabled` attribute
                (`<button>`, `<input>`, `<fieldset>` — which cascades to all
                contained inputs). The composite primitives — `dropdown_*`,
                `segment_control` — propagate `disabled` to every inner
                radio/checkbox and mark their wrapper with
                `aria-disabled="true"`, so the form can't submit a value
                and the control can't be opened or toggled.

                Look-and-feel is unified by Pico's existing
                `--pico-form-element-disabled-opacity` token, so dimming is
                consistent with native disabled inputs as well.

                Below is the same set of controls as above, with
                `disabled=True` set on each one. `form_field` forwards
                `disabled` to whatever factory it wraps.
            """),
            c.example(
                # docs:start disabled_form
                y.form(
                    **classnames("hx-grid", **styles()),
                    style="--hx-grid-columns: 2",
                )[
                    # Row 1 — plain text input + horizontal radio_fieldset.
                    c.form_field(
                        "disabled_title",
                        "Title",
                        y.input,
                        placeholder="Short summary",
                        value="Cannot edit",
                        disabled=True,
                    ),
                    c.radio_fieldset(
                        "Type (horizontal)",
                        "disabled_type_fs_horizontal",
                        tuple(TYPE_OPTIONS),
                        value="bug",
                        orientation="horizontal",
                        disabled=True,
                    ),

                    # Row 2 — dropdown_radio + segment_control via partial.
                    c.form_field(
                        "disabled_priority",
                        "Priority",
                        partial(c.dropdown_radio, options=PRIORITY_OPTIONS),
                        value="high",
                        help_text="How urgent is it?",
                        disabled=True,
                    ),
                    c.form_field(
                        "disabled_view",
                        "View",
                        partial(c.segment_control, options=TYPE_OPTIONS),
                        value="feature",
                        disabled=True,
                    ),

                    # Row 3 — dropdown_checkbox + vertical checkbox_fieldset.
                    c.form_field(
                        "disabled_labels",
                        "Labels",
                        partial(c.dropdown_checkbox, options=LABEL_OPTIONS),
                        value=("backend", "docs"),
                        disabled=True,
                    ),
                    c.checkbox_fieldset(
                        "Labels (fieldset)",
                        "disabled_labels_fs",
                        LABEL_OPTIONS,
                        value=("backend", "docs"),
                        disabled=True,
                    ),

                    # Row 4 — buttons (native + anchor variants).
                    y.div[
                        c.button("Save", appearance="primary", disabled=True),
                        " ",
                        c.button("Cancel", variant="outline", disabled=True),
                        " ",
                        c.button(
                            "Docs", variant="link", href="/docs", disabled=True
                        ),
                    ],
                ],
                # docs:end disabled_form
                code=[("code", src.text("disabled_form"), "python")],
            ),

            c.markdown("""
                ## Plugging multi-arg controls in with `partial`

                `form_field` calls its `input` factory as `input(name=…, **attrs)`. That's a
                direct fit for `y.input`, whose kwargs are just HTML attributes — pass the
                function in raw and you're done.

                But components like `dropdown_radio`, `dropdown_checkbox`, and
                `segment_control` have additional *required* parameters (typically
                `options`) that can't be supplied through `**kwargs` alone. Solve it with
                `functools.partial`: pre-bind the extras and get back a callable whose
                remaining shape matches the `InputFactory` contract.

                Anything `form_field` forwards through `**attrs` (the `name` it sets
                internally, plus any kwargs from the call site) lands on the bound
                callable. Components that consume those keywords natively — like the
                dropdowns' `name` and `placeholder` — work as expected. The live example
                above shows all three patterns (rows 3–4).
            """),
            c.code([("code", src.text("live_form"), "python")]),
        ]
    )
