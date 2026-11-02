"""Icons in out-of-band and morph swaps (drawers, forms) are rendered like those of regular swaps."""

from pathlib import Path

PYHX_JS = Path("src/pyhx/static/js/pyhx.js").read_text()


def test_icons_are_rendered_after_regular_and_out_of_band_swaps():
    assert "document.addEventListener('htmx:afterSwap'" in PYHX_JS
    loaded = PYHX_JS.split("document.addEventListener('htmx:load'", 1)
    assert len(loaded) == 2 and "feather.replace()" in loaded[1].split("});", 1)[0]
