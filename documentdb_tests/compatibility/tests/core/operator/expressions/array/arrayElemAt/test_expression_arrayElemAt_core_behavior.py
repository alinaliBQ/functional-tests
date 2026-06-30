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

# Property [Positive Index]: $arrayElemAt returns the element at the given positive index.
POSITIVE_INDEX_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="first_element",
        array=[1, 2, 3],
        idx=0,
        expected=1,
        msg="$arrayElemAt should return first element",
    ),
    ArrayElemAtTest(
        id="second_element",
        array=[1, 2, 3],
        idx=1,
        expected=2,
        msg="$arrayElemAt should return second element",
    ),
    ArrayElemAtTest(
        id="last_element",
        array=[1, 2, 3],
        idx=2,
        expected=3,
        msg="$arrayElemAt should return last element",
    ),
    ArrayElemAtTest(
        id="single_element_array",
        array=[42],
        idx=0,
        expected=42,
        msg="$arrayElemAt should return single element",
    ),
    ArrayElemAtTest(
        id="string_elements",
        array=["a", "b", "c"],
        idx=1,
        expected="b",
        msg="$arrayElemAt should return string element",
    ),
    ArrayElemAtTest(
        id="mixed_types",
        array=[1, "two", 3.0, True],
        idx=2,
        expected=3.0,
        msg="$arrayElemAt should return element from mixed-type array",
    ),
    ArrayElemAtTest(
        id="nested_array_element",
        array=[[1, 2], [3, 4]],
        idx=1,
        expected=[3, 4],
        msg="$arrayElemAt should return nested array element",
    ),
    ArrayElemAtTest(
        id="nested_object_element",
        array=[{"a": 1}, {"b": 2}],
        idx=0,
        expected={"a": 1},
        msg="$arrayElemAt should return nested object element",
    ),
    ArrayElemAtTest(
        id="null_element_in_array",
        array=[None, 1, 2],
        idx=0,
        expected=None,
        msg="$arrayElemAt should return null element",
    ),
    ArrayElemAtTest(
        id="bool_element",
        array=[True, False],
        idx=1,
        expected=False,
        msg="$arrayElemAt should return bool element",
    ),
]

# Property [Negative Index]: $arrayElemAt counts from the end of the array for a negative index.
NEGATIVE_INDEX_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="last_via_neg1",
        array=[1, 2, 3],
        idx=-1,
        expected=3,
        msg="$arrayElemAt should return last element via -1",
    ),
    ArrayElemAtTest(
        id="second_to_last",
        array=[1, 2, 3],
        idx=-2,
        expected=2,
        msg="$arrayElemAt should return second to last",
    ),
    ArrayElemAtTest(
        id="first_via_neg_len",
        array=[1, 2, 3],
        idx=-3,
        expected=1,
        msg="$arrayElemAt should return first via negative length",
    ),
    ArrayElemAtTest(
        id="single_element_neg1",
        array=[42],
        idx=-1,
        expected=42,
        msg="$arrayElemAt should return single element via -1",
    ),
]

# Property [Duplicate Values]: $arrayElemAt selects by position, ignoring duplicate elements.
DUPLICATE_VALUE_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="dup_first",
        array=[1, 1, 1],
        idx=0,
        expected=1,
        msg="$arrayElemAt is unaffected by duplicate elements at index 0",
    ),
    ArrayElemAtTest(
        id="dup_last",
        array=[1, 1, 1],
        idx=2,
        expected=1,
        msg="$arrayElemAt is unaffected by duplicate elements at the last index",
    ),
    ArrayElemAtTest(
        id="dup_neg",
        array=["a", "a", "b", "a"],
        idx=-1,
        expected="a",
        msg="$arrayElemAt is unaffected by duplicate elements at a negative index",
    ),
]

# Property [Large Array]: $arrayElemAt resolves positions within large arrays.
_LARGE_ARRAY_SIZE = 20_000
_LARGE_ARRAY = list(range(_LARGE_ARRAY_SIZE))

LARGE_ARRAY_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="large_array_first",
        array=_LARGE_ARRAY,
        idx=0,
        expected=0,
        msg="$arrayElemAt should return first in large array",
    ),
    ArrayElemAtTest(
        id="large_array_last",
        array=_LARGE_ARRAY,
        idx=_LARGE_ARRAY_SIZE - 1,
        expected=_LARGE_ARRAY_SIZE - 1,
        msg="$arrayElemAt should return last in large array",
    ),
    ArrayElemAtTest(
        id="large_array_neg1",
        array=_LARGE_ARRAY,
        idx=-1,
        expected=_LARGE_ARRAY_SIZE - 1,
        msg="$arrayElemAt should return last via -1 in large array",
    ),
    ArrayElemAtTest(
        id="large_array_middle",
        array=_LARGE_ARRAY,
        idx=_LARGE_ARRAY_SIZE // 2,
        expected=_LARGE_ARRAY_SIZE // 2,
        msg="$arrayElemAt should return middle in large array",
    ),
    ArrayElemAtTest(
        id="large_array_neg_middle",
        array=_LARGE_ARRAY,
        idx=-(_LARGE_ARRAY_SIZE // 4),
        expected=_LARGE_ARRAY_SIZE - _LARGE_ARRAY_SIZE // 4,
        msg="$arrayElemAt should return negative middle in large array",
    ),
]

ALL_TESTS = POSITIVE_INDEX_TESTS + NEGATIVE_INDEX_TESTS + DUPLICATE_VALUE_TESTS + LARGE_ARRAY_TESTS

TEST_SUBSET_FOR_LITERAL = [
    POSITIVE_INDEX_TESTS[0],
    NEGATIVE_INDEX_TESTS[0],
    LARGE_ARRAY_TESTS[0],
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
