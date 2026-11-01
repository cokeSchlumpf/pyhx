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
