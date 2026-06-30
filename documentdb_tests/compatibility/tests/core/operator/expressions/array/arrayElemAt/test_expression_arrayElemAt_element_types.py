"""
Element type preservation tests for $arrayElemAt expression.

Tests that $arrayElemAt correctly returns elements of all BSON types
including special float/Decimal128 values and boundary integers.
"""

import math
from datetime import datetime, timezone

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

# ---------------------------------------------------------------------------
# Success: various element BSON types stored in array
# ---------------------------------------------------------------------------
ELEMENT_TYPE_TESTS: list[ArrayElemAtTest] = [
    ArrayElemAtTest(
        id="int64_element",
        array=[Int64(99)],
        idx=0,
        expected=Int64(99),
        msg="Should return Int64 element",
    ),
    ArrayElemAtTest(
        id="decimal128_element",
        array=[Decimal128("1.5")],
        idx=0,
        expected=Decimal128("1.5"),
        msg="Should return Decimal128 element",
    ),
    ArrayElemAtTest(
        id="datetime_element",
        array=[datetime(2024, 1, 1, tzinfo=timezone.utc)],
        idx=0,
        expected=datetime(2024, 1, 1, tzinfo=timezone.utc),
        msg="Should return datetime element",
    ),
    ArrayElemAtTest(
        id="binary_element",
        array=[Binary(b"\x01\x02", 0)],
        idx=0,
        expected=b"\x01\x02",
        msg="Should return binary element",
    ),
    ArrayElemAtTest(
        id="regex_element",
        array=[Regex("^abc", "i")],
        idx=0,
        expected=Regex("^abc", "i"),
        msg="Should return regex element",
    ),
    ArrayElemAtTest(
        id="objectid_element",
        array=[ObjectId("000000000000000000000001")],
        idx=0,
        expected=ObjectId("000000000000000000000001"),
        msg="Should return ObjectId element",
    ),
    ArrayElemAtTest(
        id="minkey_element",
        array=[MinKey(), 1],
        idx=0,
        expected=MinKey(),
        msg="Should return MinKey element",
    ),
    ArrayElemAtTest(
        id="maxkey_element",
        array=[1, MaxKey()],
        idx=1,
        expected=MaxKey(),
        msg="Should return MaxKey element",
    ),
    ArrayElemAtTest(
        id="timestamp_element",
        array=[Timestamp(0, 0)],
        idx=0,
        expected=Timestamp(0, 0),
        msg="Should return Timestamp element",
    ),
    # Special float values
    ArrayElemAtTest(
        id="float_nan_element",
        array=[FLOAT_NAN, 1],
        idx=0,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN element",
    ),
    ArrayElemAtTest(
        id="float_infinity_element",
        array=[FLOAT_INFINITY, 1],
        idx=0,
        expected=FLOAT_INFINITY,
        msg="Should return Infinity element",
    ),
    ArrayElemAtTest(
        id="float_neg_infinity_element",
        array=[FLOAT_NEGATIVE_INFINITY, 1],
        idx=0,
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should return -Infinity element",
    ),
    # Special Decimal128 values
    ArrayElemAtTest(
        id="decimal128_nan_element",
        array=[DECIMAL128_NAN, 1],
        idx=0,
        expected=DECIMAL128_NAN,
        msg="Should return Decimal128 NaN element",
    ),
    ArrayElemAtTest(
        id="decimal128_infinity_element",
        array=[DECIMAL128_INFINITY, 1],
        idx=0,
        expected=DECIMAL128_INFINITY,
        msg="Should return Decimal128 Infinity element",
    ),
    ArrayElemAtTest(
        id="decimal128_neg_infinity_element",
        array=[DECIMAL128_NEGATIVE_INFINITY, 1],
        idx=0,
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="Should return Decimal128 -Infinity element",
    ),
    # Boundary integer values as elements
    ArrayElemAtTest(
        id="int32_max_element",
        array=[INT32_MAX, 0],
        idx=0,
        expected=INT32_MAX,
        msg="Should return INT32_MAX element",
    ),
    ArrayElemAtTest(
        id="int64_max_element",
        array=[INT64_MAX, 0],
        idx=0,
        expected=INT64_MAX,
        msg="Should return INT64_MAX element",
    ),
    # Mixed special values array
    ArrayElemAtTest(
        id="mixed_special_last",
        array=[INT32_MAX, FLOAT_INFINITY, DECIMAL128_NAN],
        idx=2,
        expected=DECIMAL128_NAN,
        msg="Should return element from mixed special values array",
    ),
]

TEST_SUBSET_FOR_LITERAL = [
    ELEMENT_TYPE_TESTS[0],  # int64_element
    ELEMENT_TYPE_TESTS[9],  # float_nan_element
    ELEMENT_TYPE_TESTS[-1],  # mixed_special_last
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayElemAt_literal(collection, test):
    """Test $arrayElemAt element type preservation with literal values."""
    result = execute_expression(collection, {"$arrayElemAt": [test.array, test.idx]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ELEMENT_TYPE_TESTS))
def test_arrayElemAt_insert(collection, test):
    """Test $arrayElemAt element type preservation with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$arr", "$idx"]}, {"arr": test.array, "idx": test.idx}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
