from typing import Any, ClassVar

from pydantic import BaseModel


class TranslatedLabels(BaseModel):
    """Labels whose unset fields show their default text in the request language.

    A field left at ``None`` reads as its entry in ``_defaults`` (marked with
    ``_l``, so translated when read); a field set explicitly reads as set. Only the explicit values are stored and serialized, so labels kept
    in a component's serialized state carry no language and follow the
    language of each later request.
    """

    _defaults: ClassVar[dict[str, Any]] = {}

    def __getattribute__(self, name: str) -> Any:
        value = super().__getattribute__(name)
        if value is None and not name.startswith("_"):
            default = type(self)._defaults.get(name)
            if default is not None:
                return str(default)
        return value
