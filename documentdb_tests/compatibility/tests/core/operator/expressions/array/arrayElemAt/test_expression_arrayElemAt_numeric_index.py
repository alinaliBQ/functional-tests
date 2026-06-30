"""
Numeric index type tests for $arrayElemAt expression.

Tests various numeric types (Int64, double, Decimal128) and edge cases
like negative zero and Decimal128 scientific notation as index values.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.array_test_case import (  # noqa: E501
    ArrayTestClass,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_NEGATIVE_ZERO, DOUBLE_NEGATIVE_ZERO

# Property [Numeric Index Types]: $arrayElemAt accepts int32, int64, and integral double indexes.
NUMERIC_INDEX_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="int64_zero_index",
        arrays=[10, 20, 30],
        idx=Int64(0),
        expected=10,
        msg="$arrayElemAt should accept Int64 zero index",
    ),
    ArrayTestClass(
        id="int64_index",
        arrays=[10, 20, 30],
        idx=Int64(1),
        expected=20,
        msg="$arrayElemAt should accept Int64 index",
    ),
    ArrayTestClass(
        id="double_integral_index",
        arrays=[10, 20, 30],
        idx=2.0,
        expected=30,
        msg="$arrayElemAt should accept integral double index",
    ),
    ArrayTestClass(
        id="decimal128_integral_index",
        arrays=[10, 20, 30],
        idx=Decimal128("0"),
        expected=10,
        msg="$arrayElemAt should accept Decimal128 index",
    ),
    ArrayTestClass(
        id="int64_negative_index",
        arrays=[10, 20, 30],
        idx=Int64(-1),
        expected=30,
        msg="$arrayElemAt should accept negative Int64 index",
    ),
    ArrayTestClass(
        id="double_negative_integral",
        arrays=[10, 20, 30],
        idx=-2.0,
        expected=20,
        msg="$arrayElemAt should accept negative integral double index",
    ),
    ArrayTestClass(
        id="negative_zero_index",
        arrays=[10, 20, 30],
        idx=-0.0,
        expected=10,
        msg="$arrayElemAt should treat -0.0 as index 0",
    ),
    ArrayTestClass(
        id="decimal128_negative_zero_index",
        arrays=[10, 20, 30],
        idx=DECIMAL128_NEGATIVE_ZERO,
        expected=10,
        msg="$arrayElemAt should treat decimal128 -0 as index 0",
    ),
    ArrayTestClass(
        id="double_negative_zero_const",
        arrays=[10, 20, 30],
        idx=DOUBLE_NEGATIVE_ZERO,
        expected=10,
        msg="$arrayElemAt should treat double -0 const as index 0",
    ),
    ArrayTestClass(
        id="decimal128_trailing_zero",
        arrays=[10, 20, 30],
        idx=Decimal128("1.0"),
        expected=20,
        msg="$arrayElemAt should accept decimal128 with trailing zero",
    ),
    ArrayTestClass(
        id="decimal128_subnormal_zero",
        arrays=[10, 20, 30],
        idx=Decimal128("0E-6176"),
        expected=10,
        msg="$arrayElemAt should accept decimal128 subnormal zero",
    ),
    ArrayTestClass(
        id="decimal128_20E_neg1",
        arrays=[10, 20, 30],
        idx=Decimal128("20E-1"),
        expected=30,
        msg="$arrayElemAt should accept decimal128 20E-1 as index 2",
    ),
    ArrayTestClass(
        id="decimal128_0_2E1",
        arrays=[10, 20, 30],
        idx=Decimal128("0.2E1"),
        expected=30,
        msg="$arrayElemAt should accept decimal128 0.2E1 as index 2",
    ),
    ArrayTestClass(
        id="decimal128_2E0",
        arrays=[10, 20, 30],
        idx=Decimal128("2E0"),
        expected=30,
        msg="$arrayElemAt should accept decimal128 2E0 as index 2",
    ),
    ArrayTestClass(
        id="decimal128_10E_neg1",
        arrays=[10, 20, 30],
        idx=Decimal128("10E-1"),
        expected=20,
        msg="$arrayElemAt should accept decimal128 10E-1 as index 1",
    ),
    ArrayTestClass(
        id="decimal128_negative_integral_index",
        arrays=[10, 20, 30],
        idx=Decimal128("-1"),
        expected=30,
        msg="$arrayElemAt should accept negative Decimal128 integral index",
    ),
    ArrayTestClass(
        id="decimal128_neg_10E_neg1",
        arrays=[10, 20, 30],
        idx=Decimal128("-10E-1"),
        expected=30,
        msg="$arrayElemAt should accept decimal128 -10E-1 as index -1",
    ),
    ArrayTestClass(
        id="decimal128_0E_pos3",
        arrays=[10, 20, 30],
        idx=Decimal128("0E+3"),
        expected=10,
        msg="$arrayElemAt should accept decimal128 0E+3 as index 0",
    ),
    ArrayTestClass(
        id="decimal128_0E_neg3",
        arrays=[10, 20, 30],
        idx=Decimal128("0E-3"),
        expected=10,
        msg="$arrayElemAt should accept decimal128 0E-3 as index 0",
    ),
    ArrayTestClass(
        id="decimal128_1_00000",
        arrays=[10, 20, 30],
        idx=Decimal128("1.00000"),
        expected=20,
        msg="$arrayElemAt should accept decimal128 1.00000 as index 1",
    ),
]

TEST_SUBSET_FOR_LITERAL = [
    NUMERIC_INDEX_TESTS[0],
    NUMERIC_INDEX_TESTS[5],
    NUMERIC_INDEX_TESTS[-1],
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayElemAt_literal(collection, test):
    """Test $arrayElemAt numeric index types with literal values."""
    result = execute_expression(collection, {"$arrayElemAt": [test.arrays, test.idx]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(NUMERIC_INDEX_TESTS))
def test_arrayElemAt_insert(collection, test):
    """Test $arrayElemAt numeric index types with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$arr", "$idx"]}, {"arr": test.arrays, "idx": test.idx}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
