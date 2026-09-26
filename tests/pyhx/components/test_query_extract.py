from pyhx.components.data.sources.query import Query
from pyhx.components.data.sources.sort import SortOrder
from pyhx.components.data.sources.filter import Condition, StringEquals


def _query() -> Query:
    return Query(
        offset=20,
        limit=10,
        filter_mode="any",
        sort=[
            SortOrder(key="name", order="asc"),
            SortOrder(key="score", order="desc"),
        ],
        filter=[
            Condition(key="name", values=[StringEquals(value="ada")]),
            Condition(key="score", values=[StringEquals(value="9")]),
        ],
    )


def test_extract_partitions_sort_and_filter_by_key():
    remaining, extracted = _query().extract("score")
    assert [s.key for s in extracted.sort] == ["score"]
    assert [c.key for c in extracted.filter] == ["score"]
    assert [s.key for s in remaining.sort] == ["name"]
    assert [c.key for c in remaining.filter] == ["name"]


def test_remaining_keeps_paging_extracted_resets():
    remaining, extracted = _query().extract("score")
    assert (remaining.offset, remaining.limit) == (20, 10)
    assert (extracted.offset, extracted.limit) == (0, None)


def test_filter_mode_copied_to_both():
    remaining, extracted = _query().extract("score")
    assert remaining.filter_mode == "any"
    assert extracted.filter_mode == "any"


def test_results_are_deep_copies_independent_of_original():
    # Mutating returned copies must not bleed back into the original query.
    original = _query()
    remaining, extracted = original.extract("score")
    extracted.sort[0].order = "asc"
    remaining.sort[0].order = "desc"
    # original is untouched
    assert original.sort[0].order == "asc"   # name
    assert original.sort[1].order == "desc"  # score

    # Deep-copy independence for Condition filter entries: mutating a nested
    # FilterValue on the extracted copy must not affect the original.
    extracted.filter[0].values[0].value = "MUTATED"
    assert original.filter[1].values[0].value == "9"  # score condition (index 1) untouched


def test_unknown_keys_extract_nothing():
    original = _query()
    remaining, extracted = original.extract("missing")
    assert extracted.sort == []
    assert extracted.filter == []
    assert [s.key for s in remaining.sort] == ["name", "score"]
    assert [c.key for c in remaining.filter] == ["name", "score"]


def test_extracting_all_keys_empties_remaining():
    remaining, extracted = _query().extract("name", "score")
    assert remaining.sort == []
    assert remaining.filter == []
    assert [s.key for s in extracted.sort] == ["name", "score"]
    assert [c.key for c in extracted.filter] == ["name", "score"]
