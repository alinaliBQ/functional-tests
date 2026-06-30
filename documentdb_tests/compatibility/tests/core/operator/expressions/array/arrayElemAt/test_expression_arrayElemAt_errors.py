"""
Error tests for $arrayElemAt expression.

Tests non-array first argument, non-numeric index, non-integral numeric index,
and wrong arity errors.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.array_test_case import (  # noqa: E501
    ArrayTestClass,
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

# Property [Array Type Strictness]: $arrayElemAt rejects a non-array first argument.
ARRAY_TYPE_ERROR_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="string_as_array",
        arrays="hello",
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject string as array",
    ),
    ArrayTestClass(
        id="int_as_array",
        arrays=42,
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject int as array",
    ),
    ArrayTestClass(
        id="bool_true_as_array",
        arrays=True,
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject bool true as array",
    ),
    ArrayTestClass(
        id="bool_false_as_array",
        arrays=False,
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject bool false as array",
    ),
    ArrayTestClass(
        id="object_as_array",
        arrays={"a": 1},
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject object as array",
    ),
    ArrayTestClass(
        id="double_as_array",
        arrays=3.14,
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject double as array",
    ),
    ArrayTestClass(
        id="decimal128_as_array",
        arrays=Decimal128("1"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject decimal128 as array",
    ),
    ArrayTestClass(
        id="int64_as_array",
        arrays=Int64(1),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject int64 as array",
    ),
    ArrayTestClass(
        id="binary_as_array",
        arrays=Binary(b"x", 0),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject binary as array",
    ),
    ArrayTestClass(
        id="datetime_as_array",
        arrays=datetime(2024, 1, 1, tzinfo=timezone.utc),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject datetime as array",
    ),
    ArrayTestClass(
        id="objectid_as_array",
        arrays=ObjectId(),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject objectid as array",
    ),
    ArrayTestClass(
        id="regex_as_array",
        arrays=Regex("x"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject regex as array",
    ),
    ArrayTestClass(
        id="maxkey_as_array",
        arrays=MaxKey(),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject maxkey as array",
    ),
    ArrayTestClass(
        id="minkey_as_array",
        arrays=MinKey(),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject minkey as array",
    ),
    ArrayTestClass(
        id="timestamp_as_array",
        arrays=Timestamp(0, 0),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject timestamp as array",
    ),
    ArrayTestClass(
        id="nan_as_array",
        arrays=float("nan"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject NaN as array",
    ),
    ArrayTestClass(
        id="inf_as_array",
        arrays=float("inf"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject Infinity as array",
    ),
    ArrayTestClass(
        id="decimal128_nan_as_array",
        arrays=Decimal128("NaN"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject Decimal128 NaN as array",
    ),
    ArrayTestClass(
        id="decimal128_inf_as_array",
        arrays=Decimal128("Infinity"),
        idx=0,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject Decimal128 Infinity as array",
    ),
]

# Property [Index Type Strictness]: $arrayElemAt rejects a non-numeric index.
INDEX_TYPE_ERROR_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="string_index",
        arrays=[1, 2],
        idx="0",
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject string index",
    ),
    ArrayTestClass(
        id="bool_true_index",
        arrays=[1, 2],
        idx=True,
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject bool true index",
    ),
    ArrayTestClass(
        id="bool_false_index",
        arrays=[1, 2],
        idx=False,
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject bool false index",
    ),
    ArrayTestClass(
        id="array_index",
        arrays=[1, 2],
        idx=[0],
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject array index",
    ),
    ArrayTestClass(
        id="object_index",
        arrays=[1, 2],
        idx={"a": 0},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject object index",
    ),
    ArrayTestClass(
        id="objectid_index",
        arrays=[1, 2],
        idx=ObjectId(),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject objectid index",
    ),
    ArrayTestClass(
        id="binary_index",
        arrays=[1, 2],
        idx=Binary(b"\x01", 0),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject binary index",
    ),
    ArrayTestClass(
        id="timestamp_index",
        arrays=[1, 2],
        idx=Timestamp(0, 0),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject timestamp index",
    ),
    ArrayTestClass(
        id="datetime_index",
        arrays=[1, 2],
        idx=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject datetime index",
    ),
    ArrayTestClass(
        id="maxkey_index",
        arrays=[1, 2],
        idx=MaxKey(),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject maxkey index",
    ),
    ArrayTestClass(
        id="minkey_index",
        arrays=[1, 2],
        idx=MinKey(),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject minkey index",
    ),
    ArrayTestClass(
        id="regex_index",
        arrays=[1, 2],
        idx=Regex("x"),
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject regex index",
    ),
]

# Property [Integral Index]: $arrayElemAt rejects a non-integral or out-of-range numeric index.
NON_INTEGRAL_INDEX_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="double_fractional_index",
        arrays=[1, 2, 3],
        idx=1.5,
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject fractional double index",
    ),
    ArrayTestClass(
        id="decimal128_fractional_index",
        arrays=[1, 2, 3],
        idx=Decimal128("0.5"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject fractional decimal128 index",
    ),
    ArrayTestClass(
        id="double_nan_index",
        arrays=[1, 2, 3],
        idx=float("nan"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject NaN index",
    ),
    ArrayTestClass(
        id="double_inf_index",
        arrays=[1, 2, 3],
        idx=float("inf"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject infinity index",
    ),
    ArrayTestClass(
        id="double_neg_inf_index",
        arrays=[1, 2, 3],
        idx=float("-inf"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject -infinity index",
    ),
    ArrayTestClass(
        id="decimal128_nan_index",
        arrays=[1, 2, 3],
        idx=Decimal128("NaN"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject decimal128 NaN index",
    ),
    ArrayTestClass(
        id="decimal128_inf_index",
        arrays=[1, 2, 3],
        idx=Decimal128("Infinity"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject decimal128 infinity index",
    ),
    ArrayTestClass(
        id="decimal128_neg_inf_index",
        arrays=[1, 2, 3],
        idx=Decimal128("-Infinity"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject decimal128 -infinity index",
    ),
    ArrayTestClass(
        id="int64_max_index",
        arrays=[1, 2, 3],
        idx=INT64_MAX,
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject INT64_MAX index",
    ),
    ArrayTestClass(
        id="int64_min_index",
        arrays=[1, 2, 3],
        idx=INT64_MIN,
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject INT64_MIN index",
    ),
    ArrayTestClass(
        id="large_double_index",
        arrays=[1, 2, 3],
        idx=1.0e18,
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject large double index",
    ),
    ArrayTestClass(
        id="large_neg_double_index",
        arrays=[1, 2, 3],
        idx=-1.0e18,
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject large negative double index",
    ),
    ArrayTestClass(
        id="decimal128_beyond_int32",
        arrays=[1, 2, 3],
        idx=Decimal128("2147483648"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject decimal128 beyond int32",
    ),
    ArrayTestClass(
        id="decimal128_huge",
        arrays=[1, 2, 3],
        idx=Decimal128("9223372036854775808"),
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject huge decimal128 index",
    ),
]

ALL_TESTS = ARRAY_TYPE_ERROR_TESTS + INDEX_TYPE_ERROR_TESTS + NON_INTEGRAL_INDEX_TESTS

TEST_SUBSET_FOR_LITERAL = [
    ARRAY_TYPE_ERROR_TESTS[0],
    INDEX_TYPE_ERROR_TESTS[0],
    NON_INTEGRAL_INDEX_TESTS[0],
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayElemAt_literal(collection, test):
    """Test $arrayElemAt error cases with literal values."""
    result = execute_expression(collection, {"$arrayElemAt": [test.arrays, test.idx]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_arrayElemAt_insert(collection, test):
    """Test $arrayElemAt error cases with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$arr", "$idx"]}, {"arr": test.arrays, "idx": test.idx}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Arity]: $arrayElemAt requires exactly two arguments.
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
