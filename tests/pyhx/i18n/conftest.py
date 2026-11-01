import pytest

from pyhx.core.primitives.negotiate_locale import LocaleSettings


@pytest.fixture(autouse=True)
def locale_settings(monkeypatch):
    """Offer en, de, it and fr with English as default, independent of the settings files."""
    settings = LocaleSettings(
        supported_locales=["en", "de", "it", "fr"], default_locale="en"
    )
    monkeypatch.setattr(LocaleSettings, "read", staticmethod(lambda: settings))
    return settings


@pytest.fixture(autouse=True)
def set_context():
    """Set the request context for a test; it is reset afterwards, so tests don't leak into each other."""
    from pyhx.core.request_context import RequestContext, _current_request_context

    # Start without a request, whatever earlier tests (of other modules) left behind.
    tokens = [_current_request_context.set(RequestContext())]
    yield lambda ctx: tokens.append(_current_request_context.set(ctx))
    for token in reversed(tokens):
        _current_request_context.reset(token)
