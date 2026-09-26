from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_STATIC = _ROOT / "src" / "pyhx" / "static"


def test_code_stylesheets_imported():
    aggregator = (_STATIC / "css" / "pyhx.css").read_text(encoding="utf-8")
    assert "components/layout/code.css" in aggregator
    assert "components/layout/code-highlight.css" in aggregator
    for name in ("code.css", "code-highlight.css"):
        assert (_STATIC / "css" / "pyhx" / "components" / "layout" / name).is_file()


def test_code_js_exists_and_is_included():
    js = _STATIC / "js" / "pyhx.code.js"
    assert js.is_file()
    skeleton = (_ROOT / "src" / "pyhx" / "core" / "templates" / "skeleton.py").read_text(
        encoding="utf-8"
    )
    assert "pyhx.code.js" in skeleton
    assert "pyhx.example.js" not in skeleton


def test_old_example_js_removed():
    assert not (_STATIC / "js" / "pyhx.example.js").exists()
