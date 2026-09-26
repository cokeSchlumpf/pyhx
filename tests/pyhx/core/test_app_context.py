import pytest

from pyhx.core.app_context import AppContext
from pyhx.core.webapp import WebApp


class _DummyService:
    pass


class _OtherService:
    pass


class _SubService(_DummyService):
    pass


# ---------------------------------------------------------------------------
# WebApp side: encapsulated dict + set_context
# ---------------------------------------------------------------------------


class TestWebAppContextStorage:
    def test_constructor_seeds_the_context(self):
        svc = _DummyService()
        app = WebApp(context={"svc": svc, "tenant_id": "acme"})
        assert app.context.get("svc", _DummyService) is svc
        assert app.context.get("tenant_id", str) == "acme"

    def test_set_context_adds_new_key(self):
        app = WebApp()
        svc = _DummyService()
        app.set_context("svc", svc)
        assert app.context.get("svc", _DummyService) is svc

    def test_set_context_replaces_existing_key(self):
        app = WebApp(context={"tenant_id": "acme"})
        app.set_context("tenant_id", "globex")
        assert app.context.get("tenant_id", str) == "globex"

    def test_values_view_is_read_only(self):
        app = WebApp(context={"a": 1})
        with pytest.raises(TypeError):
            app.context.values["a"] = 2  # type: ignore[index]

    def test_caller_dict_is_not_aliased(self):
        # Constructor defensively copies so the caller can't smuggle
        # mutations in after construction.
        caller_dict: dict = {"a": 1}
        app = WebApp(context=caller_dict)
        caller_dict["a"] = 999
        assert app.context.get("a", int) == 1


# ---------------------------------------------------------------------------
# AppContext.get(key, type)
# ---------------------------------------------------------------------------


class TestAppContextGetByKey:
    def test_returns_value_when_key_and_type_match(self):
        svc = _DummyService()
        ctx = AppContext({"svc": svc})
        assert ctx.get("svc", _DummyService) is svc

    def test_accepts_subclass_for_isinstance_check(self):
        sub = _SubService()
        ctx = AppContext({"svc": sub})
        # ``_SubService`` is-a ``_DummyService``, so lookup by the parent
        # type still succeeds.
        assert ctx.get("svc", _DummyService) is sub

    def test_missing_key_raises_key_error(self):
        ctx = AppContext({"a": 1})
        with pytest.raises(KeyError):
            ctx.get("nope", int)

    def test_wrong_type_raises_type_error(self):
        ctx = AppContext({"a": 1})
        with pytest.raises(TypeError):
            ctx.get("a", str)


# ---------------------------------------------------------------------------
# AppContext.get(type)
# ---------------------------------------------------------------------------


class TestAppContextGetByType:
    def test_returns_unique_match(self):
        svc = _DummyService()
        other = _OtherService()
        ctx = AppContext({"svc": svc, "other": other, "tenant": "acme"})
        assert ctx.get(_DummyService) is svc
        assert ctx.get(_OtherService) is other

    def test_zero_matches_raises_lookup_error(self):
        ctx = AppContext({"a": 1})
        with pytest.raises(LookupError):
            ctx.get(_DummyService)

    def test_multiple_matches_raises_lookup_error(self):
        ctx = AppContext({"a": _DummyService(), "b": _DummyService()})
        with pytest.raises(LookupError):
            ctx.get(_DummyService)

    def test_subclass_satisfies_parent_lookup(self):
        # A single ``_SubService`` entry is the unique match for both
        # ``_SubService`` and ``_DummyService``.
        sub = _SubService()
        ctx = AppContext({"svc": sub})
        assert ctx.get(_SubService) is sub
        assert ctx.get(_DummyService) is sub


# ---------------------------------------------------------------------------
# Live-reference semantics: WebApp.set_context after construction reaches the
# AppContext threaded into a RequestContext built earlier.
# ---------------------------------------------------------------------------


class TestLiveReference:
    def test_app_context_sees_post_construction_writes(self):
        app = WebApp()
        # Take a reference to the AppContext *before* the write …
        ctx = app.context
        app.set_context("feature_flag", True)
        # … and confirm that pre-existing AppContext instance sees the
        # new value (live reference, not snapshot).
        assert ctx.get("feature_flag", bool) is True
