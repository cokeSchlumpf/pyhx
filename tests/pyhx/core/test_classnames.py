from pyhx.core.primitives import classnames


class TestClassnames:
    def test_string(self):
        assert classnames("btn") == {"class_": "btn"}

    def test_given_classes_come_before_existing_class(self):
        assert classnames("btn", class_="primary") == {"class_": "btn primary"}

    def test_list_keeps_order(self):
        assert classnames(["c", "a", "b"]) == {"class_": "c a b"}

    def test_dict_includes_only_truthy(self):
        assert classnames({"active": True, "disabled": False}) == {"class_": "active"}

    def test_drops_duplicates_keeping_first_occurrence(self):
        result = classnames(["btn", "lg", "btn"], class_="lg extra btn")

        assert result == {"class_": "btn lg extra"}

    def test_keeps_other_attributes(self):
        assert classnames("btn", id="x") == {"id": "x", "class_": "btn"}

    def test_same_order_across_interpreters(self):
        # The old implementation joined a `set`, whose order depends on the
        # per-process hash seed; render in fresh interpreters to prove it's stable.
        import subprocess
        import sys

        code = (
            "from pyhx.core.primitives import classnames;"
            "print(classnames(['a','b','c','d','e'], class_='f g')['class_'])"
        )
        outputs = {
            subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                check=True,
                env={"PYTHONHASHSEED": str(seed)},
            ).stdout.strip()
            for seed in range(5)
        }

        assert outputs == {"a b c d e f g"}
