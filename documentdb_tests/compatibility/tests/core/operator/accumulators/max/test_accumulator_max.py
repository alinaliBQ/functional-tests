"""Tests for $max accumulator in $group, $bucket, and $bucketAuto contexts."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.accumulators.max.utils import (
    AccumulatorMaxTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    MODULO_BY_ZERO_V2_ERROR,
    MODULO_ZERO_REMAINDER_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    DATE_Y2K,
    DATE_YEAR_1,
    DATE_YEAR_9999,
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    TS_EPOCH,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

STAGES = ["group", "bucket", "bucketAuto"]


def _execute_accumulator(collection, test_case: AccumulatorMaxTestCase, stage: str):
    """Insert docs and run $max through the specified stage."""
    if test_case.docs:
        collection.insert_many(test_case.docs)

    if stage == "group":
        pipeline = [
            {"$group": {"_id": None, "result": {"$max": test_case.accumulator}}},
            {"$project": {"_id": 0, "result": 1}},
        ]
    elif stage == "bucket":
        pipeline = [
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": test_case.accumulator}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ]
    else:
        pipeline = [
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": test_case.accumulator}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ]

    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )


def _execute_accumulator_with_type(collection, test_case: AccumulatorMaxTestCase, stage: str):
    """Insert docs and run $max with a $type projection through the specified stage."""
    if test_case.docs:
        collection.insert_many(test_case.docs)

    if stage == "group":
        pipeline = [
            {"$group": {"_id": None, "result": {"$max": test_case.accumulator}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ]
    elif stage == "bucket":
        pipeline = [
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": test_case.accumulator}},
                }
            },
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ]
    else:
        pipeline = [
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": test_case.accumulator}},
                }
            },
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ]

    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )


# ---------------------------------------------------------------------------
# 1. Null and Missing Handling
# ---------------------------------------------------------------------------

# Property [Null and Missing Ignored]: null values, missing fields, and
# $$REMOVE are excluded from the max computation. When no non-null/non-missing
# values remain, the result is null.
MAX_NULL_MISSING_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "null_all_null",
        docs=[{"v": None}, {"v": None}],
        accumulator="$v",
        expected=None,
        msg="$max should return null when all values are null",
    ),
    AccumulatorMaxTestCase(
        "null_all_missing",
        docs=[{"x": 1}, {"x": 2}],
        accumulator="$v",
        expected=None,
        msg="$max should return null when all values reference missing fields",
    ),
    AccumulatorMaxTestCase(
        "null_and_missing_all",
        docs=[{"v": None}, {"x": 1}],
        accumulator="$v",
        expected=None,
        msg="$max should return null when values are mix of null and missing",
    ),
    AccumulatorMaxTestCase(
        "null_single_among_values",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        accumulator="$v",
        expected=5,
        msg="$max should exclude null and return max of remaining numerics",
    ),
    AccumulatorMaxTestCase(
        "null_missing_single_among_values",
        docs=[{"x": 1}, {"v": 5}, {"v": 3}],
        accumulator="$v",
        expected=5,
        msg="$max should exclude missing and return max of remaining numerics",
    ),
    AccumulatorMaxTestCase(
        "null_and_missing_among_values",
        docs=[{"v": None}, {"x": 1}, {"v": 10}],
        accumulator="$v",
        expected=10,
        msg="$max should exclude both null and missing, return max of numerics",
    ),
    AccumulatorMaxTestCase(
        "null_one_value",
        docs=[{"v": None}, {"x": 1}, {"v": 7}],
        accumulator="$v",
        expected=7,
        msg="$max should return the only numeric value when others are null/missing",
    ),
    AccumulatorMaxTestCase(
        "null_two_docs",
        docs=[{"v": None}, {"x": 1}],
        accumulator="$v",
        expected=None,
        msg="$max should return null when one doc is null and one is missing",
    ),
    AccumulatorMaxTestCase(
        "null_remove_via_cond",
        docs=[{"v": -1}, {"v": 5}, {"v": 3}],
        accumulator={"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]},
        expected=5,
        msg="$max should treat $$REMOVE as missing and exclude it",
    ),
    AccumulatorMaxTestCase(
        "null_remove_all",
        docs=[{"v": -1}, {"v": -2}],
        accumulator={"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]},
        expected=None,
        msg="$max should return null when all docs produce $$REMOVE",
    ),
    AccumulatorMaxTestCase(
        "null_remove_with_values",
        docs=[{"v": -1}, {"v": 10}, {"v": -3}, {"v": 7}],
        accumulator={"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]},
        expected=10,
        msg="$max should return max of remaining values after $$REMOVE exclusion",
    ),
]


# ---------------------------------------------------------------------------
# 2. BSON Comparison Order (Cross-Type)
# ---------------------------------------------------------------------------

# Property [BSON Comparison Order]: $max compares values using BSON comparison
# order when documents contain different types.
# BSON order: MinKey < Number < String < Object < Array < Binary < ObjectId
# < Boolean < Date < Timestamp < Regex < Code < MaxKey.
MAX_BSON_ORDER_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "bson_minkey_vs_number",
        docs=[{"v": MinKey()}, {"v": 5}],
        accumulator="$v",
        expected=5,
        msg="$max should pick number over MinKey per BSON order",
    ),
    AccumulatorMaxTestCase(
        "bson_number_vs_string",
        docs=[{"v": 100}, {"v": "hello"}],
        accumulator="$v",
        expected="hello",
        msg="$max should pick string over number per BSON order",
    ),
    AccumulatorMaxTestCase(
        "bson_string_vs_object",
        docs=[{"v": "zzz"}, {"v": {"a": 1}}],
        accumulator="$v",
        expected={"a": 1},
        msg="$max should pick object over string per BSON order",
    ),
    AccumulatorMaxTestCase(
        "bson_object_vs_array",
        docs=[{"v": {"z": 99}}, {"v": [1]}],
        accumulator="$v",
        expected=[1],
        msg="$max should pick array over object per BSON order",
    ),
    AccumulatorMaxTestCase(
        "bson_array_vs_binary",
        docs=[{"v": [999]}, {"v": Binary(b"\x00")}],
        accumulator="$v",
        expected=b"\x00",
        msg="$max should pick binary over array per BSON order",
    ),
    AccumulatorMaxTestCase(
        "bson_binary_vs_objectid",
        docs=[{"v": Binary(b"\xff" * 100)}, {"v": ObjectId("000000000000000000000001")}],
        accumulator="$v",
        expected=ObjectId("000000000000000000000001"),
        msg="$max should pick ObjectId over binary per BSON order",
    ),
    AccumulatorMaxTestCase(
        "bson_objectid_vs_boolean",
        docs=[{"v": ObjectId("ffffffffffffffffffffffff")}, {"v": False}],
        accumulator="$v",
        expected=False,
        msg="$max should pick boolean over ObjectId per BSON order",
    ),
    AccumulatorMaxTestCase(
        "bson_boolean_vs_datetime",
        docs=[{"v": True}, {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        accumulator="$v",
        expected=datetime(2020, 1, 1, tzinfo=timezone.utc),
        msg="$max should pick datetime over boolean per BSON order",
    ),
    AccumulatorMaxTestCase(
        "bson_datetime_vs_timestamp",
        docs=[
            {"v": datetime(9999, 12, 31, tzinfo=timezone.utc)},
            {"v": Timestamp(0, 1)},
        ],
        accumulator="$v",
        expected=Timestamp(0, 1),
        msg="$max should pick timestamp over datetime per BSON order",
    ),
    AccumulatorMaxTestCase(
        "bson_timestamp_vs_regex",
        docs=[{"v": Timestamp(4294967295, 4294967295)}, {"v": Regex("a")}],
        accumulator="$v",
        expected=Regex("a"),
        msg="$max should pick regex over timestamp per BSON order",
    ),
    # NOTE: bson_regex_vs_code, bson_code_vs_maxkey, and bson_minkey_vs_maxkey
    # are stage-dependent and tested separately below (see MAX_BSON_ORDER_*
    # lists and test_accumulator_max_bson_order_group_bucket /
    # test_accumulator_max_bson_order_bucket_auto).
    AccumulatorMaxTestCase(
        "bson_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        accumulator="$v",
        expected=False,
        msg="$max should pick False over 0 (boolean > number in BSON order)",
    ),
    AccumulatorMaxTestCase(
        "bson_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        accumulator="$v",
        expected=True,
        msg="$max should pick True over 1 (boolean > number in BSON order)",
    ),
    AccumulatorMaxTestCase(
        "bson_string_before_number",
        docs=[{"v": "a"}, {"v": 999999}],
        accumulator="$v",
        expected="a",
        msg="$max should pick string over number regardless of insertion order",
    ),
    # NOTE: bson_maxkey_before_minkey is stage-dependent and tested separately
    # below (see MAX_BSON_ORDER_* lists).
]


# ---------------------------------------------------------------------------
# 3. Within-Type Ordering
# ---------------------------------------------------------------------------

# Property [Numeric Comparison]: values of the same numeric type are compared
# numerically; cross-type numeric comparisons use numeric value.

# 3a. Numeric comparison
MAX_NUMERIC_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "numeric_int32_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        accumulator="$v",
        expected=30,
        msg="$max should return the largest int32 value",
    ),
    AccumulatorMaxTestCase(
        "numeric_int64_basic",
        docs=[{"v": Int64(100)}, {"v": Int64(300)}, {"v": Int64(200)}],
        accumulator="$v",
        expected=Int64(300),
        msg="$max should return the largest int64 value",
    ),
    AccumulatorMaxTestCase(
        "numeric_double_basic",
        docs=[{"v": 1.5}, {"v": 3.5}, {"v": 2.5}],
        accumulator="$v",
        expected=3.5,
        msg="$max should return the largest double value",
    ),
    AccumulatorMaxTestCase(
        "numeric_decimal128_basic",
        docs=[{"v": Decimal128("1.5")}, {"v": Decimal128("3.5")}, {"v": Decimal128("2.5")}],
        accumulator="$v",
        expected=Decimal128("3.5"),
        msg="$max should return the largest Decimal128 value",
    ),
    AccumulatorMaxTestCase(
        "numeric_cross_int32_int64",
        docs=[{"v": 5}, {"v": Int64(10)}],
        accumulator="$v",
        expected=Int64(10),
        msg="$max should pick Int64(10) over int32(5) numerically",
    ),
    AccumulatorMaxTestCase(
        "numeric_cross_int32_double",
        docs=[{"v": 5}, {"v": 10.5}],
        accumulator="$v",
        expected=10.5,
        msg="$max should pick double(10.5) over int32(5) numerically",
    ),
    AccumulatorMaxTestCase(
        "numeric_cross_int32_decimal",
        docs=[{"v": 5}, {"v": Decimal128("10")}],
        accumulator="$v",
        expected=Decimal128("10"),
        msg="$max should pick Decimal128(10) over int32(5) numerically",
    ),
    AccumulatorMaxTestCase(
        "numeric_cross_int64_double",
        docs=[{"v": Int64(5)}, {"v": 10.5}],
        accumulator="$v",
        expected=10.5,
        msg="$max should pick double(10.5) over Int64(5) numerically",
    ),
    AccumulatorMaxTestCase(
        "numeric_cross_int64_decimal",
        docs=[{"v": Int64(5)}, {"v": Decimal128("10")}],
        accumulator="$v",
        expected=Decimal128("10"),
        msg="$max should pick Decimal128(10) over Int64(5) numerically",
    ),
    AccumulatorMaxTestCase(
        "numeric_cross_double_decimal",
        docs=[{"v": 5.5}, {"v": Decimal128("10")}],
        accumulator="$v",
        expected=Decimal128("10"),
        msg="$max should pick Decimal128(10) over double(5.5) numerically",
    ),
    AccumulatorMaxTestCase(
        "numeric_all_four_types",
        docs=[{"v": 1}, {"v": Int64(2)}, {"v": 3.0}, {"v": Decimal128("4")}],
        accumulator="$v",
        expected=Decimal128("4"),
        msg="$max should return the numerically largest across all four numeric types",
    ),
    AccumulatorMaxTestCase(
        "numeric_ieee754_rounding",
        docs=[{"v": 3.14}, {"v": Decimal128("3.14")}],
        accumulator="$v",
        expected=3.14,
        msg="$max should pick double 3.14 over Decimal128 3.14 (IEEE 754 rounding)",
    ),
]

# 3b. String comparison
MAX_STRING_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "string_basic",
        docs=[{"v": "abc"}, {"v": "abd"}],
        accumulator="$v",
        expected="abd",
        msg="$max should pick the lexicographically larger string",
    ),
    AccumulatorMaxTestCase(
        "string_case",
        docs=[{"v": "a"}, {"v": "A"}],
        accumulator="$v",
        expected="a",
        msg="$max should pick lowercase 'a' over uppercase 'A' (byte order)",
    ),
    AccumulatorMaxTestCase(
        "string_digits_lexicographic",
        docs=[{"v": "9"}, {"v": "10"}],
        accumulator="$v",
        expected="9",
        msg="$max should compare strings lexicographically, not numerically",
    ),
    AccumulatorMaxTestCase(
        "string_prefix",
        docs=[{"v": "abc"}, {"v": "abcd"}],
        accumulator="$v",
        expected="abcd",
        msg="$max should pick the longer string when prefix matches",
    ),
    AccumulatorMaxTestCase(
        "string_empty_vs_nonempty",
        docs=[{"v": ""}, {"v": "a"}],
        accumulator="$v",
        expected="a",
        msg="$max should pick non-empty string over empty string",
    ),
    AccumulatorMaxTestCase(
        "string_null_byte",
        docs=[{"v": "a\x00b"}, {"v": "a\x00c"}],
        accumulator="$v",
        expected="a\x00c",
        msg="$max should compare strings containing null bytes correctly",
    ),
]

# 3c. Boolean ordering
MAX_BOOLEAN_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "boolean_true_vs_false",
        docs=[{"v": True}, {"v": False}],
        accumulator="$v",
        expected=True,
        msg="$max should pick True over False",
    ),
    AccumulatorMaxTestCase(
        "boolean_false_vs_true",
        docs=[{"v": False}, {"v": True}],
        accumulator="$v",
        expected=True,
        msg="$max should pick True over False regardless of insertion order",
    ),
]

# 3d. Datetime ordering
MAX_DATETIME_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "datetime_chronological",
        docs=[
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2023, 6, 15, tzinfo=timezone.utc)},
        ],
        accumulator="$v",
        expected=datetime(2023, 6, 15, tzinfo=timezone.utc),
        msg="$max should pick the later datetime",
    ),
    AccumulatorMaxTestCase(
        "datetime_pre_epoch_vs_epoch",
        docs=[{"v": DATE_BEFORE_EPOCH}, {"v": DATE_EPOCH}],
        accumulator="$v",
        expected=DATE_EPOCH,
        msg="$max should pick epoch over pre-epoch datetime",
    ),
    AccumulatorMaxTestCase(
        "datetime_epoch_vs_future",
        docs=[{"v": DATE_EPOCH}, {"v": DATE_Y2K}],
        accumulator="$v",
        expected=DATE_Y2K,
        msg="$max should pick Y2K over epoch datetime",
    ),
    AccumulatorMaxTestCase(
        "datetime_millisecond_precision",
        docs=[
            {"v": datetime(2020, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc)},
            {"v": datetime(2020, 1, 1, 0, 0, 0, 124000, tzinfo=timezone.utc)},
        ],
        accumulator="$v",
        expected=datetime(2020, 1, 1, 0, 0, 0, 124000, tzinfo=timezone.utc),
        msg="$max should distinguish datetimes by millisecond precision",
    ),
    AccumulatorMaxTestCase(
        "datetime_boundaries",
        docs=[{"v": DATE_YEAR_1}, {"v": DATE_YEAR_9999}],
        accumulator="$v",
        expected=DATE_YEAR_9999,
        msg="$max should pick year 9999 over year 1",
    ),
]

# 3e. Timestamp ordering
MAX_TIMESTAMP_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "timestamp_higher_time",
        docs=[{"v": Timestamp(100, 1)}, {"v": Timestamp(200, 1)}],
        accumulator="$v",
        expected=Timestamp(200, 1),
        msg="$max should pick the timestamp with higher time component",
    ),
    AccumulatorMaxTestCase(
        "timestamp_same_time_higher_increment",
        docs=[{"v": Timestamp(100, 1)}, {"v": Timestamp(100, 2)}],
        accumulator="$v",
        expected=Timestamp(100, 2),
        msg="$max should pick the timestamp with higher increment on same time",
    ),
    AccumulatorMaxTestCase(
        "timestamp_max_signed32",
        docs=[{"v": TS_EPOCH}, {"v": TS_MAX_SIGNED32}],
        accumulator="$v",
        expected=TS_MAX_SIGNED32,
        msg="$max should handle max signed 32-bit timestamp",
    ),
    AccumulatorMaxTestCase(
        "timestamp_max_unsigned32",
        docs=[{"v": TS_MAX_SIGNED32}, {"v": TS_MAX_UNSIGNED32}],
        accumulator="$v",
        expected=TS_MAX_UNSIGNED32,
        msg="$max should handle max unsigned 32-bit timestamp",
    ),
]

# 3f. ObjectId ordering
MAX_OBJECTID_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "objectid_later_timestamp",
        docs=[
            {"v": ObjectId("000000010000000000000000")},
            {"v": ObjectId("000000020000000000000000")},
        ],
        accumulator="$v",
        expected=ObjectId("000000020000000000000000"),
        msg="$max should pick the ObjectId with a later timestamp",
    ),
    AccumulatorMaxTestCase(
        "objectid_same_timestamp",
        docs=[
            {"v": ObjectId("000000010000000000000001")},
            {"v": ObjectId("000000010000000000000002")},
        ],
        accumulator="$v",
        expected=ObjectId("000000010000000000000002"),
        msg="$max should pick the ObjectId with higher random bytes on same timestamp",
    ),
]

# 3g. Binary ordering
MAX_BINARY_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "binary_content",
        docs=[{"v": Binary(b"\x01")}, {"v": Binary(b"\x02")}],
        accumulator="$v",
        expected=b"\x02",
        msg="$max should pick the binary with higher byte content",
    ),
    AccumulatorMaxTestCase(
        "binary_subtype",
        docs=[{"v": Binary(b"\x01", 0)}, {"v": Binary(b"\x01", 5)}],
        accumulator="$v",
        expected=Binary(b"\x01", 5),
        msg="$max should pick the binary with higher subtype on same content",
    ),
]

# 3h. Regex ordering
MAX_REGEX_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "regex_pattern",
        docs=[{"v": Regex("abc", "")}, {"v": Regex("def", "")}],
        accumulator="$v",
        expected=Regex("def", ""),
        msg="$max should pick the regex with the higher pattern string",
    ),
    AccumulatorMaxTestCase(
        "regex_flags",
        docs=[{"v": Regex("abc", "i")}, {"v": Regex("abc", "m")}],
        accumulator="$v",
        expected=Regex("abc", "m"),
        msg="$max should pick the regex with higher flag string on same pattern",
    ),
]

# 3i. Code ordering
# NOTE: code_basic is stage-dependent (pymongo returns Code without scope as
# str in $group/$bucket but as Code in $bucketAuto) and tested separately
# below (see MAX_CODE_GROUP_BUCKET_TESTS / MAX_CODE_BUCKET_AUTO_TESTS).
MAX_CODE_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "code_with_scope_vs_code",
        docs=[{"v": Code("z")}, {"v": Code("a", {"x": 1})}],
        accumulator="$v",
        expected=Code("a", {"x": 1}),
        msg="$max should pick CodeWithScope over Code regardless of code string",
    ),
]

# 3j. Object (embedded document) ordering
MAX_OBJECT_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "object_first_differing_field",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": {"a": 1, "b": 3}}],
        accumulator="$v",
        expected={"a": 1, "b": 3},
        msg="$max should pick object with greater value at first differing field",
    ),
    AccumulatorMaxTestCase(
        "object_more_fields",
        docs=[{"v": {"a": 1}}, {"v": {"a": 1, "b": 2}}],
        accumulator="$v",
        expected={"a": 1, "b": 2},
        msg="$max should pick object with more fields when prefix matches",
    ),
    AccumulatorMaxTestCase(
        "object_empty_vs_nonempty",
        docs=[{"v": {}}, {"v": {"a": 1}}],
        accumulator="$v",
        expected={"a": 1},
        msg="$max should pick non-empty object over empty object",
    ),
    AccumulatorMaxTestCase(
        "object_nested",
        docs=[{"v": {"a": {"b": 1}}}, {"v": {"a": {"b": 2}}}],
        accumulator="$v",
        expected={"a": {"b": 2}},
        msg="$max should compare nested objects recursively",
    ),
]

# 3k. Array ordering (as values, NOT traversed in accumulator context)
MAX_ARRAY_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "array_element_by_element",
        docs=[{"v": [1, 2, 3]}, {"v": [1, 2, 4]}],
        accumulator="$v",
        expected=[1, 2, 4],
        msg="$max should compare arrays element by element",
    ),
    AccumulatorMaxTestCase(
        "array_longer_prefix",
        docs=[{"v": [1, 2]}, {"v": [1, 2, 3]}],
        accumulator="$v",
        expected=[1, 2, 3],
        msg="$max should pick longer array when prefix matches",
    ),
    AccumulatorMaxTestCase(
        "array_empty_vs_nonempty",
        docs=[{"v": []}, {"v": [1]}],
        accumulator="$v",
        expected=[1],
        msg="$max should pick non-empty array over empty array",
    ),
    AccumulatorMaxTestCase(
        "array_nested",
        docs=[{"v": [[1]]}, {"v": [[2]]}],
        accumulator="$v",
        expected=[[2]],
        msg="$max should compare nested arrays recursively",
    ),
]

WITHIN_TYPE_TESTS = (
    MAX_NUMERIC_TESTS
    + MAX_STRING_TESTS
    + MAX_BOOLEAN_TESTS
    + MAX_DATETIME_TESTS
    + MAX_TIMESTAMP_TESTS
    + MAX_OBJECTID_TESTS
    + MAX_BINARY_TESTS
    + MAX_REGEX_TESTS
    + MAX_CODE_TESTS
    + MAX_OBJECT_TESTS
    + MAX_ARRAY_TESTS
)


# ---------------------------------------------------------------------------
# 4. NaN Handling
# ---------------------------------------------------------------------------

# Property [NaN Behavior]: NaN compares as less than all other numeric values
# (including negative infinity) in BSON comparison order. As the sole value,
# NaN is returned. Decimal128 -NaN is preserved.
MAX_NAN_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "nan_sole_float",
        docs=[{"v": FLOAT_NAN}],
        accumulator="$v",
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$max should return float NaN when it is the sole value",
    ),
    AccumulatorMaxTestCase(
        "nan_sole_decimal",
        docs=[{"v": DECIMAL128_NAN}],
        accumulator="$v",
        expected=DECIMAL128_NAN,
        msg="$max should return Decimal128 NaN when it is the sole value",
    ),
    AccumulatorMaxTestCase(
        "nan_decimal_negative",
        docs=[{"v": DECIMAL128_NEGATIVE_NAN}],
        accumulator="$v",
        expected=DECIMAL128_NEGATIVE_NAN,
        msg="$max should preserve Decimal128 -NaN as sole value",
    ),
    AccumulatorMaxTestCase(
        "nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 5}],
        accumulator="$v",
        expected=5,
        msg="$max should pick positive number over float NaN",
    ),
    AccumulatorMaxTestCase(
        "nan_vs_negative",
        docs=[{"v": FLOAT_NAN}, {"v": -1000}],
        accumulator="$v",
        expected=-1000,
        msg="$max should pick negative number over float NaN (NaN < all numerics)",
    ),
    AccumulatorMaxTestCase(
        "nan_vs_neg_infinity",
        docs=[{"v": FLOAT_NAN}, {"v": FLOAT_NEGATIVE_INFINITY}],
        accumulator="$v",
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$max should pick -Infinity over float NaN",
    ),
    # NOTE: nan_float_vs_decimal is stage-dependent ($group/$bucket return
    # the last NaN type, $bucketAuto returns the first) and tested separately
    # below (see MAX_NAN_* lists).
    AccumulatorMaxTestCase(
        "nan_as_only_nonnull",
        docs=[{"v": None}, {"v": FLOAT_NAN}],
        accumulator="$v",
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$max should return NaN when it is the only non-null value",
    ),
    AccumulatorMaxTestCase(
        "nan_three_docs",
        docs=[{"v": FLOAT_NAN}, {"v": 5}, {"v": 10}],
        accumulator="$v",
        expected=10,
        msg="$max should pick 10 over NaN and 5",
    ),
]


# ---------------------------------------------------------------------------
# 5. Infinity Handling
# ---------------------------------------------------------------------------

# Property [Infinity Comparison]: +Infinity > all finite values; -Infinity
# < all finite values but > NaN. String > Number in BSON order, so Infinity
# < any string.
MAX_INFINITY_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "inf_vs_int32",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT32_MAX}],
        accumulator="$v",
        expected=FLOAT_INFINITY,
        msg="$max should pick Infinity over INT32_MAX",
    ),
    AccumulatorMaxTestCase(
        "inf_vs_int64",
        docs=[{"v": FLOAT_INFINITY}, {"v": INT64_MAX}],
        accumulator="$v",
        expected=FLOAT_INFINITY,
        msg="$max should pick Infinity over INT64_MAX",
    ),
    AccumulatorMaxTestCase(
        "inf_vs_double",
        docs=[{"v": FLOAT_INFINITY}, {"v": DOUBLE_MAX}],
        accumulator="$v",
        expected=FLOAT_INFINITY,
        msg="$max should pick Infinity over DOUBLE_MAX",
    ),
    AccumulatorMaxTestCase(
        "inf_vs_decimal128",
        docs=[{"v": FLOAT_INFINITY}, {"v": DECIMAL128_MAX}],
        accumulator="$v",
        expected=FLOAT_INFINITY,
        msg="$max should pick float Infinity over DECIMAL128_MAX",
    ),
    AccumulatorMaxTestCase(
        "decimal_inf_vs_double",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DOUBLE_MAX}],
        accumulator="$v",
        expected=DECIMAL128_INFINITY,
        msg="$max should pick Decimal128 Infinity over DOUBLE_MAX",
    ),
    AccumulatorMaxTestCase(
        "neg_inf_vs_int32",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT32_MIN}],
        accumulator="$v",
        expected=INT32_MIN,
        msg="$max should pick INT32_MIN over -Infinity",
    ),
    AccumulatorMaxTestCase(
        "neg_inf_vs_decimal",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": DECIMAL128_MIN}],
        accumulator="$v",
        expected=DECIMAL128_MIN,
        msg="$max should pick DECIMAL128_MIN over -Infinity",
    ),
    AccumulatorMaxTestCase(
        "inf_vs_neg_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        accumulator="$v",
        expected=FLOAT_INFINITY,
        msg="$max should pick Infinity over -Infinity",
    ),
    AccumulatorMaxTestCase(
        "decimal_inf_vs_neg_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_NEGATIVE_INFINITY}],
        accumulator="$v",
        expected=DECIMAL128_INFINITY,
        msg="$max should pick Decimal128 Infinity over Decimal128 -Infinity",
    ),
    AccumulatorMaxTestCase(
        "inf_vs_string",
        docs=[{"v": FLOAT_INFINITY}, {"v": "hello"}],
        accumulator="$v",
        expected="hello",
        msg="$max should pick string over Infinity (string > number in BSON order)",
    ),
]


# ---------------------------------------------------------------------------
# 6. Numeric Boundary Values
# ---------------------------------------------------------------------------

# Property [Numeric Boundaries]: boundary values across all numeric types
# are compared correctly.
MAX_BOUNDARY_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "boundary_int32_max_vs_min",
        docs=[{"v": INT32_MAX}, {"v": INT32_MIN}],
        accumulator="$v",
        expected=INT32_MAX,
        msg="$max should pick INT32_MAX over INT32_MIN",
    ),
    AccumulatorMaxTestCase(
        "boundary_int64_max_vs_min",
        docs=[{"v": INT64_MAX}, {"v": INT64_MIN}],
        accumulator="$v",
        expected=INT64_MAX,
        msg="$max should pick INT64_MAX over INT64_MIN",
    ),
    AccumulatorMaxTestCase(
        "boundary_double_max_vs_min",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MIN}],
        accumulator="$v",
        expected=DOUBLE_MAX,
        msg="$max should pick DOUBLE_MAX over DOUBLE_MIN",
    ),
    AccumulatorMaxTestCase(
        "boundary_decimal_max_vs_min",
        docs=[{"v": DECIMAL128_MAX}, {"v": DECIMAL128_MIN}],
        accumulator="$v",
        expected=DECIMAL128_MAX,
        msg="$max should pick DECIMAL128_MAX over DECIMAL128_MIN",
    ),
    AccumulatorMaxTestCase(
        "boundary_int32_max_vs_int64_max",
        docs=[{"v": INT32_MAX}, {"v": INT64_MAX}],
        accumulator="$v",
        expected=INT64_MAX,
        msg="$max should pick INT64_MAX over INT32_MAX",
    ),
    AccumulatorMaxTestCase(
        "boundary_double_max_vs_int64_max",
        docs=[{"v": DOUBLE_MAX}, {"v": INT64_MAX}],
        accumulator="$v",
        expected=DOUBLE_MAX,
        msg="$max should pick DOUBLE_MAX over INT64_MAX",
    ),
    AccumulatorMaxTestCase(
        "boundary_decimal_max_vs_double_max",
        docs=[{"v": DECIMAL128_MAX}, {"v": DOUBLE_MAX}],
        accumulator="$v",
        expected=DECIMAL128_MAX,
        msg="$max should pick DECIMAL128_MAX over DOUBLE_MAX",
    ),
    AccumulatorMaxTestCase(
        "boundary_subnormal_vs_zero",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": DOUBLE_ZERO}],
        accumulator="$v",
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="$max should pick smallest positive subnormal over zero",
    ),
    AccumulatorMaxTestCase(
        "boundary_neg_subnormal_vs_zero",
        docs=[{"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}, {"v": DOUBLE_ZERO}],
        accumulator="$v",
        expected=DOUBLE_ZERO,
        msg="$max should pick zero over negative subnormal",
    ),
    AccumulatorMaxTestCase(
        "boundary_near_max",
        docs=[{"v": DOUBLE_NEAR_MAX}, {"v": DOUBLE_MAX}],
        accumulator="$v",
        expected=DOUBLE_MAX,
        msg="$max should pick DOUBLE_MAX over DOUBLE_NEAR_MAX",
    ),
    AccumulatorMaxTestCase(
        "boundary_int32_adjacent",
        docs=[{"v": INT32_MAX}, {"v": INT32_MAX_MINUS_1}],
        accumulator="$v",
        expected=INT32_MAX,
        msg="$max should pick INT32_MAX over INT32_MAX - 1",
    ),
    AccumulatorMaxTestCase(
        "boundary_int64_adjacent",
        docs=[{"v": INT64_MAX}, {"v": INT64_MAX_MINUS_1}],
        accumulator="$v",
        expected=INT64_MAX,
        msg="$max should pick INT64_MAX over INT64_MAX - 1",
    ),
]


# ---------------------------------------------------------------------------
# 7. Negative Zero
# ---------------------------------------------------------------------------

# Property [Negative Zero]: -0.0 and +0.0 are numerically equal; tie-breaking
# by document order differs by stage ($group/$bucket: last wins, $bucketAuto:
# first wins). The negzero_double and negzero_decimal tests are stage-dependent
# and tested separately below.
MAX_NEGZERO_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "negzero_double_vs_positive",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": 1}],
        accumulator="$v",
        expected=1,
        msg="$max should pick positive number over double -0.0",
    ),
    AccumulatorMaxTestCase(
        "negzero_decimal_vs_positive",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": 1.0}],
        accumulator="$v",
        expected=1.0,
        msg="$max should pick positive number over Decimal128 -0",
    ),
]


# ---------------------------------------------------------------------------
# 8. Decimal128 Precision
# ---------------------------------------------------------------------------

# Property [Decimal128 Precision]: Decimal128 precision boundaries are
# handled correctly.
MAX_DECIMAL_PRECISION_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "decimal_high_precision",
        docs=[
            {"v": Decimal128("1.234567890123456789012345678901234")},
            {"v": Decimal128("1.234567890123456789012345678901235")},
        ],
        accumulator="$v",
        expected=Decimal128("1.234567890123456789012345678901235"),
        msg="$max should distinguish 34-digit Decimal128 values",
    ),
    # NOTE: decimal_trailing_zeros is stage-dependent ($group/$bucket return
    # the last equal value, $bucketAuto returns the first) and tested separately
    # below (see MAX_DECIMAL_TRAILING_* lists).
    AccumulatorMaxTestCase(
        "decimal_large_exponent",
        docs=[{"v": DECIMAL128_LARGE_EXPONENT}, {"v": DECIMAL128_MAX}],
        accumulator="$v",
        expected=DECIMAL128_MAX,
        msg="$max should pick DECIMAL128_MAX over DECIMAL128_LARGE_EXPONENT",
    ),
    AccumulatorMaxTestCase(
        "decimal_min_positive",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": DECIMAL128_ZERO}],
        accumulator="$v",
        expected=DECIMAL128_MIN_POSITIVE,
        msg="$max should pick DECIMAL128_MIN_POSITIVE over zero",
    ),
    AccumulatorMaxTestCase(
        "decimal_max_negative",
        docs=[{"v": DECIMAL128_MAX_NEGATIVE}, {"v": DECIMAL128_ZERO}],
        accumulator="$v",
        expected=DECIMAL128_ZERO,
        msg="$max should pick zero over DECIMAL128_MAX_NEGATIVE",
    ),
    AccumulatorMaxTestCase(
        "decimal_inf_vs_max",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_MAX}],
        accumulator="$v",
        expected=DECIMAL128_INFINITY,
        msg="$max should pick Decimal128 Infinity over DECIMAL128_MAX",
    ),
    AccumulatorMaxTestCase(
        "decimal_neg_inf_vs_min",
        docs=[{"v": DECIMAL128_NEGATIVE_INFINITY}, {"v": DECIMAL128_MIN}],
        accumulator="$v",
        expected=DECIMAL128_MIN,
        msg="$max should pick DECIMAL128_MIN over Decimal128 -Infinity",
    ),
    AccumulatorMaxTestCase(
        "decimal_nan_vs_finite",
        docs=[{"v": DECIMAL128_NAN}, {"v": Decimal128("5")}],
        accumulator="$v",
        expected=Decimal128("5"),
        msg="$max should pick finite Decimal128 over Decimal128 NaN",
    ),
]


# ---------------------------------------------------------------------------
# 9. Tie-Breaking and Type Preservation
# ---------------------------------------------------------------------------

# Property [Tie-Breaking]: when values are numerically equal but different
# types, $group/$bucket preserve the last encountered type while $bucketAuto
# preserves the first. These are tested separately per stage group.
MAX_TIE_BREAKING_TESTS: list[AccumulatorMaxTestCase] = []

# $group and $bucket: last encountered value wins
MAX_TIE_BREAKING_GROUP_BUCKET_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "tie_int32_int64",
        docs=[{"v": 5}, {"v": Int64(5)}],
        accumulator="$v",
        expected=Int64(5),
        msg="$max should preserve type of last equal value (Int64) in $group/$bucket",
    ),
    AccumulatorMaxTestCase(
        "tie_int64_int32",
        docs=[{"v": Int64(5)}, {"v": 5}],
        accumulator="$v",
        expected=5,
        msg="$max should preserve type of last equal value (int32) in $group/$bucket",
    ),
    AccumulatorMaxTestCase(
        "tie_double_int32",
        docs=[{"v": 5.0}, {"v": 5}],
        accumulator="$v",
        expected=5,
        msg="$max should preserve type of last equal value (int32) in $group/$bucket",
    ),
    AccumulatorMaxTestCase(
        "tie_decimal_int64",
        docs=[{"v": Decimal128("5")}, {"v": Int64(5)}],
        accumulator="$v",
        expected=Int64(5),
        msg="$max should preserve type of last equal value (Int64) in $group/$bucket",
    ),
    AccumulatorMaxTestCase(
        "tie_all_four_types",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        accumulator="$v",
        expected=Decimal128("5"),
        msg="$max should preserve type of last equal value (Decimal128) in $group/$bucket",
    ),
    AccumulatorMaxTestCase(
        "tie_reversed_order",
        docs=[{"v": Decimal128("5")}, {"v": 5.0}, {"v": Int64(5)}, {"v": 5}],
        accumulator="$v",
        expected=5,
        msg="$max should preserve type of last equal value (int32) in $group/$bucket",
    ),
]

# $bucketAuto: first encountered value wins
MAX_TIE_BREAKING_BUCKET_AUTO_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "tie_int32_int64",
        docs=[{"v": 5}, {"v": Int64(5)}],
        accumulator="$v",
        expected=5,
        msg="$max should preserve type of first equal value (int32) in $bucketAuto",
    ),
    AccumulatorMaxTestCase(
        "tie_int64_int32",
        docs=[{"v": Int64(5)}, {"v": 5}],
        accumulator="$v",
        expected=Int64(5),
        msg="$max should preserve type of first equal value (Int64) in $bucketAuto",
    ),
    AccumulatorMaxTestCase(
        "tie_double_int32",
        docs=[{"v": 5.0}, {"v": 5}],
        accumulator="$v",
        expected=5.0,
        msg="$max should preserve type of first equal value (double) in $bucketAuto",
    ),
    AccumulatorMaxTestCase(
        "tie_decimal_int64",
        docs=[{"v": Decimal128("5")}, {"v": Int64(5)}],
        accumulator="$v",
        expected=Decimal128("5"),
        msg="$max should preserve type of first equal value (Decimal128) in $bucketAuto",
    ),
    AccumulatorMaxTestCase(
        "tie_all_four_types",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        accumulator="$v",
        expected=5,
        msg="$max should preserve type of first equal value (int32) in $bucketAuto",
    ),
    AccumulatorMaxTestCase(
        "tie_reversed_order",
        docs=[{"v": Decimal128("5")}, {"v": 5.0}, {"v": Int64(5)}, {"v": 5}],
        accumulator="$v",
        expected=Decimal128("5"),
        msg="$max should preserve type of first equal value (Decimal128) in $bucketAuto",
    ),
]


# ---------------------------------------------------------------------------
# 10. Numeric Equivalence
# ---------------------------------------------------------------------------

# Property [Numeric Equivalence]: numerically equivalent values across types
# are treated as equal for comparison; tie-breaking differs by stage
# ($group/$bucket: last wins, $bucketAuto: first wins).
MAX_NUMERIC_EQUIV_TESTS: list[AccumulatorMaxTestCase] = []

MAX_NUMERIC_EQUIV_GROUP_BUCKET_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "equiv_int_long_double_decimal",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        accumulator="$v",
        expected=Decimal128("5"),
        msg="$max should return last type (Decimal128) for equal values in $group/$bucket",
    ),
    AccumulatorMaxTestCase(
        "equiv_zeros",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": DOUBLE_ZERO}, {"v": DECIMAL128_ZERO}],
        accumulator="$v",
        expected=DECIMAL128_ZERO,
        msg="$max should return last type (Decimal128) for zero values in $group/$bucket",
    ),
]

MAX_NUMERIC_EQUIV_BUCKET_AUTO_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "equiv_int_long_double_decimal",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        accumulator="$v",
        expected=5,
        msg="$max should return first type (int32) for equal values in $bucketAuto",
    ),
    AccumulatorMaxTestCase(
        "equiv_zeros",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": DOUBLE_ZERO}, {"v": DECIMAL128_ZERO}],
        accumulator="$v",
        expected=0,
        msg="$max should return first type (int32) for zero values in $bucketAuto",
    ),
]


# ---------------------------------------------------------------------------
# 11. BSON Type Distinction
# ---------------------------------------------------------------------------

# Property [BSON Type Distinction]: values of different BSON types are
# distinct even when they appear similar.
MAX_TYPE_DISTINCTION_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "distinct_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        accumulator="$v",
        expected=False,
        msg="$max should pick False over 0 (boolean > number in BSON order)",
    ),
    AccumulatorMaxTestCase(
        "distinct_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        accumulator="$v",
        expected=True,
        msg="$max should pick True over 1 (boolean > number in BSON order)",
    ),
    AccumulatorMaxTestCase(
        "distinct_empty_string_vs_null",
        docs=[{"v": ""}, {"v": None}],
        accumulator="$v",
        expected="",
        msg="$max should exclude null and return empty string",
    ),
    AccumulatorMaxTestCase(
        "distinct_numeric_string",
        docs=[{"v": "123"}, {"v": 1000000}],
        accumulator="$v",
        expected="123",
        msg="$max should pick string '123' over int 1000000 (string > number, no coercion)",
    ),
]


# ---------------------------------------------------------------------------
# 12. Expression Error Propagation
# ---------------------------------------------------------------------------

# Property [Expression Error Propagation]: errors in sub-expressions used as
# $max operand propagate as errors.
# NOTE: divide-by-zero and mod-by-zero have stage-specific error codes
# ($bucketAuto wraps them differently) and are tested separately.
MAX_EXPRESSION_ERROR_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "error_toInt_invalid",
        docs=[{"v": "not_a_number"}],
        accumulator={"$toInt": "$v"},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$max should propagate conversion error from $toInt sub-expression",
    ),
]

MAX_EXPRESSION_ERROR_GROUP_BUCKET_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "error_divide_by_zero",
        docs=[{"v": 10}],
        accumulator={"$divide": ["$v", 0]},
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$max should propagate divide-by-zero error in $group/$bucket",
    ),
    AccumulatorMaxTestCase(
        "error_mod_by_zero",
        docs=[{"v": 10}],
        accumulator={"$mod": ["$v", 0]},
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$max should propagate mod-by-zero error in $group/$bucket",
    ),
]

MAX_EXPRESSION_ERROR_BUCKET_AUTO_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "error_divide_by_zero",
        docs=[{"v": 10}],
        accumulator={"$divide": ["$v", 0]},
        error_code=BAD_VALUE_ERROR,
        msg="$max should propagate divide-by-zero error in $bucketAuto (wrapped as BAD_VALUE)",
    ),
    AccumulatorMaxTestCase(
        "error_mod_by_zero",
        docs=[{"v": 10}],
        accumulator={"$mod": ["$v", 0]},
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="$max should propagate mod-by-zero error in $bucketAuto (wrapped as 16610)",
    ),
]


# ---------------------------------------------------------------------------
# 13. Expression Argument Tests (Input Forms)
# ---------------------------------------------------------------------------

# Property [Input Forms]: $max accumulator accepts various expression types
# as its operand.
MAX_INPUT_FORM_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "input_field_path",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        accumulator="$v",
        expected=20,
        msg="$max should accept a basic field path reference",
    ),
    AccumulatorMaxTestCase(
        "input_nested_field",
        docs=[{"a": {"b": 10}}, {"a": {"b": 20}}, {"a": {"b": 5}}],
        accumulator="$a.b",
        expected=20,
        msg="$max should accept a nested document field path",
    ),
    AccumulatorMaxTestCase(
        "input_literal",
        docs=[{"v": 1}, {"v": 2}],
        accumulator=42,
        expected=42,
        msg="$max with a literal constant should return that constant",
    ),
    AccumulatorMaxTestCase(
        "input_expression",
        docs=[{"price": 10, "qty": 2}, {"price": 5, "qty": 10}],
        accumulator={"$multiply": ["$price", "$qty"]},
        expected=50,
        msg="$max should accept a computed expression as operand",
    ),
    AccumulatorMaxTestCase(
        "input_cond_remove",
        docs=[{"v": -1}, {"v": 5}, {"v": 3}],
        accumulator={"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]},
        expected=5,
        msg="$max should accept conditional with $$REMOVE as operand",
    ),
    AccumulatorMaxTestCase(
        "input_null_literal",
        docs=[{"v": 1}, {"v": 2}],
        accumulator=None,
        expected=None,
        msg="$max with null literal should return null (all docs produce null)",
    ),
]


# ---------------------------------------------------------------------------
# 14. Arity Rejection
# ---------------------------------------------------------------------------

# Property [Arity]: $max in accumulator context is a unary operator and
# rejects array syntax in $group, $bucket, and $bucketAuto.
MAX_ARITY_ERROR_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "arity_empty_array",
        docs=[{"v": 1}],
        accumulator=[],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject empty array in accumulator context",
    ),
    AccumulatorMaxTestCase(
        "arity_single_element_array",
        docs=[{"v": 1}],
        accumulator=[1],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single-element literal array in accumulator context",
    ),
    AccumulatorMaxTestCase(
        "arity_single_field_ref_array",
        docs=[{"v": 1}],
        accumulator=["$v"],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single field ref in array in accumulator context",
    ),
    AccumulatorMaxTestCase(
        "arity_multi_element_array",
        docs=[{"v": 1}],
        accumulator=[1, 2, 3],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject multi-element array in accumulator context",
    ),
    AccumulatorMaxTestCase(
        "arity_multi_key_expression_object",
        docs=[{"v": 1}],
        accumulator={"$add": [1, 2], "$multiply": [3, 4]},
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$max should reject multi-key expression object",
    ),
]


# ---------------------------------------------------------------------------
# 15. Return Type Verification
# ---------------------------------------------------------------------------

# Property [Return Type]: $max preserves the BSON type of the maximum value.
MAX_RETURN_TYPE_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "return_type_int32",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        accumulator="$v",
        expected=[{"value": 30, "type": "int"}],
        msg="$max of int32 values should return type 'int'",
    ),
    AccumulatorMaxTestCase(
        "return_type_int64",
        docs=[{"v": Int64(100)}, {"v": Int64(300)}, {"v": Int64(200)}],
        accumulator="$v",
        expected=[{"value": Int64(300), "type": "long"}],
        msg="$max of int64 values should return type 'long'",
    ),
    AccumulatorMaxTestCase(
        "return_type_double",
        docs=[{"v": 1.5}, {"v": 3.5}, {"v": 2.5}],
        accumulator="$v",
        expected=[{"value": 3.5, "type": "double"}],
        msg="$max of double values should return type 'double'",
    ),
    AccumulatorMaxTestCase(
        "return_type_decimal",
        docs=[{"v": Decimal128("1")}, {"v": Decimal128("3")}, {"v": Decimal128("2")}],
        accumulator="$v",
        expected=[{"value": Decimal128("3"), "type": "decimal"}],
        msg="$max of Decimal128 values should return type 'decimal'",
    ),
    AccumulatorMaxTestCase(
        "return_type_string",
        docs=[{"v": "a"}, {"v": "c"}, {"v": "b"}],
        accumulator="$v",
        expected=[{"value": "c", "type": "string"}],
        msg="$max of string values should return type 'string'",
    ),
    AccumulatorMaxTestCase(
        "return_type_boolean",
        docs=[{"v": True}, {"v": False}],
        accumulator="$v",
        expected=[{"value": True, "type": "bool"}],
        msg="$max of boolean values should return type 'bool'",
    ),
    AccumulatorMaxTestCase(
        "return_type_date",
        docs=[
            {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        ],
        accumulator="$v",
        expected=[{"value": datetime(2023, 1, 1, tzinfo=timezone.utc), "type": "date"}],
        msg="$max of datetime values should return type 'date'",
    ),
    AccumulatorMaxTestCase(
        "return_type_null_all",
        docs=[{"v": None}, {"v": None}],
        accumulator="$v",
        expected=[{"value": None, "type": "null"}],
        msg="$max of all null values should return type 'null'",
    ),
]


# ---------------------------------------------------------------------------
# 16. Accumulator-Specific Edge Cases
# ---------------------------------------------------------------------------

# Property [Edge Cases]: edge cases unique to accumulator context.
MAX_EDGE_CASE_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "edge_single_doc",
        docs=[{"v": 42}],
        accumulator="$v",
        expected=42,
        msg="$max of a single document should return that document's value",
    ),
    AccumulatorMaxTestCase(
        "edge_single_null_doc",
        docs=[{"v": None}],
        accumulator="$v",
        expected=None,
        msg="$max of a single null document should return null",
    ),
    AccumulatorMaxTestCase(
        "edge_single_missing_doc",
        docs=[{"x": 1}],
        accumulator="$v",
        expected=None,
        msg="$max of a single document with missing field should return null",
    ),
    AccumulatorMaxTestCase(
        "edge_multi_group",
        docs=[
            {"g": "A", "v": 10},
            {"g": "A", "v": 20},
            {"g": "B", "v": 5},
            {"g": "B", "v": 15},
        ],
        accumulator="$v",
        expected=20,
        msg="$max should compute correctly across documents (single group via $literal)",
    ),
    AccumulatorMaxTestCase(
        "edge_many_docs",
        docs=[{"v": i} for i in range(100)],
        accumulator="$v",
        expected=99,
        msg="$max should return correct value across 100 documents",
    ),
    AccumulatorMaxTestCase(
        "edge_array_field_not_traversed",
        docs=[{"v": [5, 1, 8]}, {"v": [3, 9, 2]}],
        accumulator="$v",
        expected=[5, 1, 8],
        msg="$max should compare arrays as whole values, not traverse them",
    ),
    AccumulatorMaxTestCase(
        "edge_mixed_array_scalar",
        docs=[{"v": [1, 2, 3]}, {"v": 5}],
        accumulator="$v",
        expected=[1, 2, 3],
        msg="$max should pick array over scalar (array > number in BSON order)",
    ),
]


# ---------------------------------------------------------------------------
# Combine all success tests for the main parametrized function
# ---------------------------------------------------------------------------

MAX_SUCCESS_TESTS = (
    MAX_NULL_MISSING_TESTS
    + MAX_BSON_ORDER_TESTS
    + WITHIN_TYPE_TESTS
    + MAX_NAN_TESTS
    + MAX_INFINITY_TESTS
    + MAX_BOUNDARY_TESTS
    + MAX_NEGZERO_TESTS
    + MAX_DECIMAL_PRECISION_TESTS
    + MAX_TIE_BREAKING_TESTS
    + MAX_NUMERIC_EQUIV_TESTS
    + MAX_TYPE_DISTINCTION_TESTS
    + MAX_INPUT_FORM_TESTS
    + MAX_EDGE_CASE_TESTS
)


# ---------------------------------------------------------------------------
# Stage-Specific Test Data (behavior differs between $group/$bucket and
# $bucketAuto)
# ---------------------------------------------------------------------------

# BSON Order: In $group/$bucket, Code without scope is returned as str by
# pymongo, and MaxKey is wrapped in {'': MaxKey()}. In $bucketAuto, Code is
# returned as Code object and MaxKey is returned directly.
MAX_BSON_ORDER_GROUP_BUCKET_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "bson_regex_vs_code",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        accumulator="$v",
        expected="a",
        msg="$max should pick Code over regex per BSON order (returned as str in $group/$bucket)",
    ),
    AccumulatorMaxTestCase(
        "bson_code_vs_maxkey",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        accumulator="$v",
        expected={"": MaxKey()},
        msg="$max should pick MaxKey over Code per BSON order (wrapped in dict in $group/$bucket)",
    ),
    AccumulatorMaxTestCase(
        "bson_minkey_vs_maxkey",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        accumulator="$v",
        expected={"": MaxKey()},
        msg="$max should pick MaxKey over MinKey (wrapped in dict in $group/$bucket)",
    ),
    AccumulatorMaxTestCase(
        "bson_maxkey_before_minkey",
        docs=[{"v": MaxKey()}, {"v": MinKey()}],
        accumulator="$v",
        expected={"": MaxKey()},
        msg="$max should pick MaxKey even when first (wrapped in dict in $group/$bucket)",
    ),
]

MAX_BSON_ORDER_BUCKET_AUTO_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "bson_regex_vs_code",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        accumulator="$v",
        expected=Code("a"),
        msg="$max should pick Code over regex per BSON order in $bucketAuto",
    ),
    AccumulatorMaxTestCase(
        "bson_code_vs_maxkey",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        accumulator="$v",
        expected=MaxKey(),
        msg="$max should pick MaxKey over Code per BSON order in $bucketAuto",
    ),
    AccumulatorMaxTestCase(
        "bson_minkey_vs_maxkey",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        accumulator="$v",
        expected=MaxKey(),
        msg="$max should pick MaxKey over MinKey in $bucketAuto",
    ),
    AccumulatorMaxTestCase(
        "bson_maxkey_before_minkey",
        docs=[{"v": MaxKey()}, {"v": MinKey()}],
        accumulator="$v",
        expected=MaxKey(),
        msg="$max should pick MaxKey even when first in $bucketAuto",
    ),
]

# Code ordering: pymongo returns Code without scope as str in $group/$bucket
# but as Code in $bucketAuto.
MAX_CODE_GROUP_BUCKET_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "code_basic",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        accumulator="$v",
        expected="b()",
        msg="$max should pick Code with higher string value (returned as str in $group/$bucket)",
    ),
]

MAX_CODE_BUCKET_AUTO_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "code_basic",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        accumulator="$v",
        expected=Code("b()"),
        msg="$max should pick Code with higher string value in $bucketAuto",
    ),
]

# NaN tie-breaking: $group/$bucket return last NaN type, $bucketAuto returns first.
MAX_NAN_GROUP_BUCKET_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "nan_float_vs_decimal",
        docs=[{"v": FLOAT_NAN}, {"v": DECIMAL128_NAN}],
        accumulator="$v",
        expected=DECIMAL128_NAN,
        msg="$max should return last NaN type (Decimal128 NaN) in $group/$bucket",
    ),
]

MAX_NAN_BUCKET_AUTO_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "nan_float_vs_decimal",
        docs=[{"v": FLOAT_NAN}, {"v": DECIMAL128_NAN}],
        accumulator="$v",
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$max should return first NaN type (float NaN) in $bucketAuto",
    ),
]

# Negative zero tie-breaking: $group/$bucket return last (positive zero),
# $bucketAuto returns first (negative zero).
MAX_NEGZERO_GROUP_BUCKET_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "negzero_double",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": DOUBLE_ZERO}],
        accumulator="$v",
        expected=DOUBLE_ZERO,
        msg="$max should return last zero (positive) when -0.0 and 0.0 tie in $group/$bucket",
    ),
    AccumulatorMaxTestCase(
        "negzero_decimal",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": DECIMAL128_ZERO}],
        accumulator="$v",
        expected=DECIMAL128_ZERO,
        msg="$max should return last zero (positive) when Decimal128 -0 and 0 tie in $group/$bucket",
    ),
]

MAX_NEGZERO_BUCKET_AUTO_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "negzero_double",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": DOUBLE_ZERO}],
        accumulator="$v",
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="$max should return first zero (-0.0) when -0.0 and 0.0 tie in $bucketAuto",
    ),
    AccumulatorMaxTestCase(
        "negzero_decimal",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": DECIMAL128_ZERO}],
        accumulator="$v",
        expected=DECIMAL128_NEGATIVE_ZERO,
        msg="$max should return first zero (Decimal128 -0) when -0 and 0 tie in $bucketAuto",
    ),
]

# Decimal trailing zeros tie-breaking: $group/$bucket return last,
# $bucketAuto returns first.
MAX_DECIMAL_TRAILING_GROUP_BUCKET_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "decimal_trailing_zeros",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        accumulator="$v",
        expected=Decimal128("1.00"),
        msg="$max should return last Decimal128 (1.00) when equal in $group/$bucket",
    ),
]

MAX_DECIMAL_TRAILING_BUCKET_AUTO_TESTS: list[AccumulatorMaxTestCase] = [
    AccumulatorMaxTestCase(
        "decimal_trailing_zeros",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        accumulator="$v",
        expected=Decimal128("1.0"),
        msg="$max should return first Decimal128 (1.0) when equal in $bucketAuto",
    ),
]

# Combine all $group/$bucket stage-specific success tests
MAX_GROUP_BUCKET_TESTS = (
    MAX_BSON_ORDER_GROUP_BUCKET_TESTS
    + MAX_CODE_GROUP_BUCKET_TESTS
    + MAX_NAN_GROUP_BUCKET_TESTS
    + MAX_NEGZERO_GROUP_BUCKET_TESTS
    + MAX_DECIMAL_TRAILING_GROUP_BUCKET_TESTS
    + MAX_TIE_BREAKING_GROUP_BUCKET_TESTS
    + MAX_NUMERIC_EQUIV_GROUP_BUCKET_TESTS
)

# Combine all $bucketAuto stage-specific success tests
MAX_BUCKET_AUTO_TESTS = (
    MAX_BSON_ORDER_BUCKET_AUTO_TESTS
    + MAX_CODE_BUCKET_AUTO_TESTS
    + MAX_NAN_BUCKET_AUTO_TESTS
    + MAX_NEGZERO_BUCKET_AUTO_TESTS
    + MAX_DECIMAL_TRAILING_BUCKET_AUTO_TESTS
    + MAX_TIE_BREAKING_BUCKET_AUTO_TESTS
    + MAX_NUMERIC_EQUIV_BUCKET_AUTO_TESTS
)


# ===========================================================================
# Test Functions
# ===========================================================================


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("test_case", pytest_params(MAX_SUCCESS_TESTS))
def test_accumulator_max(collection, test_case: AccumulatorMaxTestCase, stage: str):
    """Test $max accumulator success cases across all three stages."""
    result = _execute_accumulator(collection, test_case, stage)
    assertSuccess(
        result,
        [{"result": test_case.expected}],
        msg=test_case.msg,
    )


@pytest.mark.parametrize("stage", ["group", "bucket"])
@pytest.mark.parametrize("test_case", pytest_params(MAX_GROUP_BUCKET_TESTS))
def test_accumulator_max_group_bucket(
    collection, test_case: AccumulatorMaxTestCase, stage: str
):
    """Test $max cases where $group/$bucket behavior differs from $bucketAuto."""
    result = _execute_accumulator(collection, test_case, stage)
    assertSuccess(
        result,
        [{"result": test_case.expected}],
        msg=test_case.msg,
    )


@pytest.mark.parametrize("test_case", pytest_params(MAX_BUCKET_AUTO_TESTS))
def test_accumulator_max_bucket_auto(
    collection, test_case: AccumulatorMaxTestCase
):
    """Test $max cases where $bucketAuto behavior differs from $group/$bucket."""
    result = _execute_accumulator(collection, test_case, "bucketAuto")
    assertSuccess(
        result,
        [{"result": test_case.expected}],
        msg=test_case.msg,
    )


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("test_case", pytest_params(MAX_EXPRESSION_ERROR_TESTS))
def test_accumulator_max_expression_errors(
    collection, test_case: AccumulatorMaxTestCase, stage: str
):
    """Test $max expression error propagation across all three stages."""
    result = _execute_accumulator(collection, test_case, stage)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


@pytest.mark.parametrize("stage", ["group", "bucket"])
@pytest.mark.parametrize("test_case", pytest_params(MAX_EXPRESSION_ERROR_GROUP_BUCKET_TESTS))
def test_accumulator_max_expression_errors_group_bucket(
    collection, test_case: AccumulatorMaxTestCase, stage: str
):
    """Test $max expression errors that have different codes in $bucketAuto."""
    result = _execute_accumulator(collection, test_case, stage)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MAX_EXPRESSION_ERROR_BUCKET_AUTO_TESTS))
def test_accumulator_max_expression_errors_bucket_auto(
    collection, test_case: AccumulatorMaxTestCase
):
    """Test $max expression errors in $bucketAuto with stage-specific error codes."""
    result = _execute_accumulator(collection, test_case, "bucketAuto")
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("test_case", pytest_params(MAX_ARITY_ERROR_TESTS))
def test_accumulator_max_arity_errors(collection, test_case: AccumulatorMaxTestCase, stage: str):
    """Test $max arity rejection across all three stages."""
    result = _execute_accumulator(collection, test_case, stage)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("test_case", pytest_params(MAX_RETURN_TYPE_TESTS))
def test_accumulator_max_return_type(collection, test_case: AccumulatorMaxTestCase, stage: str):
    """Test $max return type preservation across all three stages."""
    result = _execute_accumulator_with_type(collection, test_case, stage)
    assertSuccess(result, test_case.expected, msg=test_case.msg)
