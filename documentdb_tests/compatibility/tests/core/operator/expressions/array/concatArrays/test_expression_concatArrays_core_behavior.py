"""
Core behavior tests for $concatArrays expression.

Tests concatenation of arrays with various element types, empty arrays,
single arrays, multiple arrays, nested arrays, duplicates, null
propagation, and large arrays.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.array.concatArrays.utils.concatArrays_common import (  # noqa: E501
    ConcatArraysTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Concatenation]: $concatArrays joins multiple arrays into one in argument order.
BASIC_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="two_int_arrays",
        arrays=[[1, 2], [3, 4]],
        expected=[1, 2, 3, 4],
        msg="$concatArrays should concatenate two int arrays",
    ),
    ConcatArraysTest(
        id="two_string_arrays",
        arrays=[["a", "b"], ["c", "d"]],
        expected=["a", "b", "c", "d"],
        msg="$concatArrays should concatenate two string arrays",
    ),
    ConcatArraysTest(
        id="three_arrays",
        arrays=[[1, 2], [3, 4], [5, 6]],
        expected=[1, 2, 3, 4, 5, 6],
        msg="$concatArrays should concatenate three arrays",
    ),
    ConcatArraysTest(
        id="mixed_type_elements",
        arrays=[[1, "two"], [True, None, {"a": 1}]],
        expected=[1, "two", True, None, {"a": 1}],
        msg="$concatArrays should concatenate arrays with mixed types",
    ),
]

# Property [Empty Arrays]: $concatArrays treats empty arrays as contributing no elements.
EMPTY_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="both_empty",
        arrays=[[], []],
        expected=[],
        msg="$concatArrays should return empty array for two empty arrays",
    ),
    ConcatArraysTest(
        id="first_empty",
        arrays=[[], [1, 2]],
        expected=[1, 2],
        msg="$concatArrays should return second array when first is empty",
    ),
    ConcatArraysTest(
        id="second_empty",
        arrays=[[1, 2], []],
        expected=[1, 2],
        msg="$concatArrays should return first array when second is empty",
    ),
    ConcatArraysTest(
        id="all_empty",
        arrays=[[], [], []],
        expected=[],
        msg="$concatArrays should return empty array for all empty inputs",
    ),
    ConcatArraysTest(
        id="no_arguments",
        arrays=[],
        expected=[],
        msg="$concatArrays should return an empty array for no arguments",
    ),
    ConcatArraysTest(
        id="empty_between_nonempty",
        arrays=[[1], [], [2]],
        expected=[1, 2],
        msg="$concatArrays should skip an empty array between non-empty arrays",
    ),
    ConcatArraysTest(
        id="multiple_empty",
        arrays=[[], [], [], []],
        expected=[],
        msg="$concatArrays should return an empty array for multiple empty arrays",
    ),
]

# Property [Single Array]: $concatArrays returns a single array argument unchanged.
SINGLE_ARRAY_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="single_array",
        arrays=[[1, 2, 3]],
        expected=[1, 2, 3],
        msg="$concatArrays should return the single array unchanged",
    ),
    ConcatArraysTest(
        id="single_empty_array",
        arrays=[[]],
        expected=[],
        msg="$concatArrays should return empty array for single empty input",
    ),
]

# Property [Top Level Only]: $concatArrays joins at the top level without flattening.
NESTED_ARRAY_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="nested_subarrays",
        arrays=[[[1, 2]], [[3, 4]]],
        expected=[[1, 2], [3, 4]],
        msg="$concatArrays should concatenate top-level, not flatten subarrays",
    ),
    ConcatArraysTest(
        id="mixed_nested",
        arrays=[[[1], "two"], [[3, 4]]],
        expected=[[1], "two", [3, 4]],
        msg="$concatArrays should concatenate mixed nested elements",
    ),
    ConcatArraysTest(
        id="deeply_nested",
        arrays=[[[[1]]], [[[2]]]],
        expected=[[[1]], [[2]]],
        msg="$concatArrays should preserve deeply nested array elements",
    ),
    ConcatArraysTest(
        id="empty_nested",
        arrays=[[[]], [[]]],
        expected=[[], []],
        msg="$concatArrays should preserve empty nested arrays as elements",
    ),
]

# Property [Duplicates]: $concatArrays keeps duplicate elements from the inputs.
DUPLICATE_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="duplicate_elements",
        arrays=[[1, 2, 3], [2, 3, 4]],
        expected=[1, 2, 3, 2, 3, 4],
        msg="$concatArrays should preserve duplicate elements across arrays",
    ),
    ConcatArraysTest(
        id="identical_arrays",
        arrays=[[1, 2], [1, 2]],
        expected=[1, 2, 1, 2],
        msg="$concatArrays should concatenate identical arrays",
    ),
]

# Property [Null Propagation]: $concatArrays returns null when any argument is null or missing.
NULL_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="null_first_arg",
        arrays=[None, [1, 2]],
        expected=None,
        msg="$concatArrays should return null when first argument is null",
    ),
    ConcatArraysTest(
        id="null_second_arg",
        arrays=[[1, 2], None],
        expected=None,
        msg="$concatArrays should return null when second argument is null",
    ),
    ConcatArraysTest(
        id="all_null",
        arrays=[None, None],
        expected=None,
        msg="$concatArrays should return null when all arguments are null",
    ),
    ConcatArraysTest(
        id="null_among_three",
        arrays=[[1], None, [2]],
        expected=None,
        msg="$concatArrays should return null when any argument is null",
    ),
    ConcatArraysTest(
        id="null_elements_in_arrays",
        arrays=[[1, None], [None, 2]],
        expected=[1, None, None, 2],
        msg="$concatArrays should preserve null elements within arrays",
    ),
]

# Property [Object Elements]: $concatArrays concatenates arrays of documents intact.
OBJECT_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="arrays_of_objects",
        arrays=[[{"a": 1}], [{"b": 2}]],
        expected=[{"a": 1}, {"b": 2}],
        msg="$concatArrays should concatenate arrays of objects",
    ),
    ConcatArraysTest(
        id="objects_with_arrays",
        arrays=[[{"items": [1, 2]}], [{"items": [3, 4]}]],
        expected=[{"items": [1, 2]}, {"items": [3, 4]}],
        msg="$concatArrays should preserve inner arrays in objects",
    ),
]

# Property [Large Arrays]: $concatArrays concatenates large arrays.
_LARGE_A = list(range(500))
_LARGE_B = list(range(500, 1000))

LARGE_ARRAY_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="large_arrays",
        arrays=[_LARGE_A, _LARGE_B],
        expected=list(range(1000)),
        msg="$concatArrays should concatenate large arrays",
    ),
    ConcatArraysTest(
        id="two_5000_arrays",
        arrays=[list(range(5000)), list(range(5000, 10000))],
        expected=list(range(10000)),
        msg="$concatArrays should concatenate two large arrays into 10,000 elements",
    ),
    ConcatArraysTest(
        id="one_large_one_small",
        arrays=[list(range(10000)), [10000]],
        expected=list(range(10001)),
        msg="$concatArrays should concatenate a large array and a small array",
    ),
    ConcatArraysTest(
        id="100_single_element_arrays",
        arrays=[[i] for i in range(100)],
        expected=list(range(100)),
        msg="$concatArrays should concatenate 100 single-element arrays",
    ),
]

# Property [Many Arrays]: $concatArrays concatenates many array arguments.
MANY_ARRAYS_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="five_arrays",
        arrays=[[1], [2], [3], [4], [5]],
        expected=[1, 2, 3, 4, 5],
        msg="$concatArrays should concatenate five arrays",
    ),
    ConcatArraysTest(
        id="ten_empty_arrays",
        arrays=[[] for _ in range(10)],
        expected=[],
        msg="$concatArrays should concatenate ten empty arrays",
    ),
    ConcatArraysTest(
        id="fifty_arrays",
        arrays=[[i] for i in range(50)],
        expected=list(range(50)),
        msg="$concatArrays should concatenate 50 arrays",
    ),
]

ALL_TESTS = (
    BASIC_TESTS
    + EMPTY_TESTS
    + SINGLE_ARRAY_TESTS
    + NESTED_ARRAY_TESTS
    + DUPLICATE_TESTS
    + NULL_TESTS
    + OBJECT_TESTS
    + LARGE_ARRAY_TESTS
    + MANY_ARRAYS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_concatArrays_insert(collection, test):
    """Test $concatArrays with values from inserted documents."""
    doc = {f"arr{i}": a for i, a in enumerate(test.arrays)}
    refs = [f"$arr{i}" for i in range(len(test.arrays))]
    result = execute_expression_with_insert(collection, {"$concatArrays": refs}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


TEST_SUBSET_FOR_LITERAL = [
    BASIC_TESTS[0],
    BASIC_TESTS[2],
    EMPTY_TESTS[0],
    SINGLE_ARRAY_TESTS[0],
    NESTED_ARRAY_TESTS[0],
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_concatArrays_literal(collection, test):
    """Test $concatArrays with literal values."""
    args = [{"$literal": a} if isinstance(a, list) else a for a in test.arrays]
    result = execute_expression(collection, {"$concatArrays": args})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
