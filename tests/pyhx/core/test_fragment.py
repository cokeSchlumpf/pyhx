from http import HTTPMethod, HTTPStatus

import pytest

from pyhx.core.fragment import (
    Fragment,
    FragmentDefinition,
    FragmentFactory,
    FragmentResponse,
)
from pyhx.core.primitives import Path, PathTemplate


async def _dummy_render(): ...


class TestRedirect:
    def test_uses_hx_redirect_header_not_location(self):
        response = FragmentResponse.redirect("/orders/42")

        # HTMX's XHR follows a 3xx transparently and would swap the redirected
        # page into the originating element, so the redirect has to travel in
        # ``HX-Redirect`` on a 200 instead.
        assert response.headers == {"HX-Redirect": "/orders/42"}
        assert response.status_code == HTTPStatus.OK

    def test_body_is_empty(self):
        assert FragmentResponse.redirect("/orders/42").node == ""


class TestUrl:
    def _make(self, path: str) -> FragmentDefinition:
        return FragmentDefinition(PathTemplate(path), HTTPMethod.GET, _dummy_render)

    def test_path_params_only(self):
        fragment = self._make("/users/{id}")
        assert fragment.url(id=42) == "/users/42"

    def test_query_only(self):
        fragment = self._make("/items")
        assert fragment.url(query={"select_id": 7}) == "/items?select_id=7"

    def test_path_params_and_query(self):
        fragment = self._make("/users/{id}")
        assert fragment.url(id=42, query={"tab": "posts"}) == "/users/42?tab=posts"

    def test_none_query_omits_question_mark(self):
        fragment = self._make("/items")
        assert fragment.url(query=None) == "/items"

    def test_empty_query_omits_question_mark(self):
        fragment = self._make("/items")
        assert fragment.url(query={}) == "/items"


def _make_factory(fragments: list[Fragment] | None = None) -> FragmentFactory:
    return FragmentFactory(fragments if fragments is not None else [])


class TestExists:
    # --- Empty / no match ---

    def test_empty_factory_returns_false(self):
        factory = _make_factory()
        assert factory.exists("/users", HTTPMethod.GET) is False

    def test_no_match_returns_false(self):
        factory = _make_factory()
        factory.add("/users", "GET", _dummy_render)
        assert factory.exists("/admins", HTTPMethod.GET) is False

    def test_path_matches_but_method_differs_returns_false(self):
        factory = _make_factory()
        factory.add("/users", "GET", _dummy_render)
        assert factory.exists("/users", HTTPMethod.POST) is False

    # --- str query ---

    def test_str_query_equal_to_registered_template_returns_true(self):
        factory = _make_factory()
        factory.add("/users/{id}", "GET", _dummy_render)
        assert factory.exists("/users/{id}", HTTPMethod.GET) is True

    def test_str_query_with_different_var_name_returns_false(self):
        # PathTemplate compares by string form, so "{id}" != "{user_id}".
        factory = _make_factory()
        factory.add("/users/{id}", "GET", _dummy_render)
        assert factory.exists("/users/{user_id}", HTTPMethod.GET) is False

    def test_str_method_literal_accepted(self):
        factory = _make_factory()
        factory.add("/users", "GET", _dummy_render)
        assert factory.exists("/users", "GET") is True

    def test_invalid_str_method_raises(self):
        factory = _make_factory()
        with pytest.raises(ValueError):
            factory.exists("/users", "FOOBAR")  # type: ignore[arg-type]

    # --- PathTemplate query ---

    def test_pathtemplate_query_equal_returns_true(self):
        factory = _make_factory()
        factory.add("/users/{id}", "GET", _dummy_render)
        assert factory.exists(PathTemplate("/users/{id}"), HTTPMethod.GET) is True

    def test_pathtemplate_query_unequal_returns_false(self):
        factory = _make_factory()
        factory.add("/users/{id}", "GET", _dummy_render)
        assert (
            factory.exists(PathTemplate("/users/{id}/posts"), HTTPMethod.GET) is False
        )

    # --- Path (concrete) query ---

    def test_concrete_path_matching_registered_template_returns_true(self):
        # /users/42 matches the template /users/{id}.
        factory = _make_factory()
        factory.add("/users/{id}", "GET", _dummy_render)
        assert factory.exists(Path("/users/42"), HTTPMethod.GET) is True

    def test_concrete_path_not_matching_template_returns_false(self):
        factory = _make_factory()
        factory.add("/users/{id}", "GET", _dummy_render)
        assert factory.exists(Path("/admins/42"), HTTPMethod.GET) is False

    def test_concrete_path_matches_static_registered_path(self):
        factory = _make_factory()
        factory.add("/health", "GET", _dummy_render)
        assert factory.exists(Path("/health"), HTTPMethod.GET) is True
