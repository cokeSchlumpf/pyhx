import dataclasses

import pytest

from pyhx.components import Color
from pyhx.components.view_model import document_viewer as vm


class TestBoundingBox:
    def test_is_given_in_fractions_of_the_page(self):
        box = vm.BoundingBox(x=0.1, y=0.2, width=0.3, height=0.05)

        assert (box.x, box.y, box.width, box.height) == (0.1, 0.2, 0.3, 0.05)

    def test_from_pixels_gives_fractions(self):
        box = vm.BoundingBox.from_pixels(
            x=124, y=175.4, width=620, height=87.7, page_width=1240, page_height=1754
        )

        assert (box.x, box.y, box.width, box.height) == pytest.approx(
            (0.1, 0.1, 0.5, 0.05)
        )

    @pytest.mark.parametrize(
        "values",
        [
            {"x": -0.1, "y": 0, "width": 0.1, "height": 0.1},
            {"x": 0, "y": 1.2, "width": 0.1, "height": 0.1},
            {"x": 0.8, "y": 0, "width": 0.3, "height": 0.1},
            {"x": 0, "y": 0.95, "width": 0.1, "height": 0.1},
        ],
    )
    def test_refuses_values_outside_the_page(self, values: dict[str, float]):
        with pytest.raises(ValueError):
            vm.BoundingBox(**values)


class TestPoint:
    def test_from_pixels(self):
        point = vm.Point.from_pixels(x=620, y=877, page_width=1240, page_height=1754)

        assert point == vm.Point(0.5, 0.5)

    def test_refuses_values_outside_the_page(self):
        with pytest.raises(ValueError):
            vm.Point(x=1.5, y=0.5)


class TestDocumentPage:
    def test_a_page_with_a_size_has_its_aspect_ratio(self):
        page = vm.DocumentPage(src="/p.png", width=1240, height=1754)

        assert page.size_known
        assert page.aspect_ratio == "1240 / 1754"

    @pytest.mark.parametrize("size", [{}, {"width": 1240}, {"height": 1754}])
    def test_without_both_sizes_a4_is_assumed(self, size: dict[str, int]):
        page = vm.DocumentPage(src="/p.png", **size)

        assert not page.size_known
        assert page.aspect_ratio == vm.A4_ASPECT_RATIO == "210 / 297"

    @pytest.mark.parametrize("size", [{"width": 0}, {"height": -1}])
    def test_refuses_a_size_that_is_not_positive(self, size: dict[str, int]):
        with pytest.raises(ValueError):
            vm.DocumentPage(src="/p.png", **size)


class TestValues:
    def test_are_immutable(self):
        mark = vm.Mark(id="m", label="M", box=vm.BoundingBox(0, 0, 0.1, 0.1))

        with pytest.raises(dataclasses.FrozenInstanceError):
            mark.label = "other"  # type: ignore[misc]

    def test_defaults_of_marks_notes_and_badges(self):
        mark = vm.Mark(id="m", label="M", box=vm.BoundingBox(0, 0, 0.1, 0.1))
        note = vm.Note(id="n", label="N", at=vm.Point(0.5, 0.5))
        badge = vm.PageBadge(text="2", label="2 values")

        assert mark.style == vm.MarkStyle(color="info", look="fill")
        assert note.color == "warning"
        assert badge.appearance == "neutral"

    def test_css_color_of_an_appearance_and_a_colour(self):
        assert vm.css_color("warning") == Color.appearance("warning").value
        assert vm.css_color(Color.hex("#6d28d9")) == Color.hex("#6d28d9").value

    def test_the_names_stay_out_of_pyhx_components(self):
        import pyhx.components as c

        for name in ("Document", "Mark", "Note", "Point", "BoundingBox"):
            assert not hasattr(c, name)
