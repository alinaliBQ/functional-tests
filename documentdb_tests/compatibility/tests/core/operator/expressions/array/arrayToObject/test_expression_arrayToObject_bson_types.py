"""
BSON type tests for $arrayToObject expression.

Tests that various BSON value types are preserved when converting
arrays to objects, including special numeric values, boundary values,
UUID binary, nested BSON values, and numeric type equivalence,
across both k/v and pair input forms.
"""

import math
from datetime import datetime, timezone
from uuid import UUID

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
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Value Types K/V]: $arrayToObject preserves each value's BSON type in k/v form.
BSON_KV_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="kv_int64",
        arrays=[{"k": "a", "v": Int64(99)}],
        expected={"a": Int64(99)},
        msg="$arrayToObject should preserve Int64 value",
    ),
    ArrayTestClass(
        id="kv_decimal128",
        arrays=[{"k": "a", "v": Decimal128("3.14")}],
        expected={"a": Decimal128("3.14")},
        msg="$arrayToObject should preserve Decimal128 value",
    ),
    ArrayTestClass(
        id="kv_datetime",
        arrays=[{"k": "a", "v": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        expected={"a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="$arrayToObject should preserve datetime value",
    ),
    ArrayTestClass(
        id="kv_objectid",
        arrays=[{"k": "a", "v": ObjectId("000000000000000000000001")}],
        expected={"a": ObjectId("000000000000000000000001")},
        msg="$arrayToObject should preserve ObjectId value",
    ),
    ArrayTestClass(
        id="kv_bool_false",
        arrays=[{"k": "a", "v": False}],
        expected={"a": False},
        msg="$arrayToObject should preserve false value",
    ),
    ArrayTestClass(
        id="kv_bool_true",
        arrays=[{"k": "a", "v": True}],
        expected={"a": True},
        msg="$arrayToObject should preserve true value",
    ),
    ArrayTestClass(
        id="kv_null",
        arrays=[{"k": "a", "v": None}],
        expected={"a": None},
        msg="$arrayToObject should preserve null value",
    ),
    ArrayTestClass(
        id="kv_regex",
        arrays=[{"k": "a", "v": Regex("^abc", "i")}],
        expected={"a": Regex("^abc", "i")},
        msg="$arrayToObject should preserve regex value",
    ),
    ArrayTestClass(
        id="kv_minkey",
        arrays=[{"k": "a", "v": MinKey()}],
        expected={"a": MinKey()},
        msg="$arrayToObject should preserve MinKey value",
    ),
    ArrayTestClass(
        id="kv_maxkey",
        arrays=[{"k": "a", "v": MaxKey()}],
        expected={"a": MaxKey()},
        msg="$arrayToObject should preserve MaxKey value",
    ),
    ArrayTestClass(
        id="kv_binary",
        arrays=[{"k": "a", "v": Binary(b"\x01\x02\x03", 0)}],
        expected={"a": b"\x01\x02\x03"},
        msg="$arrayToObject should preserve Binary value",
    ),
    ArrayTestClass(
        id="kv_timestamp",
        arrays=[{"k": "a", "v": Timestamp(1234567890, 1)}],
        expected={"a": Timestamp(1234567890, 1)},
        msg="$arrayToObject should preserve Timestamp value",
    ),
    ArrayTestClass(
        id="kv_uuid",
        arrays=[{"k": "a", "v": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))}],
        expected={"a": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))},
        msg="$arrayToObject should preserve UUID binary value",
    ),
]

