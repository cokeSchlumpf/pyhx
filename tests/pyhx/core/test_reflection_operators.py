import inspect
from typing import Annotated, Any, List, Optional, Protocol, Union

import pytest

from pyhx.core.reflection_operators import (
    ensure_parameter_type_in_signature,
    inject_parameters,
)


class Marker: ...
class Other: ...


class Animal: ...
class Dog(Animal): ...
class Puppy(Dog): ...


class MyProtocol(Protocol):
    def hello(self) -> str: ...


def _fn_with_marker(x: int, ctx: Marker, y: str) -> None: ...
def _fn_without_marker(x: int, y: str) -> None: ...
def _fn_no_params() -> None: ...


class TestEnsureParameterTypeInSignature:
    def test_found_returns_original_signature_and_existing_name(self):
        sig, name, added = ensure_parameter_type_in_signature(_fn_with_marker, Marker, "default")
        assert name == "ctx"
        assert added is False
        assert sig == inspect.signature(_fn_with_marker)

    def test_not_found_returns_extended_signature_with_default_name(self):
        sig, name, added = ensure_parameter_type_in_signature(_fn_without_marker, Marker, "default")
        assert name == "default"
        assert added is True
        assert "default" in sig.parameters
        assert sig.parameters["default"].annotation is Marker

    def test_not_found_preserves_existing_params(self):
        sig, _, _ = ensure_parameter_type_in_signature(_fn_without_marker, Marker, "default")
        assert "x" in sig.parameters
        assert "y" in sig.parameters

    def test_no_params_extends_to_single_param(self):
        sig, name, added = ensure_parameter_type_in_signature(_fn_no_params, Marker, "ctx")
        assert name == "ctx"
        assert added is True
        assert list(sig.parameters.keys()) == ["ctx"]

    def test_first_matching_type_wins(self):
        def fn(a: Marker, b: Marker) -> None: ...
        sig, name, added = ensure_parameter_type_in_signature(fn, Marker, "default")
        assert name == "a"
        assert added is False

    def test_unannotated_param_is_not_matched(self):
        def fn(x, y: str) -> None: ...
        sig, name, added = ensure_parameter_type_in_signature(fn, str, "default")
        assert name == "y"
        assert added is False


