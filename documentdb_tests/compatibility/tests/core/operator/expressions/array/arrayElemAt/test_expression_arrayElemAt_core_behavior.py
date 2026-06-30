"""
Core behavior tests for $arrayElemAt expression.

Tests basic positive/negative index access, duplicate values, and large arrays.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.array_test_case import (  # noqa: E501
    ArrayTestClass,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Positive Index]: $arrayElemAt returns the element at the given positive index.
POSITIVE_INDEX_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="first_element",
        arrays=[1, 2, 3],
        idx=0,
        expected=1,
        msg="$arrayElemAt should return first element",
    ),
    ArrayTestClass(
        id="second_element",
        arrays=[1, 2, 3],
        idx=1,
        expected=2,
        msg="$arrayElemAt should return second element",
    ),
    ArrayTestClass(
        id="last_element",
        arrays=[1, 2, 3],
        idx=2,
        expected=3,
        msg="$arrayElemAt should return last element",
    ),
    ArrayTestClass(
        id="single_element_array",
        arrays=[42],
        idx=0,
        expected=42,
        msg="$arrayElemAt should return single element",
    ),
    ArrayTestClass(
        id="string_elements",
        arrays=["a", "b", "c"],
        idx=1,
        expected="b",
        msg="$arrayElemAt should return string element",
    ),
    ArrayTestClass(
        id="mixed_types",
        arrays=[1, "two", 3.0, True],
        idx=2,
        expected=3.0,
        msg="$arrayElemAt should return element from mixed-type array",
    ),
    ArrayTestClass(
        id="nested_array_element",
        arrays=[[1, 2], [3, 4]],
        idx=1,
        expected=[3, 4],
        msg="$arrayElemAt should return nested array element",
    ),
    ArrayTestClass(
        id="nested_object_element",
        arrays=[{"a": 1}, {"b": 2}],
        idx=0,
        expected={"a": 1},
        msg="$arrayElemAt should return nested object element",
    ),
    ArrayTestClass(
        id="null_element_in_array",
        arrays=[None, 1, 2],
        idx=0,
        expected=None,
        msg="$arrayElemAt should return null element",
    ),
    ArrayTestClass(
        id="bool_element",
        arrays=[True, False],
        idx=1,
        expected=False,
        msg="$arrayElemAt should return bool element",
    ),
]

# Property [Negative Index]: $arrayElemAt counts from the end of the array for a negative index.
NEGATIVE_INDEX_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="last_via_neg1",
        arrays=[1, 2, 3],
        idx=-1,
        expected=3,
        msg="$arrayElemAt should return last element via -1",
    ),
    ArrayTestClass(
        id="second_to_last",
        arrays=[1, 2, 3],
        idx=-2,
        expected=2,
        msg="$arrayElemAt should return second to last",
    ),
    ArrayTestClass(
        id="first_via_neg_len",
        arrays=[1, 2, 3],
        idx=-3,
        expected=1,
        msg="$arrayElemAt should return first via negative length",
    ),
    ArrayTestClass(
        id="single_element_neg1",
        arrays=[42],
        idx=-1,
        expected=42,
        msg="$arrayElemAt should return single element via -1",
    ),
]

# Property [Duplicate Values]: $arrayElemAt selects by position, ignoring duplicate elements.
DUPLICATE_VALUE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="dup_first",
        arrays=[1, 1, 1],
        idx=0,
        expected=1,
        msg="$arrayElemAt is unaffected by duplicate elements at index 0",
    ),
    ArrayTestClass(
        id="dup_last",
        arrays=[1, 1, 1],
        idx=2,
        expected=1,
        msg="$arrayElemAt is unaffected by duplicate elements at the last index",
    ),
    ArrayTestClass(
        id="dup_neg",
        arrays=["a", "a", "b", "a"],
        idx=-1,
        expected="a",
        msg="$arrayElemAt is unaffected by duplicate elements at a negative index",
    ),
]

# Property [Large Array]: $arrayElemAt resolves positions within large arrays.
_LARGE_ARRAY_SIZE = 20_000
_LARGE_ARRAY = list(range(_LARGE_ARRAY_SIZE))

LARGE_ARRAY_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="large_array_first",
        arrays=_LARGE_ARRAY,
        idx=0,
        expected=0,
        msg="$arrayElemAt should return first in large array",
    ),
    ArrayTestClass(
        id="large_array_last",
        arrays=_LARGE_ARRAY,
        idx=_LARGE_ARRAY_SIZE - 1,
        expected=_LARGE_ARRAY_SIZE - 1,
        msg="$arrayElemAt should return last in large array",
    ),
    ArrayTestClass(
        id="large_array_neg1",
        arrays=_LARGE_ARRAY,
        idx=-1,
        expected=_LARGE_ARRAY_SIZE - 1,
        msg="$arrayElemAt should return last via -1 in large array",
    ),
    ArrayTestClass(
        id="large_array_middle",
        arrays=_LARGE_ARRAY,
        idx=_LARGE_ARRAY_SIZE // 2,
        expected=_LARGE_ARRAY_SIZE // 2,
        msg="$arrayElemAt should return middle in large array",
    ),
    ArrayTestClass(
        id="large_array_neg_middle",
        arrays=_LARGE_ARRAY,
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
    result = execute_expression(collection, {"$arrayElemAt": [test.arrays, test.idx]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_arrayElemAt_insert(collection, test):
    """Test $arrayElemAt with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$arr", "$idx"]}, {"arr": test.arrays, "idx": test.idx}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
