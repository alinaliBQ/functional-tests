"""
Error tests for $arrayElemAt expression.

Tests non-array first argument, non-numeric index, non-integral numeric index,
and wrong arity errors.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.arrayElemAt.utils.arrayElemAt_common import (  # noqa: E501
    ArrayElemAtTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
    ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
    ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_MAX, INT64_MIN

# ---------------------------------------------------------------------------
# Error: non-array first argument
# ---------------------------------------------------------------------------
ARRAY_TYPE_ERROR_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="string_as_array",
        array="hello",
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject string as array",
    ),
    ArrayElemAtTest(
        id="int_as_array",
        array=42,
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject int as array",
    ),
    ArrayElemAtTest(
        id="bool_true_as_array",
        array=True,
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject bool true as array",
    ),
    ArrayElemAtTest(
        id="bool_false_as_array",
        array=False,
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject bool false as array",
    ),
    ArrayElemAtTest(
        id="object_as_array",
        array={"a": 1},
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject object as array",
    ),
    ArrayElemAtTest(
        id="double_as_array",
        array=3.14,
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject double as array",
    ),
    ArrayElemAtTest(
        id="decimal128_as_array",
        array=Decimal128("1"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject decimal128 as array",
    ),
    ArrayElemAtTest(
        id="int64_as_array",
        array=Int64(1),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject int64 as array",
    ),
    ArrayElemAtTest(
        id="binary_as_array",
        array=Binary(b"x", 0),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject binary as array",
    ),
    ArrayElemAtTest(
        id="datetime_as_array",
        array=datetime(2024, 1, 1),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject datetime as array",
    ),
    ArrayElemAtTest(
        id="objectid_as_array",
        array=ObjectId(),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject objectid as array",
    ),
    ArrayElemAtTest(
        id="regex_as_array",
        array=Regex("x"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject regex as array",
    ),
    ArrayElemAtTest(
        id="maxkey_as_array",
        array=MaxKey(),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject maxkey as array",
    ),
    ArrayElemAtTest(
        id="minkey_as_array",
        array=MinKey(),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject minkey as array",
    ),
    ArrayElemAtTest(
        id="timestamp_as_array",
        array=Timestamp(0, 0),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject timestamp as array",
    ),
    ArrayElemAtTest(
        id="nan_as_array",
        array=float("nan"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject NaN as array",
    ),
    ArrayElemAtTest(
        id="inf_as_array",
        array=float("inf"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject Infinity as array",
    ),
    ArrayElemAtTest(
        id="decimal128_nan_as_array",
        array=Decimal128("NaN"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject Decimal128 NaN as array",
    ),
    ArrayElemAtTest(
        id="decimal128_inf_as_array",
        array=Decimal128("Infinity"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="Should reject Decimal128 Infinity as array",
    ),
]

# ---------------------------------------------------------------------------
# Error: non-numeric index
# ---------------------------------------------------------------------------
INDEX_TYPE_ERROR_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="string_index",
        array=[1, 2],
        idx="0",
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject string index",
    ),
    ArrayElemAtTest(
        id="bool_true_index",
        array=[1, 2],
        idx=True,
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject bool true index",
    ),
    ArrayElemAtTest(
        id="bool_false_index",
        array=[1, 2],
        idx=False,
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject bool false index",
    ),
    ArrayElemAtTest(
        id="array_index",
        array=[1, 2],
        idx=[0],
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject array index",
    ),
    ArrayElemAtTest(
        id="object_index",
        array=[1, 2],
        idx={"a": 0},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject object index",
    ),
    ArrayElemAtTest(
        id="objectid_index",
        array=[1, 2],
        idx=ObjectId(),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject objectid index",
    ),
    ArrayElemAtTest(
        id="binary_index",
        array=[1, 2],
        idx=Binary(b"\x01", 0),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject binary index",
    ),
    ArrayElemAtTest(
        id="timestamp_index",
        array=[1, 2],
        idx=Timestamp(0, 0),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject timestamp index",
    ),
    ArrayElemAtTest(
        id="datetime_index",
        array=[1, 2],
        idx=datetime(2024, 1, 1),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject datetime index",
    ),
    ArrayElemAtTest(
        id="maxkey_index",
        array=[1, 2],
        idx=MaxKey(),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject maxkey index",
    ),
    ArrayElemAtTest(
        id="minkey_index",
        array=[1, 2],
        idx=MinKey(),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject minkey index",
    ),
    ArrayElemAtTest(
        id="regex_index",
        array=[1, 2],
        idx=Regex("x"),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="Should reject regex index",
    ),
]

# ---------------------------------------------------------------------------
# Error: non-integral numeric index
# ---------------------------------------------------------------------------
NON_INTEGRAL_INDEX_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="double_fractional_index",
        array=[1, 2, 3],
        idx=1.5,
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject fractional double index",
    ),
    ArrayElemAtTest(
        id="decimal128_fractional_index",
        array=[1, 2, 3],
        idx=Decimal128("0.5"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject fractional decimal128 index",
    ),
    ArrayElemAtTest(
        id="double_nan_index",
        array=[1, 2, 3],
        idx=float("nan"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject NaN index",
    ),
    ArrayElemAtTest(
        id="double_inf_index",
        array=[1, 2, 3],
        idx=float("inf"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject infinity index",
    ),
    ArrayElemAtTest(
        id="double_neg_inf_index",
        array=[1, 2, 3],
        idx=float("-inf"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject -infinity index",
    ),
    ArrayElemAtTest(
        id="decimal128_nan_index",
        array=[1, 2, 3],
        idx=Decimal128("NaN"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject decimal128 NaN index",
    ),
    ArrayElemAtTest(
        id="decimal128_inf_index",
        array=[1, 2, 3],
        idx=Decimal128("Infinity"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject decimal128 infinity index",
    ),
    ArrayElemAtTest(
        id="decimal128_neg_inf_index",
        array=[1, 2, 3],
        idx=Decimal128("-Infinity"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject decimal128 -infinity index",
    ),
    ArrayElemAtTest(
        id="int64_max_index",
        array=[1, 2, 3],
        idx=INT64_MAX,
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject INT64_MAX index",
    ),
    ArrayElemAtTest(
        id="int64_min_index",
        array=[1, 2, 3],
        idx=INT64_MIN,
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject INT64_MIN index",
    ),
    ArrayElemAtTest(
        id="large_double_index",
        array=[1, 2, 3],
        idx=1.0e18,
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject large double index",
    ),
    ArrayElemAtTest(
        id="large_neg_double_index",
        array=[1, 2, 3],
        idx=-1.0e18,
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject large negative double index",
    ),
    ArrayElemAtTest(
        id="decimal128_beyond_int32",
        array=[1, 2, 3],
        idx=Decimal128("2147483648"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject decimal128 beyond int32",
    ),
    ArrayElemAtTest(
        id="decimal128_huge",
        array=[1, 2, 3],
        idx=Decimal128("9223372036854775808"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject huge decimal128 index",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_TESTS = ARRAY_TYPE_ERROR_TESTS + INDEX_TYPE_ERROR_TESTS + NON_INTEGRAL_INDEX_TESTS

TEST_SUBSET_FOR_LITERAL = [
    ARRAY_TYPE_ERROR_TESTS[0],  # string_as_array
    INDEX_TYPE_ERROR_TESTS[0],  # string_index
    NON_INTEGRAL_INDEX_TESTS[0],  # double_fractional_index
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayElemAt_literal(collection, test):
    """Test $arrayElemAt error cases with literal values."""
    result = execute_expression(collection, {"$arrayElemAt": [test.array, test.idx]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_arrayElemAt_insert(collection, test):
    """Test $arrayElemAt error cases with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$arr", "$idx"]}, {"arr": test.array, "idx": test.idx}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# ---------------------------------------------------------------------------
# Error: wrong arity
# ---------------------------------------------------------------------------
ARITY_ERROR_TESTS = [
    pytest.param({"$arrayElemAt": [[1, 2, 3]]}, id="one_arg"),
    pytest.param({"$arrayElemAt": [[1, 2, 3], 0, 1]}, id="three_args"),
    pytest.param({"$arrayElemAt": []}, id="zero_args"),
    pytest.param({"$arrayElemAt": [[[1, 2, 3], 0]]}, id="nested_array_of_args"),
]


@pytest.mark.parametrize("expr", ARITY_ERROR_TESTS)
def test_arrayElemAt_syntax_error(collection, expr):
    """Test $arrayElemAt errors with wrong number of arguments."""
    result = execute_expression(collection, expr)
    assert_expression_result(result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR)
