"""Slider with one or more thumbs for picking values on a scale.

``slider(name, ...)`` renders the complete control: a track on a scale from
``min`` to ``max`` (snapping to ``step``), one thumb per value and one hidden
input per thumb, so the slider submits like any other form control::

    slider("opacity", value=40)
    slider("period", min=2020, max=2030, value=(2022, 2026))
    slider(
        "gradient",
        value=[
            SliderThumb(0, max=30, label="Start"),
            SliderThumb(50, min=20, max=80, label="Middle"),
            SliderThumb(100, min=70, label="End"),
        ],
    )

All hidden inputs share ``name``: one thumb submits a single value, two or
more submit a list (``Annotated[list[float], Form()]`` on the server), in
thumb order. Thumbs never cross — each neighbour acts as an additional bound.

The visual elements are also exposed as sub-builders (``slider.container``,
``slider.track``, ``slider.range``, ``slider.thumb``) for composing a static
slider by hand. Dragging, clicking the track and the keyboard are wired up
client-side by ``pyhx.slider.js``.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from itertools import pairwise

import htpy as y

from pyhx.core.primitives import classnames, merge_styles

from ..view_model import Pct
from ._element import _KxSimpleElementFactory

_TRACK_START = Pct(0.0)
_TRACK_END = Pct(1.0)


@dataclass(frozen=True)
class SliderThumb:
    """One thumb of a :data:`slider`: its value plus optional bounds.

    Attributes
    ----------
    value : float
        The thumb's position on the slider's scale.
    min : float | None
        Lowest value the thumb may take. ``None`` falls back to the scale's
        ``min``; otherwise it must lie within the scale.
    max : float | None
        Highest value the thumb may take. ``None`` falls back to the scale's
        ``max``; otherwise it must lie within the scale.
    label : str | None
        Accessible name of the thumb — set it as soon as a slider has more
        than one thumb (e.g. ``"Start"`` / ``"End"``).
    """

    value: float
    min: float | None = None
    max: float | None = None
    label: str | None = None


type SliderValue = float | SliderThumb | Sequence[float | SliderThumb]


@dataclass(frozen=True)
class _ResolvedThumb:
    """A thumb with its value snapped to the scale and its own bounds resolved."""

    value: float
    min: float
    max: float
    label: str | None


class _Slider:
    """Public entry point for the slider primitive (the :data:`slider`
    singleton).

    Call it to render the complete control — see :meth:`__call__`. The visual
    elements are exposed as sub-builders for composing a slider by hand:

    * ``slider.container(...)[...]`` / ``slider.container[...]`` — the root
      element.
    * ``slider.track[...]`` — the rail; positions of its children are
      relative to it.
    * ``slider.range(...)`` — the filled section of the track.
    * ``slider.thumb(...)`` — a draggable handle.
    """

    def __init__(self) -> None:
        self.container = _KxSimpleElementFactory("hx-slider")
        self.track = _KxSimpleElementFactory("hx-slider__track")

    def __call__(
        self,
        name: str,
        value: SliderValue | None = None,
        *,
        min: float = 0,
        max: float = 100,
        step: float = 1,
        disabled: bool = False,
        **kwargs: y.Attribute,
    ) -> y.Node:
        """Render the slider.

        Args:
            name: Form field name shared by every thumb's hidden input.
            value: One value per thumb — a number or a :class:`SliderThumb`
                (for per-thumb bounds and labels), or a sequence of them for
                several thumbs. ``None`` renders a single thumb at ``min``.
                Values are snapped to ``step`` and clamped to their bounds;
                they must be in ascending order.
            min: Start of the scale.
            max: End of the scale.
            step: Distance between selectable values, counted from ``min``.
            disabled: Make the thumbs inert. The hidden inputs keep
                submitting, so a disabled slider doesn't drop its value on
                save.
            **kwargs: Extra HTML attributes forwarded to the outer ``<div>``
                (e.g. ``aria_invalid`` / ``aria_describedby`` set by
                ``form_field``).

        Raises:
            ValueError: If the scale is empty, ``step`` isn't positive, a
                thumb's bounds lie outside the scale or are empty, or the
                values are not in ascending order.
        """
        if not min < max:
            raise ValueError(f"slider scale is empty: min={min!r}, max={max!r}")
        if not step > 0:
            raise ValueError(f"slider step must be positive: {step!r}")

        thumbs = [
            self._resolve(thumb, min, max, step) for thumb in self._thumbs(value, min)
        ]
        for prev, nxt in pairwise(thumbs):
            if nxt.value < prev.value:
                raise ValueError(
                    f"slider values must be ascending: {prev.value!r} > {nxt.value!r}"
                )

        def pct(v: float) -> Pct:
            return Pct.clamp((v - min) / (max - min))

        if disabled:
            kwargs["aria_disabled"] = "true"

        last = len(thumbs) - 1
        return self.container(
            data_slider=True,
            data_slider_min=_format(min),
            data_slider_max=_format(max),
            data_slider_step=_format(step),
            **kwargs,
        )[
            self.track[
                self._range(thumbs, pct),
                (
                    self.thumb(
                        pct(t.value),
                        aria_label=t.label,
                        # ARIA bounds include the neighbours: the range a thumb
                        # can actually move in right now.
                        aria_valuemin=_format(thumbs[i - 1].value if i else t.min),
                        aria_valuemax=_format(
                            thumbs[i + 1].value if i < last else t.max
                        ),
                        aria_valuenow=_format(t.value),
                        aria_disabled="true" if disabled else None,
                        tabindex="-1" if disabled else "0",
                        data_slider_index=str(i),
                        data_slider_min=_format(t.min),
                        data_slider_max=_format(t.max),
                    )
                    for i, t in enumerate(thumbs)
                ),
            ],
            (
                y.input(
                    type="hidden",
                    name=name,
                    value=_format(t.value),
                    data_slider_index=str(i),
                )
                for i, t in enumerate(thumbs)
            ),
        ]

    def range(
        self,
        start: Pct = _TRACK_START,
        end: Pct = _TRACK_END,
        **kwargs: y.Attribute,
    ) -> y.Node:
        """Render the filled section of the track between two positions.

        Args:
            start: Where the range begins along the track.
            end: Where the range ends along the track.
            **kwargs: Extra HTML attributes forwarded to the ``<span>``.
        """
        return y.span(
            **classnames(
                "hx-slider__range",
                **merge_styles(
                    {
                        "--hx-slider--start": str(start),
                        "--hx-slider--end": str(end),
                    },
                    **kwargs,
                ),
            )
        )

    def thumb(
        self,
        position: Pct,
        *,
        aria_label: str | None = None,
        **kwargs: y.Attribute,
    ) -> y.Node:
        """Render a handle at a position along the track.

        The ARIA value attributes default to the position on a 0–100 scale;
        pass ``aria_valuemin`` / ``aria_valuemax`` / ``aria_valuenow`` to
        report real values instead.

        Args:
            position: Where the thumb sits along the track.
            aria_label: Accessible name, needed as soon as a slider has more
                than one thumb (e.g. ``"Start"`` / ``"End"``).
            **kwargs: Extra HTML attributes forwarded to the ``<span>``.
        """
        attrs: dict[str, y.Attribute] = {
            "role": "slider",
            "tabindex": "0",
            "aria_label": aria_label,
            "aria_valuemin": "0",
            "aria_valuemax": "100",
            "aria_valuenow": f"{position.percent:g}",
            **kwargs,
        }
        return y.span(
            **classnames(
                "hx-slider__thumb",
                **merge_styles({"--hx-slider--position": str(position)}, **attrs),
            ),
        )

    def _range(
        self, thumbs: list[_ResolvedThumb], pct: Callable[[float], Pct]
    ) -> y.Node:
        """The filled range: from the scale start to a single thumb, between
        two thumbs, none for three or more."""
        if len(thumbs) == 1:
            return self.range(end=pct(thumbs[0].value))
        if len(thumbs) == 2:
            return self.range(start=pct(thumbs[0].value), end=pct(thumbs[1].value))
        return None

    @staticmethod
    def _thumbs(value: SliderValue | None, scale_min: float) -> list[SliderThumb]:
        """Normalise ``value`` into one :class:`SliderThumb` per thumb."""
        if value is None:
            return [SliderThumb(scale_min)]
        if isinstance(value, SliderThumb):
            return [value]
        if isinstance(value, int | float):
            return [SliderThumb(value)]
        thumbs = [v if isinstance(v, SliderThumb) else SliderThumb(v) for v in value]
        if not thumbs:
            raise ValueError("slider needs at least one value")
        return thumbs

    @staticmethod
    def _resolve(
        thumb: SliderThumb, scale_min: float, scale_max: float, step: float
    ) -> _ResolvedThumb:
        """Resolve a thumb's bounds against the scale, then snap its value to
        the step grid and clamp it into those bounds."""
        lo = scale_min if thumb.min is None else thumb.min
        hi = scale_max if thumb.max is None else thumb.max
        if not scale_min <= lo <= hi <= scale_max:
            raise ValueError(
                f"slider thumb bounds [{lo!r}, {hi!r}] must be non-empty and lie "
                f"within the scale [{scale_min!r}, {scale_max!r}]"
            )
        return _ResolvedThumb(
            value=_clamp(_snap(thumb.value, scale_min, step), lo, hi),
            min=lo,
            max=hi,
            label=thumb.label,
        )


def _snap(value: float, origin: float, step: float) -> float:
    """Round ``value`` to the nearest multiple of ``step`` counted from
    ``origin`` — in decimal arithmetic, so fractional steps like ``0.1`` don't
    accumulate float noise (``0.30000000000000004``)."""
    d_origin, d_step = Decimal(str(origin)), Decimal(str(step))
    steps = ((Decimal(str(value)) - d_origin) / d_step).to_integral_value()
    return float(d_origin + steps * d_step)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(value, hi))


def _format(value: float) -> str:
    """A value as submitted / reported: ``2026`` rather than ``2026.0``."""
    return str(int(value)) if float(value).is_integer() else str(value)


#: The slider primitive. Import as ``from pyhx.components import slider`` (or
#: via ``c.slider``) and call ``slider(name, ...)``.
slider = _Slider()
