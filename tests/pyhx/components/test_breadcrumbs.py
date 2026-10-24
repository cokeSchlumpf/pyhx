import htpy as y

from pyhx.components import breadcrumbs


class TestBreadcrumbs:
    def test_renders_nav_with_ordered_list(self):
        html = str(breadcrumbs(y.a(href="/")["Home"], "Current"))

        assert html == (
            '<nav aria-label="Breadcrumb" class="hx-breadcrumbs"><ol>'
            '<li><a href="/">Home</a></li>'
            '<li aria-current="page">Current</li>'
            "</ol></nav>"
        )

    def test_single_item_is_current_page(self):
        assert '<li aria-current="page">Home</li>' in str(breadcrumbs("Home"))

    def test_without_items_renders_empty_list(self):
        assert "<ol></ol>" in str(breadcrumbs())

    def test_passes_extra_attributes(self):
        html = str(breadcrumbs("Home", class_="extra", id="crumbs"))

        assert 'class="hx-breadcrumbs extra"' in html
        assert 'id="crumbs"' in html