# Property [Value Types Pair]: $arrayToObject preserves each value's BSON type in pair form.
BSON_PAIR_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="pair_int64",
        arrays=[["a", Int64(99)]],
        expected={"a": Int64(99)},
        msg="$arrayToObject should preserve Int64 value (pair form)",
    ),
    ArrayTestClass(
        id="pair_decimal128",
        arrays=[["a", Decimal128("3.14")]],
        expected={"a": Decimal128("3.14")},
        msg="$arrayToObject should preserve Decimal128 value (pair form)",
    ),
    ArrayTestClass(
        id="pair_datetime",
        arrays=[["a", datetime(2024, 1, 1, tzinfo=timezone.utc)]],
        expected={"a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="$arrayToObject should preserve datetime value (pair form)",
    ),
    ArrayTestClass(
        id="pair_objectid",
        arrays=[["a", ObjectId("000000000000000000000001")]],
        expected={"a": ObjectId("000000000000000000000001")},
        msg="$arrayToObject should preserve ObjectId value (pair form)",
    ),
    ArrayTestClass(
        id="pair_binary",
        arrays=[["a", Binary(b"\x01\x02\x03", 0)]],
        expected={"a": b"\x01\x02\x03"},
        msg="$arrayToObject should preserve Binary value (pair form)",
    ),
    ArrayTestClass(
        id="pair_timestamp",
        arrays=[["a", Timestamp(1234567890, 1)]],
        expected={"a": Timestamp(1234567890, 1)},
        msg="$arrayToObject should preserve Timestamp value (pair form)",
    ),
    ArrayTestClass(
        id="pair_regex",
        arrays=[["a", Regex("^abc", "i")]],
        expected={"a": Regex("^abc", "i")},
        msg="$arrayToObject should preserve regex value (pair form)",
    ),
    ArrayTestClass(
        id="pair_minkey",
        arrays=[["a", MinKey()]],
        expected={"a": MinKey()},
        msg="$arrayToObject should preserve MinKey value (pair form)",
    ),
    ArrayTestClass(
        id="pair_maxkey",
        arrays=[["a", MaxKey()]],
        expected={"a": MaxKey()},
        msg="$arrayToObject should preserve MaxKey value (pair form)",
    ),
    ArrayTestClass(
        id="pair_uuid",
        arrays=[["a", Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))]],
        expected={"a": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))},
        msg="$arrayToObject should preserve UUID binary value (pair form)",
    ),
]

# Property [Special Numerics]: $arrayToObject preserves NaN, Infinity, and negative zero.
SPECIAL_NUMERIC_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="value_infinity",
        arrays=[{"k": "a", "v": FLOAT_INFINITY}],
        expected={"a": FLOAT_INFINITY},
        msg="$arrayToObject should preserve Infinity value",
    ),
    ArrayTestClass(
        id="value_neg_infinity",
        arrays=[{"k": "a", "v": FLOAT_NEGATIVE_INFINITY}],
        expected={"a": FLOAT_NEGATIVE_INFINITY},
        msg="$arrayToObject should preserve -Infinity value",
    ),
    ArrayTestClass(
        id="value_neg_zero",
        arrays=[{"k": "a", "v": DOUBLE_NEGATIVE_ZERO}],
        expected={"a": DOUBLE_NEGATIVE_ZERO},
        msg="$arrayToObject should preserve negative zero value",
    ),
    ArrayTestClass(
        id="value_decimal128_nan",
        arrays=[{"k": "a", "v": DECIMAL128_NAN}],
        expected={"a": DECIMAL128_NAN},
        msg="$arrayToObject should preserve Decimal128 NaN value",
    ),
    ArrayTestClass(
        id="value_decimal128_infinity",
        arrays=[{"k": "a", "v": DECIMAL128_INFINITY}],
        expected={"a": DECIMAL128_INFINITY},
        msg="$arrayToObject should preserve Decimal128 Infinity value",
    ),
    ArrayTestClass(
        id="value_decimal128_neg_infinity",
        arrays=[{"k": "a", "v": DECIMAL128_NEGATIVE_INFINITY}],
        expected={"a": DECIMAL128_NEGATIVE_INFINITY},
        msg="$arrayToObject should preserve Decimal128 -Infinity value",
    ),
    ArrayTestClass(
        id="value_decimal128_neg_zero",
        arrays=[{"k": "a", "v": DECIMAL128_NEGATIVE_ZERO}],
        expected={"a": DECIMAL128_NEGATIVE_ZERO},
        msg="$arrayToObject should preserve Decimal128 -0 value",
    ),
    ArrayTestClass(
        id="value_decimal128_high_precision",
        arrays=[{"k": "a", "v": Decimal128("1.234567890123456789012345678901234")}],
        expected={"a": Decimal128("1.234567890123456789012345678901234")},
        msg="$arrayToObject should preserve full Decimal128 precision",
    ),
    ArrayTestClass(
        id="value_decimal128_zero_exponent",
        arrays=[{"k": "a", "v": Decimal128("0E+10")}],
        expected={"a": Decimal128("0E+10")},
        msg="$arrayToObject should preserve Decimal128 exponent notation",
    ),
    ArrayTestClass(
        id="value_decimal128_trailing_zeros",
        arrays=[{"k": "a", "v": Decimal128("1.00000")}],
        expected={"a": Decimal128("1.00000")},
        msg="$arrayToObject should preserve Decimal128 trailing zeros",
    ),
    ArrayTestClass(
        id="value_decimal128_subnormal_zero",
        arrays=[{"k": "a", "v": Decimal128("0E-6176")}],
        expected={"a": Decimal128("0E-6176")},
        msg="$arrayToObject should preserve Decimal128 subnormal zero",
    ),
]

