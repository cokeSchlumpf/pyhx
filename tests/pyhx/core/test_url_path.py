import pytest

from pyhx.core.primitives.path_template import (
    Path,
    PathTemplate,
    StaticSegment,
    VariableSegment,
    encode_query,
)


class TestEncodeQuery:
    def test_empty_mapping_returns_empty_string(self) -> None:
        assert encode_query({}) == ""

    def test_single_param(self) -> None:
        assert encode_query({"foo": "bar"}) == "?foo=bar"

    def test_multiple_params_preserve_insertion_order(self) -> None:
        assert encode_query({"param": 123, "foo": "bar"}) == "?param=123&foo=bar"

    def test_none_values_are_skipped(self) -> None:
        assert encode_query({"a": 1, "b": None, "c": 3}) == "?a=1&c=3"

    def test_all_none_values_returns_empty_string(self) -> None:
        assert encode_query({"a": None, "b": None}) == ""

    def test_special_characters_are_escaped(self) -> None:
        assert encode_query({"q": "a b&c"}) == "?q=a+b%26c"

    def test_sequence_value_expands_to_repeated_params(self) -> None:
        assert encode_query({"t": ["a", "b"]}) == "?t=a&t=b"

    def test_none_inside_sequence_is_skipped(self) -> None:
        assert encode_query({"t": ["a", None, "b"]}) == "?t=a&t=b"


class TestConstruction:
    def test_root(self) -> None:
        t = PathTemplate("/")
        assert str(t) == "/"
        assert not t.is_parameterized()

    def test_static_path(self) -> None:
        t = PathTemplate("/users")
        assert str(t) == "/users"
        assert not t.is_parameterized()

    def test_parameterized_path(self) -> None:
        t = PathTemplate("/users/{user_id}")
        assert str(t) == "/users/{user_id}"
        assert t.is_parameterized()

    def test_multi_variable_path(self) -> None:
        t = PathTemplate("/users/{user_id}/posts/{post_id}")
        assert str(t) == "/users/{user_id}/posts/{post_id}"

    def test_segment_kinds(self) -> None:
        t = PathTemplate("/users/{user_id}")
        # White-box check: segments are typed correctly.
        assert t._segments == [StaticSegment("users"), VariableSegment("user_id")]

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "users",          # missing leading slash
            "//users",        # empty segment
            "/users/",        # trailing slash
            "/Users",         # uppercase rejected
            "/users/{1id}",   # variable must start with a letter
            "/users/{}",      # empty variable name
            "/users/{a-b}",   # hyphen not allowed in variable names
            "/users/ id ",    # whitespace
        ],
    )
    def test_invalid_template_raises(self, value: str) -> None:
        with pytest.raises(ValueError, match="Invalid path template"):
            PathTemplate(value)

    def test_duplicate_variable_raises(self) -> None:
        with pytest.raises(ValueError, match="Duplicate variable `x`"):
            PathTemplate("/{x}/{x}")


class TestExpand:
    def test_substitutes_variables(self) -> None:
        t = PathTemplate("/users/{user_id}/posts/{post_id}")
        assert t.expand(user_id="42", post_id="abc") == "/users/42/posts/abc"

    def test_coerces_non_string_values(self) -> None:
        t = PathTemplate("/users/{user_id}")
        assert t.expand(user_id=42) == "/users/42"

    def test_static_path_takes_no_args(self) -> None:
        assert PathTemplate("/health").expand() == "/health"

    def test_root_path(self) -> None:
        assert PathTemplate("/").expand() == "/"

    def test_missing_variable_raises(self) -> None:
        t = PathTemplate("/users/{user_id}/posts/{post_id}")
        with pytest.raises(ValueError, match="Missing variables: \\['post_id'\\]"):
            t.expand(user_id=1)

    def test_unexpected_variable_raises(self) -> None:
        t = PathTemplate("/users/{user_id}")
        with pytest.raises(ValueError, match="Unexpected variables: \\['extra'\\]"):
            t.expand(user_id=1, extra=2)

    def test_format_is_alias_for_expand(self) -> None:
        t = PathTemplate("/users/{user_id}")
        assert t.format(user_id=1) == t.expand(user_id=1)


