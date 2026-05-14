"""
Tests for $avg accumulator overflow, boundary values, and decimal128 precision
in $group context.

These test the accumulator's running sum behavior across documents,
which differs from expression-context evaluation on a single array.
"""

from __future__ import annotations

from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.test_constants import (
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# --- Helpers ---


def _group_avg_values(collection, values):
    """Insert documents with given values and return $avg across all."""
    docs = [{"_id": i, "v": v} for i, v in enumerate(values)]
    collection.insert_many(docs)
    return execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "avg": {"$avg": "$v"}}},
            ],
            "cursor": {},
        },
    )


# --- Integer Boundary Values ---


def test_avg_group_int32_max_pair(collection):
    """Test $avg of two INT32_MAX values."""
    result = _group_avg_values(collection, [INT32_MAX, INT32_MAX])
    assertSuccess(
        result,
        [{"_id": None, "avg": float(INT32_MAX)}],
        msg="avg of two INT32_MAX should return INT32_MAX as double",
    )


def test_avg_group_int32_min_pair(collection):
    """Test $avg of two INT32_MIN values."""
    result = _group_avg_values(collection, [INT32_MIN, INT32_MIN])
    assertSuccess(
        result,
        [{"_id": None, "avg": float(INT32_MIN)}],
        msg="avg of two INT32_MIN should return INT32_MIN as double",
    )


def test_avg_group_int32_max_and_min(collection):
    """Test $avg of INT32_MAX and INT32_MIN."""
    result = _group_avg_values(collection, [INT32_MAX, INT32_MIN])
    # (2147483647 + -2147483648) / 2 = -0.5
    assertSuccess(
        result,
        [{"_id": None, "avg": -0.5}],
        msg="avg of INT32_MAX and INT32_MIN should be -0.5",
    )


def test_avg_group_int64_max_pair(collection):
    """Test $avg of two INT64_MAX values — potential precision loss in double."""
    result = _group_avg_values(collection, [INT64_MAX, INT64_MAX])
    assertSuccess(
        result,
        [{"_id": None, "avg": 9.223372036854776e18}],
        msg="avg of two INT64_MAX should handle overflow",
    )


def test_avg_group_int64_min_pair(collection):
    """Test $avg of two INT64_MIN values."""
    result = _group_avg_values(collection, [INT64_MIN, INT64_MIN])
    assertSuccess(
        result,
        [{"_id": None, "avg": -9.223372036854776e18}],
        msg="avg of two INT64_MIN should handle overflow",
    )


def test_avg_group_int64_max_and_one(collection):
    """Test $avg of INT64_MAX and 1."""
    result = _group_avg_values(collection, [INT64_MAX, Int64(1)])
    assertSuccess(
        result,
        [{"_id": None, "avg": 4.611686018427388e18}],
        msg="avg of INT64_MAX and 1",
    )


# --- Double Boundary Values ---


def test_avg_group_double_near_max_pair(collection):
    """Test $avg of two DOUBLE_NEAR_MAX values — sum overflows to inf."""
    result = _group_avg_values(collection, [DOUBLE_NEAR_MAX, DOUBLE_NEAR_MAX])
    assertSuccess(
        result,
        [{"_id": None, "avg": float("inf")}],
        msg="avg of two DOUBLE_NEAR_MAX overflows sum to inf",
    )


def test_avg_group_double_subnormal(collection):
    """Test $avg of subnormal double values."""
    result = _group_avg_values(collection, [DOUBLE_MIN_SUBNORMAL, DOUBLE_MIN_SUBNORMAL])
    assertSuccess(
        result,
        [{"_id": None, "avg": DOUBLE_MIN_SUBNORMAL}],
        msg="avg of two subnormal doubles should return subnormal",
    )


# --- Decimal128 Precision ---


def test_avg_group_decimal128_high_precision(collection):
    """Test $avg of decimal128 values requiring high precision."""
    result = _group_avg_values(
        collection,
        [
            Decimal128("1.000000000000000000000000000000001"),
            Decimal128("2.999999999999999999999999999999999"),
        ],
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": Decimal128("2.000000000000000000000000000000000")}],
        msg="decimal128 avg should preserve high precision",
    )


def test_avg_group_decimal128_large_exponent(collection):
    """Test $avg with decimal128 large exponent values."""
    result = _group_avg_values(collection, [DECIMAL128_LARGE_EXPONENT, DECIMAL128_LARGE_EXPONENT])
    assertSuccess(
        result,
        [{"_id": None, "avg": DECIMAL128_LARGE_EXPONENT}],
        msg="avg of two identical large exponent values should return same value",
    )


def test_avg_group_decimal128_small_exponent(collection):
    """Test $avg with decimal128 small exponent values."""
    result = _group_avg_values(collection, [DECIMAL128_SMALL_EXPONENT, DECIMAL128_SMALL_EXPONENT])
    assertSuccess(
        result,
        [{"_id": None, "avg": DECIMAL128_SMALL_EXPONENT}],
        msg="avg of two identical small exponent values should return same value",
    )


def test_avg_group_decimal128_max_and_min(collection):
    """Test $avg of DECIMAL128_MAX and DECIMAL128_MIN."""
    result = _group_avg_values(collection, [DECIMAL128_MAX, DECIMAL128_MIN])
    assertSuccess(
        result,
        [{"_id": None, "avg": Decimal128("0")}],
        msg="avg of DECIMAL128_MAX and DECIMAL128_MIN",
    )


def test_avg_group_decimal128_extreme_exponent_diff(collection):
    """Test $avg of values with extreme exponent difference."""
    result = _group_avg_values(collection, [Decimal128("1E+6144"), Decimal128("1")])
    assertSuccess(
        result,
        [{"_id": None, "avg": Decimal128("5.00000000000000000000000000000000E+6143")}],
        msg="avg with extreme exponent difference",
    )