class TestInjectParameters:
    # --- Matching ---

    def test_exact_type_match(self):
        def fn(m: Marker) -> None: ...
        m = Marker()
        assert inject_parameters(fn, {Marker: m}) == {"m": m}

    def test_subclass_key_matches_annotation(self):
        def fn(a: Animal) -> None: ...
        d = Dog()
        assert inject_parameters(fn, {Dog: d}) == {"a": d}

    def test_exact_match_wins_over_subclass(self):
        def fn(a: Animal) -> None: ...
        animal = Animal()
        dog = Dog()
        assert inject_parameters(fn, {Animal: animal, Dog: dog}) == {"a": animal}

    def test_duplicate_annotated_params_both_get_same_instance(self):
        def fn(a: Marker, b: Marker) -> None: ...
        m = Marker()
        assert inject_parameters(fn, {Marker: m}) == {"a": m, "b": m}

    # --- Skip conditions ---

    def test_unannotated_param_skipped(self):
        def fn(m: Marker, x) -> None: ...
        m = Marker()
        assert inject_parameters(fn, {Marker: m}) == {"m": m}

    def test_annotation_not_in_instances_skipped(self):
        def fn(m: Marker, o: Other) -> None: ...
        m = Marker()
        assert inject_parameters(fn, {Marker: m}) == {"m": m}

    def test_ambiguous_subclass_matches_skipped(self):
        # Annotation is Animal; both Dog and Puppy are subclasses → ambiguous → skip
        def fn(a: Animal) -> None: ...
        assert inject_parameters(fn, {Dog: Dog(), Puppy: Puppy()}) == {}

    def test_var_positional_keyword_and_positional_only_skipped(self):
        # Positional-only, *args, **kwargs all skipped.
        def fn(p: Marker, /, k: Marker, *args: Marker, **kwargs: Marker) -> None: ...
        m = Marker()
        # Only `k` is POSITIONAL_OR_KEYWORD/KEYWORD_ONLY-eligible.
        assert inject_parameters(fn, {Marker: m}) == {"k": m}

    def test_keyword_only_param_matched(self):
        def fn(*, k: Marker) -> None: ...
        m = Marker()
        assert inject_parameters(fn, {Marker: m}) == {"k": m}

    # --- Optional / Union ---

    def test_optional_typing_form_matches_inner(self):
        def fn(m: Optional[Marker]) -> None: ...
        m = Marker()
        assert inject_parameters(fn, {Marker: m}) == {"m": m}

    def test_pep604_optional_matches_inner(self):
        def fn(m: Marker | None) -> None: ...
        m = Marker()
        assert inject_parameters(fn, {Marker: m}) == {"m": m}

    def test_non_none_union_skipped(self):
        def fn(x: Union[Marker, Other]) -> None: ...
        assert inject_parameters(fn, {Marker: Marker(), Other: Other()}) == {}

    def test_optional_without_instance_skipped(self):
        def fn(m: Optional[Marker]) -> None: ...
        assert inject_parameters(fn, {}) == {}

    # --- String / forward-ref annotations ---

    def test_pep563_string_annotations_resolved(self, tmp_path):
        # Build a self-contained module with `from __future__ import
        # annotations` so the function's annotations are stored as strings
        # and need resolving via `typing.get_type_hints`.
        import importlib.util
        import sys

        module_src = (
            "from __future__ import annotations\n"
            "class A: ...\n"
            "class B: ...\n"
            "def handler(a: A, b: B) -> None: ...\n"
        )
        mod_path = tmp_path / "_pep563_mod.py"
        mod_path.write_text(module_src)
        spec = importlib.util.spec_from_file_location("_pep563_mod", mod_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_pep563_mod"] = mod
        try:
            spec.loader.exec_module(mod)
            a, b = mod.A(), mod.B()
            assert inject_parameters(mod.handler, {mod.A: a, mod.B: b}) == {"a": a, "b": b}
        finally:
            sys.modules.pop("_pep563_mod", None)

    def test_unresolvable_forward_ref_does_not_break_other_params(self):
        # Explicit string annotation that names a non-existent type for `x`,
        # plus a resolvable real-type annotation for `m`. Resolution of x
        # fails, but m should still be injected.
        def fn(m: Marker, x: "DoesNotExist") -> None: ...  # noqa: F821
        m = Marker()
        assert inject_parameters(fn, {Marker: m}) == {"m": m}

    # --- Edge types ---

    def test_any_annotation_skipped(self):
        def fn(x: Any) -> None: ...
        assert inject_parameters(fn, {Marker: Marker()}) == {}

    def test_parameterized_generic_skipped(self):
        def fn(xs: List[int]) -> None: ...
        assert inject_parameters(fn, {List: [1, 2, 3]}) == {}

    def test_annotated_metadata_stripped(self):
        def fn(m: Annotated[Marker, "tag"]) -> None: ...
        m = Marker()
        assert inject_parameters(fn, {Marker: m}) == {"m": m}

    def test_non_runtime_checkable_protocol_in_instances_does_not_raise(self):
        # MyProtocol is NOT @runtime_checkable. A subclass scan against an
        # unrelated annotation must not blow up because MyProtocol is a key.
        def fn(m: Marker) -> None: ...
        m = Marker()
        proto_instance = object()
        # Exact match on Marker should still work; the bad key is just skipped
        # during any subclass scan.
        assert inject_parameters(fn, {Marker: m, MyProtocol: proto_instance}) == {"m": m}

    # --- Integration ---

    def test_round_trip_call_with_kwargs_splat(self):
        captured = {}

        def handler(m: Marker, o: Other) -> str:
            captured["m"] = m
            captured["o"] = o
            return "ok"

        m, o = Marker(), Other()
        kwargs = inject_parameters(handler, {Marker: m, Other: o})
        assert handler(**kwargs) == "ok"
        assert captured == {"m": m, "o": o}

    def test_round_trip_with_missing_key_raises_at_call_site(self):
        def handler(m: Marker, o: Other) -> None: ...
        m = Marker()
        kwargs = inject_parameters(handler, {Marker: m})  # missing Other
        assert kwargs == {"m": m}
        with pytest.raises(TypeError):
            handler(**kwargs)