class TestMatch:
    def test_extracts_variables(self) -> None:
        t = PathTemplate("/users/{user_id}")
        assert t.match("/users/42") == {"user_id": "42"}

    def test_multi_variable(self) -> None:
        t = PathTemplate("/users/{user_id}/posts/{post_id}")
        assert t.match("/users/42/posts/abc") == {"user_id": "42", "post_id": "abc"}

    def test_static_match_returns_empty_dict(self) -> None:
        assert PathTemplate("/health").match("/health") == {}

    def test_root_match_returns_empty_dict(self) -> None:
        assert PathTemplate("/").match("/") == {}

    @pytest.mark.parametrize(
        "path",
        [
            "/users",          # missing segment
            "/users/",         # trailing slash
            "/users/42/posts", # extra segment
            "/admin/42",       # different static
            "/users/A1",       # uppercase rejected by [a-z0-9_-]
            "/users/{42}",     # literal braces
            "",                # empty
        ],
    )
    def test_non_matching_paths_return_none(self, path: str) -> None:
        t = PathTemplate("/users/{user_id}")
        assert t.match(path) is None

    def test_root_does_not_match_other_paths(self) -> None:
        t = PathTemplate("/")
        assert t.match("/anything") is None

    def test_round_trip_expand_then_match(self) -> None:
        t = PathTemplate("/users/{user_id}/posts/{post_id}")
        rendered = t.expand(user_id="1", post_id="2")
        assert t.match(str(rendered)) == {"user_id": "1", "post_id": "2"}

    def test_static_segment_with_regex_special_chars_is_escaped(self) -> None:
        # Hyphens are allowed by the path grammar; ensure they're treated
        # literally in the match regex, not as a regex range.
        t = PathTemplate("/a-b/{id}")
        assert t.match("/a-b/1") == {"id": "1"}
        assert t.match("/aXb/1") is None


class TestEqualityAndHash:
    def test_equal_templates(self) -> None:
        assert PathTemplate("/users/{id}") == PathTemplate("/users/{id}")

    def test_different_variable_names_are_unequal(self) -> None:
        assert PathTemplate("/users/{id}") != PathTemplate("/users/{user_id}")

    def test_different_static_segments_are_unequal(self) -> None:
        assert PathTemplate("/users/{id}") != PathTemplate("/admin/{id}")

    def test_not_equal_to_string(self) -> None:
        assert PathTemplate("/users/{id}") != "/users/{id}"

    def test_hashable_and_consistent_with_equality(self) -> None:
        a = PathTemplate("/users/{id}")
        b = PathTemplate("/users/{id}")
        assert hash(a) == hash(b)
        assert {a, b} == {a}

    def test_usable_as_dict_key(self) -> None:
        d = {PathTemplate("/users/{id}"): "handler"}
        assert d[PathTemplate("/users/{id}")] == "handler"


class TestRepr:
    def test_repr_is_evaluable_form(self) -> None:
        t = PathTemplate("/users/{user_id}")
        assert repr(t) == "PathTemplate('/users/{user_id}')"

    def test_repr_round_trips_via_eval(self) -> None:
        t = PathTemplate("/users/{user_id}")
        assert eval(repr(t), {"PathTemplate": PathTemplate}) == t


class TestSegments:
    def test_static_segment_str(self) -> None:
        assert str(StaticSegment("users")) == "users"

    def test_variable_segment_str(self) -> None:
        assert str(VariableSegment("user_id")) == "{user_id}"


class TestPath:
    def test_root(self) -> None:
        assert str(Path("/")) == "/"

    def test_single_segment(self) -> None:
        assert str(Path("/users")) == "/users"

    def test_multi_segment(self) -> None:
        assert str(Path("/users/42/posts")) == "/users/42/posts"

    @pytest.mark.parametrize(
        "value",
        [
            "/{id}",
            "/users/{id}",
            "/users/{user_id}/posts/{post_id}",
        ],
    )
    def test_variables_rejected(self, value: str) -> None:
        with pytest.raises(ValueError, match="Invalid path"):
            Path(value)

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "users",          # missing leading slash
            "/users/",        # trailing slash
            "/Users",         # uppercase rejected
            "//users",        # empty segment
            "/users/ id",     # whitespace
        ],
    )
    def test_invalid_path_raises(self, value: str) -> None:
        with pytest.raises(ValueError, match="Invalid path"):
            Path(value)

    def test_equal_paths(self) -> None:
        assert Path("/users/42") == Path("/users/42")

    def test_different_paths_unequal(self) -> None:
        assert Path("/users/42") != Path("/users/99")

    def test_equal_to_matching_string(self) -> None:
        assert Path("/users/42") == "/users/42"

    def test_not_equal_to_different_string(self) -> None:
        assert Path("/users/42") != "/users/99"

    def test_not_equal_to_path_template(self) -> None:
        assert Path("/users") != PathTemplate("/users")

    def test_hashable_consistent_with_equality(self) -> None:
        a = Path("/users/42")
        b = Path("/users/42")
        assert hash(a) == hash(b)
        assert {a, b} == {a}

    def test_usable_as_dict_key(self) -> None:
        d = {Path("/health"): "handler"}
        assert d[Path("/health")] == "handler"

    def test_repr(self) -> None:
        assert repr(Path("/users/42")) == "Path('/users/42')"


