# tests/pyhx/components/test_button_glass.py
from typing import get_args

from pyhx.components.primitives.button import button
from pyhx.components.variants import Variant


def test_glass_is_a_variant():
    assert "glass" in get_args(Variant)


def test_button_glass_emits_class():
    html = str(button("Copy", variant="glass"))
    assert "hx-button--glass" in html


def test_glass_composes_with_appearance():
    html = str(button("Copy", variant="glass", appearance="primary"))
    assert "hx-button--glass" in html
    assert "hx-button--primary" in html
