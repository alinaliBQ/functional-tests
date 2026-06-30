"""
Null and missing field behavior tests for $arrayElemAt expression.

Tests null propagation and missing field handling for array and index arguments.
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
from documentdb_tests.framework.test_constants import MISSING

# Property [Null Propagation]: $arrayElemAt returns null when the array or index argument is null.
NULL_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="null_array",
        array=None,
        idx=0,
        expected=None,
        msg="$arrayElemAt should return null for null array",
    ),
    ArrayElemAtTest(
        id="null_array_neg_idx",
        array=None,
        idx=-1,
        expected=None,
        msg="$arrayElemAt should return null for null array with negative index",
    ),
    ArrayElemAtTest(
        id="null_index",
        array=[1, 2],
        idx=None,
        expected=None,
        msg="$arrayElemAt should return null for null index",
    ),
    ArrayElemAtTest(
        id="both_null",
        array=None,
        idx=None,
        expected=None,
        msg="$arrayElemAt should return null when both null",
    ),
]

# Property [Missing Propagation]: $arrayElemAt returns null when the array or index is missing.
LITERAL_ONLY_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="missing_array",
        array=MISSING,
        idx=0,
        expected=None,
        msg="$arrayElemAt should return null for missing array",
    ),
    ArrayElemAtTest(
        id="missing_index",
        array=[1, 2, 3],
        idx=MISSING,
        expected=None,
        msg="$arrayElemAt should return null for missing index",
    ),
]

TEST_SUBSET_FOR_LITERAL = [
    NULL_TESTS[0],
    NULL_TESTS[2],
    NULL_TESTS[3],
] + LITERAL_ONLY_TESTS


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayElemAt_literal(collection, test):
    """Test $arrayElemAt null/missing with literal values."""
    result = execute_expression(collection, {"$arrayElemAt": [test.array, test.idx]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(NULL_TESTS))
def test_arrayElemAt_insert(collection, test):
    """Test $arrayElemAt null with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$arr", "$idx"]}, {"arr": test.array, "idx": test.idx}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
