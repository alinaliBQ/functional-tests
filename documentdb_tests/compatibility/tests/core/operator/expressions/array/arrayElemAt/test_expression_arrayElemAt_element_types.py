"""
Element type preservation tests for $arrayElemAt expression.

Tests that $arrayElemAt correctly returns elements of all BSON types
including special float/Decimal128 values and boundary integers.
"""

import math
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
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT64_MAX,
)

# Property [Element Types]: $arrayElemAt returns the element with its original BSON type.
ELEMENT_TYPE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="int64_element",
        arrays=[Int64(99)],
        idx=0,
        expected=Int64(99),
        msg="$arrayElemAt should return Int64 element",
    ),
    ArrayTestClass(
        id="decimal128_element",
        arrays=[Decimal128("1.5")],
        idx=0,
        expected=Decimal128("1.5"),
        msg="$arrayElemAt should return Decimal128 element",
    ),
    ArrayTestClass(
        id="datetime_element",
        arrays=[datetime(2024, 1, 1, tzinfo=timezone.utc)],
        idx=0,
        expected=datetime(2024, 1, 1, tzinfo=timezone.utc),
        msg="$arrayElemAt should return datetime element",
    ),
    ArrayTestClass(
        id="binary_element",
        arrays=[Binary(b"\x01\x02", 0)],
        idx=0,
        expected=b"\x01\x02",
        msg="$arrayElemAt should return binary element",
    ),
    ArrayTestClass(
        id="regex_element",
        arrays=[Regex("^abc", "i")],
        idx=0,
        expected=Regex("^abc", "i"),
        msg="$arrayElemAt should return regex element",
    ),
    ArrayTestClass(
        id="objectid_element",
        arrays=[ObjectId("000000000000000000000001")],
        idx=0,
        expected=ObjectId("000000000000000000000001"),
        msg="$arrayElemAt should return ObjectId element",
    ),
    ArrayTestClass(
        id="minkey_element",
        arrays=[MinKey(), 1],
        idx=0,
        expected=MinKey(),
        msg="$arrayElemAt should return MinKey element",
    ),
    ArrayTestClass(
        id="maxkey_element",
        arrays=[1, MaxKey()],
        idx=1,
        expected=MaxKey(),
        msg="$arrayElemAt should return MaxKey element",
    ),
    ArrayTestClass(
        id="timestamp_element",
        arrays=[Timestamp(0, 0)],
        idx=0,
        expected=Timestamp(0, 0),
        msg="$arrayElemAt should return Timestamp element",
    ),
    ArrayTestClass(
        id="float_nan_element",
        arrays=[FLOAT_NAN, 1],
        idx=0,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$arrayElemAt should return NaN element",
    ),
    ArrayTestClass(
        id="float_infinity_element",
        arrays=[FLOAT_INFINITY, 1],
        idx=0,
        expected=FLOAT_INFINITY,
        msg="$arrayElemAt should return Infinity element",
    ),
    ArrayTestClass(
        id="float_neg_infinity_element",
        arrays=[FLOAT_NEGATIVE_INFINITY, 1],
        idx=0,
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$arrayElemAt should return -Infinity element",
    ),
    ArrayTestClass(
        id="decimal128_nan_element",
        arrays=[DECIMAL128_NAN, 1],
        idx=0,
        expected=DECIMAL128_NAN,
        msg="$arrayElemAt should return Decimal128 NaN element",
    ),
    ArrayTestClass(
        id="decimal128_infinity_element",
        arrays=[DECIMAL128_INFINITY, 1],
        idx=0,
        expected=DECIMAL128_INFINITY,
        msg="$arrayElemAt should return Decimal128 Infinity element",
    ),
    ArrayTestClass(
        id="decimal128_neg_infinity_element",
        arrays=[DECIMAL128_NEGATIVE_INFINITY, 1],
        idx=0,
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$arrayElemAt should return Decimal128 -Infinity element",
    ),
    ArrayTestClass(
        id="int32_max_element",
        arrays=[INT32_MAX, 0],
        idx=0,
        expected=INT32_MAX,
        msg="$arrayElemAt should return INT32_MAX element",
    ),
    ArrayTestClass(
        id="int64_max_element",
        arrays=[INT64_MAX, 0],
        idx=0,
        expected=INT64_MAX,
        msg="$arrayElemAt should return INT64_MAX element",
    ),
    ArrayTestClass(
        id="mixed_special_last",
        arrays=[INT32_MAX, FLOAT_INFINITY, DECIMAL128_NAN],
        idx=2,
        expected=DECIMAL128_NAN,
        msg="$arrayElemAt should return element from mixed special values array",
    ),
]

TEST_SUBSET_FOR_LITERAL = [
    ELEMENT_TYPE_TESTS[0],
    ELEMENT_TYPE_TESTS[9],
    ELEMENT_TYPE_TESTS[-1],
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayElemAt_literal(collection, test):
    """Test $arrayElemAt element type preservation with literal values."""
    result = execute_expression(collection, {"$arrayElemAt": [test.arrays, test.idx]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ELEMENT_TYPE_TESTS))
def test_arrayElemAt_insert(collection, test):
    """Test $arrayElemAt element type preservation with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$arr", "$idx"]}, {"arr": test.arrays, "idx": test.idx}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
