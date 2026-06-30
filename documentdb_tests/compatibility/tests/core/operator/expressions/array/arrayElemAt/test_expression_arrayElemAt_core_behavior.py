"""
Core behavior tests for $arrayElemAt expression.

Tests basic positive/negative index access, duplicate values, and large arrays.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.array.arrayElemAt.utils.arrayElemAt_common import (  # noqa: E501
    ArrayElemAtTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Success: basic positive index access
# ---------------------------------------------------------------------------
POSITIVE_INDEX_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="first_element", array=[1, 2, 3], idx=0, expected=1, msg="Should return first element"
    ),
    ArrayElemAtTest(
        id="second_element", array=[1, 2, 3], idx=1, expected=2, msg="Should return second element"
    ),
    ArrayElemAtTest(
        id="last_element", array=[1, 2, 3], idx=2, expected=3, msg="Should return last element"
    ),
    ArrayElemAtTest(
        id="single_element_array",
        array=[42],
        idx=0,
        expected=42,
        msg="Should return single element",
    ),
    ArrayElemAtTest(
        id="string_elements",
        array=["a", "b", "c"],
        idx=1,
        expected="b",
        msg="Should return string element",
    ),
    ArrayElemAtTest(
        id="mixed_types",
        array=[1, "two", 3.0, True],
        idx=2,
        expected=3.0,
        msg="Should return element from mixed-type array",
    ),
    ArrayElemAtTest(
        id="nested_array_element",
        array=[[1, 2], [3, 4]],
        idx=1,
        expected=[3, 4],
        msg="Should return nested array element",
    ),
    ArrayElemAtTest(
        id="nested_object_element",
        array=[{"a": 1}, {"b": 2}],
        idx=0,
        expected={"a": 1},
        msg="Should return nested object element",
    ),
    ArrayElemAtTest(
        id="null_element_in_array",
        array=[None, 1, 2],
        idx=0,
        expected=None,
        msg="Should return null element",
    ),
    ArrayElemAtTest(
        id="bool_element",
        array=[True, False],
        idx=1,
        expected=False,
        msg="Should return bool element",
    ),
]

# ---------------------------------------------------------------------------
# Success: negative index access
# ---------------------------------------------------------------------------
NEGATIVE_INDEX_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="last_via_neg1",
        array=[1, 2, 3],
        idx=-1,
        expected=3,
        msg="Should return last element via -1",
    ),
    ArrayElemAtTest(
        id="second_to_last", array=[1, 2, 3], idx=-2, expected=2, msg="Should return second to last"
    ),
    ArrayElemAtTest(
        id="first_via_neg_len",
        array=[1, 2, 3],
        idx=-3,
        expected=1,
        msg="Should return first via negative length",
    ),
    ArrayElemAtTest(
        id="single_element_neg1",
        array=[42],
        idx=-1,
        expected=42,
        msg="Should return single element via -1",
    ),
]

# ---------------------------------------------------------------------------
# Success: duplicate values in array — index-based access unaffected
# ---------------------------------------------------------------------------
DUPLICATE_VALUE_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="dup_first",
        array=[1, 1, 1],
        idx=0,
        expected=1,
        msg="Duplicates don't affect index 0",
    ),
    ArrayElemAtTest(
        id="dup_last",
        array=[1, 1, 1],
        idx=2,
        expected=1,
        msg="Duplicates don't affect last index",
    ),
    ArrayElemAtTest(
        id="dup_neg",
        array=["a", "a", "b", "a"],
        idx=-1,
        expected="a",
        msg="Duplicates don't affect negative index",
    ),
]

# ---------------------------------------------------------------------------
# Success: large array
# ---------------------------------------------------------------------------
_LARGE_ARRAY_SIZE = 20_000
_LARGE_ARRAY = list(range(_LARGE_ARRAY_SIZE))

LARGE_ARRAY_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="large_array_first",
        array=_LARGE_ARRAY,
        idx=0,
        expected=0,
        msg="Should return first in large array",
    ),
    ArrayElemAtTest(
        id="large_array_last",
        array=_LARGE_ARRAY,
        idx=_LARGE_ARRAY_SIZE - 1,
        expected=_LARGE_ARRAY_SIZE - 1,
        msg="Should return last in large array",
    ),
    ArrayElemAtTest(
        id="large_array_neg1",
        array=_LARGE_ARRAY,
        idx=-1,
        expected=_LARGE_ARRAY_SIZE - 1,
        msg="Should return last via -1 in large array",
    ),
    ArrayElemAtTest(
        id="large_array_middle",
        array=_LARGE_ARRAY,
        idx=_LARGE_ARRAY_SIZE // 2,
        expected=_LARGE_ARRAY_SIZE // 2,
        msg="Should return middle in large array",
    ),
    ArrayElemAtTest(
        id="large_array_neg_middle",
        array=_LARGE_ARRAY,
        idx=-(_LARGE_ARRAY_SIZE // 4),
        expected=_LARGE_ARRAY_SIZE - _LARGE_ARRAY_SIZE // 4,
        msg="Should return negative middle in large array",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_TESTS = POSITIVE_INDEX_TESTS + NEGATIVE_INDEX_TESTS + DUPLICATE_VALUE_TESTS + LARGE_ARRAY_TESTS

TEST_SUBSET_FOR_LITERAL = [
    POSITIVE_INDEX_TESTS[0],  # first_element
    NEGATIVE_INDEX_TESTS[0],  # last_via_neg1
    LARGE_ARRAY_TESTS[0],  # large_array_first
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayElemAt_literal(collection, test):
    """Test $arrayElemAt with literal values."""
    result = execute_expression(collection, {"$arrayElemAt": [test.array, test.idx]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_arrayElemAt_insert(collection, test):
    """Test $arrayElemAt with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$arr", "$idx"]}, {"arr": test.array, "idx": test.idx}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
