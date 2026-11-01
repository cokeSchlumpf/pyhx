from contextvars import Context, copy_context

import pytest

from pyhx.core.webapp import WebApp, set_webapp


class TestWebAppContext:

    def test_get_after_set_returns_same_instance(self):
        app = WebApp()
        set_webapp(app)
        assert WebApp.get() is app

    def test_get_without_set_raises_lookup_error(self):
        # `Context()` (unlike `copy_context()`) creates a brand-new empty
        # context, so previous tests in the same session can't leak a value in.
        def _check() -> None:
            with pytest.raises(LookupError):
                WebApp.get()

        Context().run(_check)

    def test_set_replaces_previous_value(self):
        first = WebApp()
        second = WebApp()
        set_webapp(first)
        set_webapp(second)
        assert WebApp.get() is second

    def test_writes_are_isolated_to_their_context(self):
        outer = WebApp()
        inner = WebApp()
        set_webapp(outer)

        def in_isolated_context() -> WebApp:
            # The ContextVar value from the parent context is visible here ...
            assert WebApp.get() is outer
            # ... but writes inside this Context don't leak back out.
            set_webapp(inner)
            return WebApp.get()

        result = copy_context().run(in_isolated_context)

        assert result is inner          # inner context saw its own write
        assert WebApp.get() is outer    # outer context unaffected