# Property [Numeric Boundaries]: $arrayToObject preserves numeric boundary values.
BOUNDARY_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="value_int32_max",
        arrays=[{"k": "a", "v": INT32_MAX}],
        expected={"a": INT32_MAX},
        msg="$arrayToObject should preserve INT32_MAX value",
    ),
    ArrayTestClass(
        id="value_int32_min",
        arrays=[{"k": "a", "v": INT32_MIN}],
        expected={"a": INT32_MIN},
        msg="$arrayToObject should preserve INT32_MIN value",
    ),
    ArrayTestClass(
        id="value_int64_max",
        arrays=[{"k": "a", "v": INT64_MAX}],
        expected={"a": INT64_MAX},
        msg="$arrayToObject should preserve INT64_MAX value",
    ),
    ArrayTestClass(
        id="value_int64_min",
        arrays=[{"k": "a", "v": INT64_MIN}],
        expected={"a": INT64_MIN},
        msg="$arrayToObject should preserve INT64_MIN value",
    ),
    ArrayTestClass(
        id="value_decimal128_max",
        arrays=[{"k": "a", "v": DECIMAL128_MAX}],
        expected={"a": DECIMAL128_MAX},
        msg="$arrayToObject should preserve DECIMAL128_MAX value",
    ),
    ArrayTestClass(
        id="value_decimal128_min",
        arrays=[{"k": "a", "v": DECIMAL128_MIN}],
        expected={"a": DECIMAL128_MIN},
        msg="$arrayToObject should preserve DECIMAL128_MIN value",
    ),
]

# Property [Nested Values]: $arrayToObject preserves nested arrays and documents as values.
NESTED_BSON_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="nested_bson_in_object_value",
        arrays=[{"k": "a", "v": {"x": Int64(1), "y": Decimal128("2.5")}}],
        expected={"a": {"x": Int64(1), "y": Decimal128("2.5")}},
        msg="$arrayToObject should preserve nested BSON types in object value",
    ),
    ArrayTestClass(
        id="nested_bson_in_array_value",
        arrays=[
            {
                "k": "a",
                "v": [
                    MinKey(),
                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                    ObjectId("000000000000000000000001"),
                ],
            }
        ],
        expected={
            "a": [
                MinKey(),
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                ObjectId("000000000000000000000001"),
            ]
        },
        msg="$arrayToObject should preserve nested BSON types in array value",
    ),
    ArrayTestClass(
        id="deeply_nested_bson",
        arrays=[{"k": "a", "v": {"x": [{"y": Decimal128("1.5")}, Timestamp(0, 0)]}}],
        expected={"a": {"x": [{"y": Decimal128("1.5")}, Timestamp(0, 0)]}},
        msg="$arrayToObject should preserve deeply nested BSON types",
    ),
    ArrayTestClass(
        id="nested_array_not_interpreted_as_kv",
        arrays=[{"k": "a", "v": [["level2", {"x": 1}]]}],
        expected={"a": [["level2", {"x": 1}]]},
        msg="$arrayToObject should preserve nested array as value without interpreting as k/v",
    ),
]

