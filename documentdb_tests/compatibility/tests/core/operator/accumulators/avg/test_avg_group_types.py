"""
Tests for $avg accumulator data type handling in $group context.

Covers type promotion rules, NaN/Infinity propagation, null/missing handling,
and non-numeric type ignoring when accumulating across documents.
"""

from __future__ import annotations

from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
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


# --- Type Promotion in $group ---


def test_avg_group_all_int32(collection):
    """Test $avg over int32 documents returns double."""
    result = _group_avg_values(collection, [10, 20, 30])
    assertSuccess(result, [{"_id": None, "avg": 20.0}], msg="int32 avg should return double")


def test_avg_group_all_int64(collection):
    """Test $avg over int64 documents returns double."""
    result = _group_avg_values(collection, [Int64(10), Int64(20), Int64(30)])
    assertSuccess(result, [{"_id": None, "avg": 20.0}], msg="int64 avg should return double")


def test_avg_group_all_double(collection):
    """Test $avg over double documents returns double."""
    result = _group_avg_values(collection, [10.0, 20.0, 30.0])
    assertSuccess(result, [{"_id": None, "avg": 20.0}], msg="double avg should return double")


def test_avg_group_all_decimal128(collection):
    """Test $avg over decimal128 documents returns decimal128."""
    result = _group_avg_values(collection, [Decimal128("10"), Decimal128("20"), Decimal128("30")])
    assertSuccess(
        result,
        [{"_id": None, "avg": Decimal128("20")}],
        msg="decimal128 avg should return decimal128",
    )


def test_avg_group_int32_and_int64(collection):
    """Test $avg over mixed int32/int64 returns double."""
    result = _group_avg_values(collection, [10, Int64(20)])
    assertSuccess(result, [{"_id": None, "avg": 15.0}], msg="int32+int64 avg should return double")


def test_avg_group_int32_and_double(collection):
    """Test $avg over mixed int32/double returns double."""
    result = _group_avg_values(collection, [10, 20.0])
    assertSuccess(result, [{"_id": None, "avg": 15.0}], msg="int32+double avg should return double")


def test_avg_group_int32_and_decimal128(collection):
    """Test $avg over mixed int32/decimal128 returns decimal128."""
    result = _group_avg_values(collection, [10, Decimal128("20")])
    assertSuccess(
        result,
        [{"_id": None, "avg": Decimal128("15")}],
        msg="int32+decimal128 avg should return decimal128",
    )


def test_avg_group_int64_and_decimal128(collection):
    """Test $avg over mixed int64/decimal128 returns decimal128."""
    result = _group_avg_values(collection, [Int64(10), Decimal128("20")])
    assertSuccess(
        result,
        [{"_id": None, "avg": Decimal128("15")}],
        msg="int64+decimal128 avg should return decimal128",
    )


def test_avg_group_double_and_decimal128(collection):
    """Test $avg over mixed double/decimal128 returns decimal128."""
    result = _group_avg_values(collection, [10.0, Decimal128("20")])
    assertSuccess(
        result,
        [{"_id": None, "avg": Decimal128("15")}],
        msg="double+decimal128 avg should return decimal128",
    )


def test_avg_group_all_four_types(collection):
    """Test $avg over all numeric types returns decimal128."""
    result = _group_avg_values(collection, [10, Int64(20), 30.0, Decimal128("40")])
    assertSuccess(
        result,
        [{"_id": None, "avg": Decimal128("25")}],
        msg="all four numeric types avg should return decimal128",
    )


def test_avg_group_fractional_result_from_int32(collection):
    """Test $avg of int32 values producing fractional result returns double."""
    result = _group_avg_values(collection, [1, 2])
    assertSuccess(
        result,
        [{"_id": None, "avg": 1.5}],
        msg="int32 avg producing fraction should return double",
    )


# --- NaN Propagation in $group ---


def test_avg_group_nan_propagates(collection):
    """Test $avg where one document has NaN propagates NaN."""
    result = _group_avg_values(collection, [10, float("nan"), 30])
    assertSuccessNaN(
        result,
        [{"_id": None, "avg": float("nan")}],
        msg="NaN in group should propagate to result",
    )


def test_avg_group_all_nan(collection):
    """Test $avg where all documents have NaN returns NaN."""
    result = _group_avg_values(collection, [float("nan"), float("nan")])
    assertSuccessNaN(
        result,
        [{"_id": None, "avg": float("nan")}],
        msg="All NaN in group should return NaN",
    )


def test_avg_group_decimal128_nan_propagates(collection):
    """Test $avg where one document has Decimal128 NaN propagates."""
    result = _group_avg_values(collection, [Decimal128("10"), DECIMAL128_NAN, Decimal128("30")])
    assertSuccessNaN(
        result,
        [{"_id": None, "avg": DECIMAL128_NAN}],
        msg="Decimal128 NaN in group should propagate",
    )


def test_avg_group_nan_dominates_infinity(collection):
    """Test $avg with NaN and Infinity returns NaN."""
    result = _group_avg_values(collection, [float("nan"), FLOAT_INFINITY])
    assertSuccessNaN(
        result,
        [{"_id": None, "avg": float("nan")}],
        msg="NaN should dominate Infinity in group",
    )


def test_avg_group_cross_type_nan_decimal(collection):
    """Test $avg with double NaN and Decimal128 value returns Decimal128 NaN."""
    result = _group_avg_values(collection, [float("nan"), Decimal128("5")])
    assertSuccessNaN(
        result,
        [{"_id": None, "avg": DECIMAL128_NAN}],
        msg="double NaN + Decimal128 should return Decimal128 NaN",
    )


