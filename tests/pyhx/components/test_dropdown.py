"""Render tests for the ``dropdown`` primitive.

Focus: the multi-select label-recompute wiring must work even when several
dropdowns sharing the same ``name`` live on one page/form — each instance must
include only its own option inputs and update only its own summary.
"""

import re

from pyhx.components.primitives.dropdown import dropdown_checkbox
from pyhx.components.view_model import Option


OPTIONS = [
    Option(label="Bug", value="bug"),
    Option(label="Feature", value="feature"),
    Option(label="Docs", value="docs"),
]


def _summary_id(html: str) -> str:
    m = re.search(r"<summary id=\"([^\"]+)\"", html)
    assert m, "summary id not found"
    return m.group(1)


def _attr(html: str, attr: str) -> str:
    m = re.search(rf'{attr}="([^"]+)"', html)
    assert m, f"{attr} not found"
    return m.group(1)


class TestLabelRecomputeWiring:
    def test_includes_own_inputs_via_this_not_first_only(self) -> None:
        # ``find input[name=…]`` matched only the *first* option, so the label
        # recompute ignored every non-first selection. ``this`` includes all of
        # the dropdown's own inputs.
        html = str(dropdown_checkbox("tags", OPTIONS, value=["feature"]))
        assert _attr(html, "hx-include") == "this"
        assert "find input" not in html

    def test_hx_target_matches_own_summary(self) -> None:
        html = str(dropdown_checkbox("tags", OPTIONS))
        assert _attr(html, "hx-target") == f"#{_summary_id(html)}"


class TestSameNameInstances:
    def test_distinct_summary_ids(self) -> None:
        a = str(dropdown_checkbox("shared", OPTIONS))
        b = str(dropdown_checkbox("shared", OPTIONS))
        assert _summary_id(a) != _summary_id(b)

    def test_each_targets_its_own_summary(self) -> None:
        # Two same-name dropdowns must each swap *their own* summary, not the
        # first one with that name.
        for _ in range(5):
            html = str(dropdown_checkbox("shared", OPTIONS))
            assert _attr(html, "hx-target") == f"#{_summary_id(html)}"

    def test_summary_id_is_a_valid_css_selector(self) -> None:
        # Statically prefixed with ``hx-`` so the id always starts with a letter —
        # a CSS ``#id`` selector can't start with a digit, and neither the uuid
        # suffix nor the name is guaranteed to.
        sid = _summary_id(str(dropdown_checkbox("shared", OPTIONS)))
        assert re.match(r"^[A-Za-z]", sid)
        assert sid.startswith("hx-shared--summary--")

    def test_summary_id_valid_when_name_starts_with_digit(self) -> None:
        # Regression: callers prefix the field name with a record uuid, e.g.
        # ``29ee8c8c-…-client-domicile``. Without the ``hx-`` prefix the id (and
        # thus ``hx-target``) started with a digit, an invalid CSS selector that
        # made htmx throw and silently skip the label-recompute swap.
        html = str(dropdown_checkbox("29ee8c8c-client-domicile", OPTIONS))
        sid = _summary_id(html)
        assert re.match(r"^-?[_A-Za-z][_A-Za-z0-9-]*$", sid)
        assert _attr(html, "hx-target") == f"#{sid}"
