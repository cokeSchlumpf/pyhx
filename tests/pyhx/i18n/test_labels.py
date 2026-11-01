from datetime import date

from pyhx.components import CalendarLabels, DrawerRadioLabels, DrawerSelectLabels
from pyhx.components.primitives.conditional_select import ConditionalSelectLabels
from pyhx.i18n import use_locale

from .test_translate import dirs, write_catalog  # noqa: F401 (fixture)


class TestTranslatedLabels:
    def test_defaults_follow_the_language_explicit_labels_are_kept(self, dirs):
        _app_dir, pyhx_dir = dirs
        write_catalog(
            pyhx_dir,
            "de",
            "pyhx",
            {"Cancel": "Abbrechen", "Select items": "Einträge auswählen"},
        )
        write_catalog(
            pyhx_dir,
            "fr",
            "pyhx",
            {"Cancel": "Annuler", "Select items": "Sélectionner"},
        )
        labels = DrawerSelectLabels(select_button="Übernehmen")

        with use_locale("de"):
            assert (
                labels.cancel_button,
                labels.drawer_title,
                labels.select_button,
            ) == (
                "Abbrechen",
                "Einträge auswählen",
                "Übernehmen",
            )

        # The serialized state carries only the explicit label, no language …
        state = labels.model_dump_json()
        assert "Abbrechen" not in state and "Übernehmen" in state

        # … so a later request in another language shows its defaults.
        restored = DrawerSelectLabels.model_validate_json(state)
        with use_locale("fr"):
            assert (
                restored.cancel_button,
                restored.drawer_title,
                restored.select_button,
            ) == (
                "Annuler",
                "Sélectionner",
                "Übernehmen",
            )

    def test_english_defaults_without_a_catalog(self, dirs):
        assert DrawerRadioLabels().clear_item == "Clear selection"
        assert ConditionalSelectLabels().all_option == "All"
        assert ConditionalSelectLabels().drawer.cancel_button == "Cancel"


class TestCalendarLabels:
    def test_names_of_the_request_language(self):
        day = date(2026, 1, 5)  # a Monday
        expected = {
            "en": ("January", "M"),
            "de": ("Januar", "M"),
            "it": ("Gennaio", "L"),
            "fr": ("Janvier", "L"),
        }

        for locale, names in expected.items():
            with use_locale(locale):
                assert (
                    CalendarLabels().month(day),
                    CalendarLabels().weekday(day),
                ) == names

    def test_set_fields_override(self):
        with use_locale("de"):
            assert (
                CalendarLabels(january="Jänner", monday="Mo").month(date(2026, 1, 5))
                == "Jänner"
            )
            assert CalendarLabels(monday="Mo").weekday(date(2026, 1, 5)) == "Mo"