# --- Infinity in $group ---


def test_avg_group_infinity(collection):
    """Test $avg where documents include Infinity returns Infinity."""
    result = _group_avg_values(collection, [FLOAT_INFINITY, 10])
    assertSuccess(
        result,
        [{"_id": None, "avg": FLOAT_INFINITY}],
        msg="Infinity in group should propagate",
    )


def test_avg_group_negative_infinity(collection):
    """Test $avg where documents include -Infinity returns -Infinity."""
    result = _group_avg_values(collection, [FLOAT_NEGATIVE_INFINITY, 10])
    assertSuccess(
        result,
        [{"_id": None, "avg": FLOAT_NEGATIVE_INFINITY}],
        msg="-Infinity in group should propagate",
    )


def test_avg_group_inf_neg_inf_cancel(collection):
    """Test $avg with Infinity and -Infinity documents returns NaN."""
    result = _group_avg_values(collection, [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY])
    assertSuccessNaN(
        result,
        [{"_id": None, "avg": float("nan")}],
        msg="Infinity + -Infinity in group should return NaN",
    )


def test_avg_group_decimal128_infinity(collection):
    """Test $avg with Decimal128 Infinity documents."""
    result = _group_avg_values(collection, [DECIMAL128_INFINITY, Decimal128("10")])
    assertSuccess(
        result,
        [{"_id": None, "avg": DECIMAL128_INFINITY}],
        msg="Decimal128 Infinity in group should propagate",
    )


def test_avg_group_decimal128_inf_neg_inf_cancel(collection):
    """Test $avg with Decimal128 Infinity and -Infinity returns Decimal128 NaN."""
    result = _group_avg_values(collection, [DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY])
    assertSuccessNaN(
        result,
        [{"_id": None, "avg": DECIMAL128_NAN}],
        msg="Decimal128 Inf + -Inf in group should return Decimal128 NaN",
    )


# --- Null / Missing in $group ---


def test_avg_group_all_null(collection):
    """Test $avg where all documents have null returns null."""
    result = _group_avg_values(collection, [None, None, None])
    assertSuccess(result, [{"_id": None, "avg": None}], msg="All null in group should return null")


def test_avg_group_some_null(collection):
    """Test $avg ignores null documents and averages the rest."""
    result = _group_avg_values(collection, [10, None, 30])
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="Null docs should be ignored, avg of 10 and 30 is 20",
    )


def test_avg_group_all_missing(collection):
    """Test $avg where all documents are missing the field returns null."""
    docs = [{"_id": i, "other": i} for i in range(3)]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": None, "avg": None}], msg="All missing fields should return null")


def test_avg_group_some_missing(collection):
    """Test $avg ignores documents with missing field."""
    collection.insert_many(
        [
            {"_id": 0, "v": 10},
            {"_id": 1},
            {"_id": 2, "v": 30},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="Missing field docs should be ignored",
    )


def test_avg_group_mix_null_missing_numeric(collection):
    """Test $avg with mix of null, missing, and numeric values."""
    collection.insert_many(
        [
            {"_id": 0, "v": 10},
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": 30},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="Only numeric values should contribute to average",
    )


# --- Non-numeric types ignored in $group ---


def test_avg_group_ignores_strings(collection):
    """Test $avg ignores string values in group."""
    result = _group_avg_values(collection, [10, "hello", 30])
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="String values should be ignored in group avg",
    )


def test_avg_group_ignores_booleans(collection):
    """Test $avg ignores boolean values in group."""
    result = _group_avg_values(collection, [10, True, False, 30])
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="Boolean values should be ignored in group avg",
    )


def test_avg_group_ignores_arrays(collection):
    """Test $avg ignores array values in group."""
    result = _group_avg_values(collection, [10, [1, 2, 3], 30])
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="Array values should be ignored in group avg",
    )


def test_avg_group_ignores_objects(collection):
    """Test $avg ignores embedded document values in group."""
    result = _group_avg_values(collection, [10, {"nested": 99}, 30])
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="Object values should be ignored in group avg",
    )


def test_avg_group_all_non_numeric(collection):
    """Test $avg returns null when all values are non-numeric."""
    result = _group_avg_values(collection, ["a", True, [1], {"x": 1}])
    assertSuccess(
        result,
        [{"_id": None, "avg": None}],
        msg="All non-numeric values should return null",
    )


def test_avg_group_boolean_not_numeric(collection):
    """Test $avg treats boolean as non-numeric (false != 0, true != 1)."""
    result = _group_avg_values(collection, [False, True])
    assertSuccess(
        result,
        [{"_id": None, "avg": None}],
        msg="Booleans should not be treated as 0/1 in avg",
    )


# --- Negative Zero in $group ---


def test_avg_group_negative_zero_double(collection):
    """Test $avg normalizes double negative zero to positive zero."""
    result = _group_avg_values(collection, [DOUBLE_NEGATIVE_ZERO, DOUBLE_NEGATIVE_ZERO])
    assertSuccess(
        result,
        [{"_id": None, "avg": DOUBLE_ZERO}],
        msg="Double -0.0 avg should normalize to 0.0",
    )


def test_avg_group_negative_zero_decimal128(collection):
    """Test $avg normalizes Decimal128 negative zero to positive zero."""
    result = _group_avg_values(collection, [DECIMAL128_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO])
    assertSuccess(
        result,
        [{"_id": None, "avg": DECIMAL128_ZERO}],
        msg="Decimal128 -0 avg should normalize to 0",
    )
