"""Tests for $unwind stage — core unwinding behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Unwinding]: each element of the array at the path produces a
# separate output document with the array field replaced by that element,
# retaining all other fields, in original array order, without deduplication.
UNWIND_CORE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "core_basic_array",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": 2},
            {"_id": 1, "a": 3},
        ],
        msg="$unwind should produce one document per array element",
    ),
    StageTestCase(
        "core_retains_other_fields",
        docs=[{"_id": 1, "a": [10, 20], "x": "keep", "y": 99}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 10, "x": "keep", "y": 99},
            {"_id": 1, "a": 20, "x": "keep", "y": 99},
        ],
        msg="$unwind should retain all other fields from the input document",
    ),
    StageTestCase(
        "core_preserves_array_order",
        docs=[{"_id": 1, "a": ["c", "a", "b"]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": "c"},
            {"_id": 1, "a": "a"},
            {"_id": 1, "a": "b"},
        ],
        msg="$unwind should emit elements in their original array order",
    ),
    StageTestCase(
        "core_duplicates_not_deduplicated",
        docs=[{"_id": 1, "a": [5, 5, 5]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 5},
            {"_id": 1, "a": 5},
            {"_id": 1, "a": 5},
        ],
        msg="$unwind should produce one document per duplicate value without deduplication",
    ),
    StageTestCase(
        "core_mixed_type_array",
        docs=[{"_id": 1, "a": [1, "two", True, None, 3.5]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": "two"},
            {"_id": 1, "a": True},
            {"_id": 1, "a": None},
            {"_id": 1, "a": 3.5},
        ],
        msg="$unwind should preserve each element's type in a mixed-type array",
    ),
]

# Property [Shorthand Document Form Equivalence]: the shorthand
# { $unwind: "$field" } and document form { $unwind: { path: "$field" } }
# produce identical results for all input types.
UNWIND_SHORTHAND_EQUIV_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equiv_document_form_array",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": 2},
            {"_id": 1, "a": 3},
        ],
        msg="Document form should unwind array identically to shorthand form",
    ),
    StageTestCase(
        "equiv_document_form_scalar",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[{"_id": 1, "a": 42}],
        msg="Document form should pass through scalar identically to shorthand form",
    ),
    StageTestCase(
        "equiv_shorthand_null",
        docs=[{"_id": 1, "a": None}],
        pipeline=[{"$unwind": "$a"}],
        expected=[],
        msg="Shorthand form should drop null identically to document form",
    ),
    StageTestCase(
        "equiv_shorthand_missing",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": "$a"}],
        expected=[],
        msg="Shorthand form should drop missing identically to document form",
    ),
    StageTestCase(
        "equiv_shorthand_empty_array",
        docs=[{"_id": 1, "a": []}],
        pipeline=[{"$unwind": "$a"}],
        expected=[],
        msg="Shorthand form should drop empty array identically to document form",
    ),
]

UNWIND_CORE_ALL_TESTS = UNWIND_CORE_TESTS + UNWIND_SHORTHAND_EQUIV_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_CORE_ALL_TESTS))
def test_unwind_core(collection, test_case: StageTestCase):
    """Test $unwind core unwinding and shorthand equivalence."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


# Property [Field Ordering]: document field order from the input is preserved
# in output documents, and other array fields are not unwound.
@pytest.mark.aggregate
def test_unwind_field_ordering(collection):
    """Test $unwind preserves input document field order."""
    collection.insert_many([{"_id": 1, "z": 99, "a": [10, 20], "m": "mid", "b": "end"}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unwind": "$a"}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        expected=[["_id", "z", "a", "m", "b"]],
        transform=lambda docs: [list(d.keys()) for d in docs[:1]],
        msg="$unwind should preserve input document field order in output",
    )


@pytest.mark.aggregate
def test_unwind_other_arrays_not_unwound(collection):
    """Test $unwind does not unwind other array fields."""
    collection.insert_many([{"_id": 1, "a": [1, 2], "b": ["x", "y"], "c": [[3]]}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unwind": "$a"}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        expected=[
            {"_id": 1, "a": 1, "b": ["x", "y"], "c": [[3]]},
            {"_id": 1, "a": 2, "b": ["x", "y"], "c": [[3]]},
        ],
        msg="$unwind should not unwind other array fields in the document",
    )


# Property [Large Arrays]: arrays with many elements produce the correct
# number of output documents with sequential indices and no off-by-one errors.
@pytest.mark.aggregate
def test_unwind_large_array(collection):
    """Test $unwind with a large array."""
    collection.insert_many([{"_id": 1, "a": list(range(10_000))}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
            "cursor": {"batchSize": 10_000},
        },
    )
    assertSuccess(
        result,
        expected=True,
        transform=lambda docs: (
            len(docs) == 10_000 and all(d["a"] == i and d["idx"] == i for i, d in enumerate(docs))
        ),
        msg="$unwind should produce 10,000 output documents with sequential values and indices",
    )
