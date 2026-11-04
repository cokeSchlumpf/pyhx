from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

import pytest
from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_core import PydanticCustomError

from pyhx.core.primitives import field_error, validation_error
from pyhx.i18n import use_locale, validation_message
from pyhx.i18n import _catalogs


@pytest.fixture(autouse=True)
def real_catalogs():
    _catalogs.clear_cache()
    yield
    _catalogs.clear_cache()


class Case(BaseModel):
    number: Annotated[
        str, Field(min_length=3, max_length=8, pattern=r"^[A-Z0-9-]+$")
    ] = "AB-1"
    name: Annotated[str, Field(min_length=1)] = "x"
    pages: Annotated[int, Field(ge=1, le=1000)] = 1
    amount: Annotated[Decimal, Field(gt=0, max_digits=6, decimal_places=2)] = Decimal(1)
    opened: date = date(2026, 1, 1)
    kind: Literal["a", "b"] = "a"
    tags: Annotated[list[str], Field(max_length=2)] = []
    note: str = ""

    @field_validator("note")
    @classmethod
    def _no_secret(cls, value: str) -> str:
        if value == "secret":
            raise ValueError("Notes must not be secret.")
        return value


def message(**values) -> str:
    with pytest.raises(ValidationError) as exc:
        Case.model_validate(values)
    return validation_message(exc.value.errors()[0])


def required() -> str:
    class Required(BaseModel):
        name: str

    with pytest.raises(ValidationError) as exc:
        Required.model_validate({})
    return validation_message(exc.value.errors()[0])


class TestEnglish:
    def test_builtin_errors_get_sentences_with_their_limits(self):
        assert required() == "This field is required."
        assert message(number="A") == "Enter at least 3 characters."
        assert message(name="") == "This field is required."
        assert message(number="ABCDEFGHIJ") == "Enter at most 8 characters."
        assert message(number="ab") == "Enter at least 3 characters."
        assert message(number="abc") == "The value doesn't have the expected format."
        assert message(pages="many") == "Enter a whole number."
        assert message(pages=0) == "Enter a value of at least 1."
        assert message(pages=1001) == "Enter a value of at most 1,000."
        assert message(amount=0) == "Enter a value greater than 0."
        assert message(amount="1.234") == "Enter at most 2 decimal places."
        assert message(opened="yesterday") == "Enter a valid date."
        assert message(kind="c") == "Choose one of the offered values."
        assert message(tags=["a", "b", "c"]) == "Choose at most 2 entries."

    def test_a_validator_message_comes_without_pydantics_prefix(self):
        assert message(note="secret") == "Notes must not be secret."

    def test_other_errors_keep_their_message(self):
        error = validation_error(
            field_error("name", "Takes {n} letters.", type="too_few", n=4)
        )
        assert validation_message(error.errors()[0]) == "Takes 4 letters."
        custom = ValidationError.from_exception_data(
            "X",
            [
                {
                    "type": PydanticCustomError("taken", "This name is taken."),
                    "loc": ("name",),
                    "input": None,
                }
            ],
        )
        assert validation_message(custom.errors()[0]) == "This name is taken."


class TestGerman:
    def test_builtin_errors_in_the_request_language_with_formatted_limits(self):
        with use_locale("de"):
            assert required() == "Dieses Feld ist erforderlich."
            assert message(number="A") == "Geben Sie mindestens 3 Zeichen ein."
            assert message(pages=1001) == "Geben Sie höchstens 1.000 ein."
            assert message(opened="yesterday") == "Geben Sie ein gültiges Datum ein."

    def test_every_offered_language_translates_the_required_field(self):
        texts = set()
        for locale in ("de", "it", "fr"):
            with use_locale(locale):
                texts.add(required())
        assert "This field is required." not in texts
        assert len(texts) == 3