class TestIsPrefixOf:
    def test_strict_prefix(self) -> None:
        assert Path("/a").is_prefix_of(Path("/a/b")) is True

    def test_longer_is_not_prefix(self) -> None:
        assert Path("/a/b").is_prefix_of(Path("/a")) is False

    def test_equal_paths_are_prefixes(self) -> None:
        assert Path("/a").is_prefix_of(Path("/a")) is True

    def test_root_is_prefix_of_other(self) -> None:
        assert Path("/").is_prefix_of(Path("/anything")) is True

    def test_root_is_prefix_of_root(self) -> None:
        assert Path("/").is_prefix_of(Path("/")) is True

    def test_segment_boundary_is_respected(self) -> None:
        # String-prefix would say yes; segment-prefix must say no.
        assert Path("/users").is_prefix_of(Path("/users-admin")) is False

    def test_multi_segment_prefix(self) -> None:
        assert Path("/a/b").is_prefix_of(Path("/a/b/c/d")) is True

    def test_diverging_segment_is_not_prefix(self) -> None:
        assert Path("/a/c").is_prefix_of(Path("/a/b/c")) is False


class TestPathTemplateJoin:

    def test_two_static_templates(self) -> None:
        result = PathTemplate("/foo/bar").join(PathTemplate("/lorem/ipsum"))
        assert isinstance(result, PathTemplate)
        assert str(result) == "/foo/bar/lorem/ipsum"

    def test_preserves_variables_from_both_sides(self) -> None:
        result = PathTemplate("/users/{user_id}").join(PathTemplate("/posts/{post_id}"))
        assert str(result) == "/users/{user_id}/posts/{post_id}"
        assert result.is_parameterized()

    def test_root_left(self) -> None:
        assert str(PathTemplate("/").join(PathTemplate("/foo"))) == "/foo"

    def test_root_right(self) -> None:
        assert str(PathTemplate("/foo").join(PathTemplate("/"))) == "/foo"

    def test_root_both(self) -> None:
        assert str(PathTemplate("/").join(PathTemplate("/"))) == "/"

    def test_join_with_concrete_path_returns_template(self) -> None:
        result = PathTemplate("/users/{id}").join(Path("/posts"))
        assert isinstance(result, PathTemplate)
        assert str(result) == "/users/{id}/posts"

    def test_truediv_delegates_to_join(self) -> None:
        a = PathTemplate("/foo/{x}")
        b = PathTemplate("/bar/{y}")
        assert a / b == a.join(b)


class TestPathJoin:

    def test_two_concrete_paths(self) -> None:
        result = Path("/foo/bar").join(Path("/lorem/ipsum"))
        assert isinstance(result, Path)
        assert str(result) == "/foo/bar/lorem/ipsum"

    def test_join_concrete_with_template_returns_template(self) -> None:
        result = Path("/foo").join(PathTemplate("/users/{id}"))
        assert isinstance(result, PathTemplate)
        assert not isinstance(result, Path)
        assert str(result) == "/foo/users/{id}"

    def test_root_left(self) -> None:
        assert str(Path("/").join(Path("/foo"))) == "/foo"

    def test_root_right(self) -> None:
        assert str(Path("/foo").join(Path("/"))) == "/foo"

    def test_root_both(self) -> None:
        assert str(Path("/").join(Path("/"))) == "/"

    def test_truediv_delegates_to_join(self) -> None:
        a = Path("/foo")
        b = Path("/bar")
        assert a / b == a.join(b)

    def test_truediv_with_template_returns_template(self) -> None:
        result = Path("/foo") / PathTemplate("/users/{id}")
        assert isinstance(result, PathTemplate)
        assert str(result) == "/foo/users/{id}"
