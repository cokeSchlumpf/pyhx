from http import HTTPStatus

from pyhx.core.page import PageDefinition, PageResponse
from pyhx.core.primitives import PathTemplate, omit


async def _dummy_render(): ...


class TestRedirect:
    def test_sends_303_with_location_header(self):
        response = PageResponse.redirect("/login")

        assert response.status_code == HTTPStatus.SEE_OTHER
        assert response.headers == {"location": "/login"}

    def test_body_is_empty(self):
        assert PageResponse.redirect("/login").node == ""

    def test_skips_the_default_page_template(self):
        # The browser only reads the ``Location`` header, so wrapping an empty
        # body in the app skeleton would be pure waste.
        assert PageResponse.redirect("/login").page_template is omit


class TestUrl:
    def _make(self, path: str) -> PageDefinition:
        return PageDefinition(PathTemplate(path), title="Title", render=_dummy_render)

    def test_path_params_only(self):
        page = self._make("/users/{id}")
        assert page.url(id=42) == "/users/42"

    def test_path_params_and_query(self):
        page = self._make("/users/{id}")
        assert page.url(id=42, query={"tab": "posts"}) == "/users/42?tab=posts"

    def test_none_query_omits_question_mark(self):
        page = self._make("/users/{id}")
        assert page.url(id=42, query=None) == "/users/42"