# Property [Duplicate Numeric Keys]: last value wins for duplicate keys of differing numeric types.
NUMERIC_EQUIVALENCE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="duplicate_key_int_then_int64",
        arrays=[{"k": "a", "v": 1}, {"k": "a", "v": Int64(2)}],
        expected={"a": Int64(2)},
        msg="$arrayToObject should keep the last Int64 value for a duplicate key",
    ),
    ArrayTestClass(
        id="duplicate_key_int_then_decimal128",
        arrays=[{"k": "a", "v": 1}, {"k": "a", "v": Decimal128("2")}],
        expected={"a": Decimal128("2")},
        msg="$arrayToObject should keep the last Decimal128 value for a duplicate key",
    ),
    ArrayTestClass(
        id="duplicate_key_decimal128_then_double",
        arrays=[{"k": "a", "v": Decimal128("1")}, {"k": "a", "v": 2.0}],
        expected={"a": 2.0},
        msg="$arrayToObject should keep the last double value for a duplicate key",
    ),
]

# Property [Mixed Types]: $arrayToObject preserves multiple mixed BSON value types in one array.
MIXED_BSON_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="kv_mixed_bson_types",
        arrays=[
            {"k": "int64", "v": Int64(1)},
            {"k": "dec", "v": Decimal128("1.5")},
            {"k": "dt", "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"k": "oid", "v": ObjectId("000000000000000000000001")},
            {"k": "bin", "v": Binary(b"\x01", 0)},
            {"k": "ts", "v": Timestamp(0, 0)},
            {"k": "min", "v": MinKey()},
        ],
        expected={
            "int64": Int64(1),
            "dec": Decimal128("1.5"),
            "dt": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "oid": ObjectId("000000000000000000000001"),
            "bin": b"\x01",
            "ts": Timestamp(0, 0),
            "min": MinKey(),
        },
        msg="$arrayToObject should preserve multiple mixed BSON types in one conversion",
    ),
]

ALL_BSON_TESTS = (
    BSON_KV_TESTS
    + BSON_PAIR_TESTS
    + SPECIAL_NUMERIC_TESTS
    + BOUNDARY_TESTS
    + NESTED_BSON_TESTS
    + NUMERIC_EQUIVALENCE_TESTS
    + MIXED_BSON_TESTS
)

TEST_SUBSET_FOR_LITERAL = [
    BSON_KV_TESTS[0],
    BSON_KV_TESTS[10],
    BSON_KV_TESTS[12],
    BSON_PAIR_TESTS[0],
    SPECIAL_NUMERIC_TESTS[0],
    BOUNDARY_TESTS[0],
    NESTED_BSON_TESTS[0],
    MIXED_BSON_TESTS[0],
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayToObject_bson_literal(collection, test):
    """Test $arrayToObject BSON types with literal values."""
    result = execute_expression(collection, {"$arrayToObject": {"$literal": test.arrays}})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_arrayToObject_bson_insert(collection, test):
    """Test $arrayToObject BSON types with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayToObject": "$arr"}, {"arr": test.arrays}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Float NaN needs a dedicated test because NaN does not compare equal to itself.
def test_arrayToObject_float_nan_value(collection):
    """Test $arrayToObject preserves float NaN value."""
    result = execute_expression(collection, {"$arrayToObject": {"$literal": [["a", float("nan")]]}})
    assert_expression_result(
        result,
        expected={"a": pytest.approx(math.nan, nan_ok=True)},
        msg="$arrayToObject should preserve a NaN value",
    )
