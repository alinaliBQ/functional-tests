"""
BSON type tests for $arrayToObject expression.

Tests that various BSON value types are preserved when converting
arrays to objects, including special numeric values, boundary values,
UUID binary, nested BSON values, and numeric type equivalence,
across both k/v and pair input forms.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.arrayToObject.utils.arrayToObject_common import (  # noqa: E501
    ArrayToObjectTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
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

# ---------------------------------------------------------------------------
# BSON value types preserved (k/v form)
# ---------------------------------------------------------------------------
BSON_KV_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="kv_int64",
        array=[{"k": "a", "v": Int64(99)}],
        expected={"a": Int64(99)},
        msg="Should preserve Int64 value",
    ),
    ArrayToObjectTest(
        id="kv_decimal128",
        array=[{"k": "a", "v": Decimal128("3.14")}],
        expected={"a": Decimal128("3.14")},
        msg="Should preserve Decimal128 value",
    ),
    ArrayToObjectTest(
        id="kv_datetime",
        array=[{"k": "a", "v": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        expected={"a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="Should preserve datetime value",
    ),
    ArrayToObjectTest(
        id="kv_objectid",
        array=[{"k": "a", "v": ObjectId("000000000000000000000001")}],
        expected={"a": ObjectId("000000000000000000000001")},
        msg="Should preserve ObjectId value",
    ),
    ArrayToObjectTest(
        id="kv_bool_false",
        array=[{"k": "a", "v": False}],
        expected={"a": False},
        msg="Should preserve false value",
    ),
    ArrayToObjectTest(
        id="kv_bool_true",
        array=[{"k": "a", "v": True}],
        expected={"a": True},
        msg="Should preserve true value",
    ),
    ArrayToObjectTest(
        id="kv_null",
        array=[{"k": "a", "v": None}],
        expected={"a": None},
        msg="Should preserve null value",
    ),
    ArrayToObjectTest(
        id="kv_regex",
        array=[{"k": "a", "v": Regex("^abc", "i")}],
        expected={"a": Regex("^abc", "i")},
        msg="Should preserve regex value",
    ),
    ArrayToObjectTest(
        id="kv_minkey",
        array=[{"k": "a", "v": MinKey()}],
        expected={"a": MinKey()},
        msg="Should preserve MinKey value",
    ),
    ArrayToObjectTest(
        id="kv_maxkey",
        array=[{"k": "a", "v": MaxKey()}],
        expected={"a": MaxKey()},
        msg="Should preserve MaxKey value",
    ),
    ArrayToObjectTest(
        id="kv_binary",
        array=[{"k": "a", "v": Binary(b"\x01\x02\x03", 0)}],
        expected={"a": b"\x01\x02\x03"},
        msg="Should preserve Binary value",
    ),
    ArrayToObjectTest(
        id="kv_timestamp",
        array=[{"k": "a", "v": Timestamp(1234567890, 1)}],
        expected={"a": Timestamp(1234567890, 1)},
        msg="Should preserve Timestamp value",
    ),
    ArrayToObjectTest(
        id="kv_uuid",
        array=[{"k": "a", "v": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))}],
        expected={"a": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))},
        msg="Should preserve UUID binary value",
    ),
]

# ---------------------------------------------------------------------------
# BSON value types preserved (pair form)
# ---------------------------------------------------------------------------
BSON_PAIR_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="pair_int64",
        array=[["a", Int64(99)]],
        expected={"a": Int64(99)},
        msg="Should preserve Int64 value (pair form)",
    ),
    ArrayToObjectTest(
        id="pair_decimal128",
        array=[["a", Decimal128("3.14")]],
        expected={"a": Decimal128("3.14")},
        msg="Should preserve Decimal128 value (pair form)",
    ),
    ArrayToObjectTest(
        id="pair_datetime",
        array=[["a", datetime(2024, 1, 1, tzinfo=timezone.utc)]],
        expected={"a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="Should preserve datetime value (pair form)",
    ),
    ArrayToObjectTest(
        id="pair_objectid",
        array=[["a", ObjectId("000000000000000000000001")]],
        expected={"a": ObjectId("000000000000000000000001")},
        msg="Should preserve ObjectId value (pair form)",
    ),
    ArrayToObjectTest(
        id="pair_binary",
        array=[["a", Binary(b"\x01\x02\x03", 0)]],
        expected={"a": b"\x01\x02\x03"},
        msg="Should preserve Binary value (pair form)",
    ),
    ArrayToObjectTest(
        id="pair_timestamp",
        array=[["a", Timestamp(1234567890, 1)]],
        expected={"a": Timestamp(1234567890, 1)},
        msg="Should preserve Timestamp value (pair form)",
    ),
    ArrayToObjectTest(
        id="pair_regex",
        array=[["a", Regex("^abc", "i")]],
        expected={"a": Regex("^abc", "i")},
        msg="Should preserve regex value (pair form)",
    ),
    ArrayToObjectTest(
        id="pair_minkey",
        array=[["a", MinKey()]],
        expected={"a": MinKey()},
        msg="Should preserve MinKey value (pair form)",
    ),
    ArrayToObjectTest(
        id="pair_maxkey",
        array=[["a", MaxKey()]],
        expected={"a": MaxKey()},
        msg="Should preserve MaxKey value (pair form)",
    ),
    ArrayToObjectTest(
        id="pair_uuid",
        array=[["a", Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))]],
        expected={"a": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))},
        msg="Should preserve UUID binary value (pair form)",
    ),
]

# ---------------------------------------------------------------------------
# Special numeric values
# ---------------------------------------------------------------------------
SPECIAL_NUMERIC_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="value_infinity",
        array=[{"k": "a", "v": FLOAT_INFINITY}],
        expected={"a": FLOAT_INFINITY},
        msg="Should preserve Infinity value",
    ),
    ArrayToObjectTest(
        id="value_neg_infinity",
        array=[{"k": "a", "v": FLOAT_NEGATIVE_INFINITY}],
        expected={"a": FLOAT_NEGATIVE_INFINITY},
        msg="Should preserve -Infinity value",
    ),
    ArrayToObjectTest(
        id="value_neg_zero",
        array=[{"k": "a", "v": DOUBLE_NEGATIVE_ZERO}],
        expected={"a": DOUBLE_NEGATIVE_ZERO},
        msg="Should preserve negative zero value",
    ),
    ArrayToObjectTest(
        id="value_decimal128_nan",
        array=[{"k": "a", "v": DECIMAL128_NAN}],
        expected={"a": DECIMAL128_NAN},
        msg="Should preserve Decimal128 NaN value",
    ),
    ArrayToObjectTest(
        id="value_decimal128_infinity",
        array=[{"k": "a", "v": DECIMAL128_INFINITY}],
        expected={"a": DECIMAL128_INFINITY},
        msg="Should preserve Decimal128 Infinity value",
    ),
    ArrayToObjectTest(
        id="value_decimal128_neg_infinity",
        array=[{"k": "a", "v": DECIMAL128_NEGATIVE_INFINITY}],
        expected={"a": DECIMAL128_NEGATIVE_INFINITY},
        msg="Should preserve Decimal128 -Infinity value",
    ),
    ArrayToObjectTest(
        id="value_decimal128_neg_zero",
        array=[{"k": "a", "v": DECIMAL128_NEGATIVE_ZERO}],
        expected={"a": DECIMAL128_NEGATIVE_ZERO},
        msg="Should preserve Decimal128 -0 value",
    ),
    ArrayToObjectTest(
        id="value_decimal128_high_precision",
        array=[{"k": "a", "v": Decimal128("1.234567890123456789012345678901234")}],
        expected={"a": Decimal128("1.234567890123456789012345678901234")},
        msg="Should preserve full Decimal128 precision",
    ),
    ArrayToObjectTest(
        id="value_decimal128_zero_exponent",
        array=[{"k": "a", "v": Decimal128("0E+10")}],
        expected={"a": Decimal128("0E+10")},
        msg="Should preserve Decimal128 exponent notation",
    ),
    ArrayToObjectTest(
        id="value_decimal128_trailing_zeros",
        array=[{"k": "a", "v": Decimal128("1.00000")}],
        expected={"a": Decimal128("1.00000")},
        msg="Should preserve Decimal128 trailing zeros",
    ),
    ArrayToObjectTest(
        id="value_decimal128_subnormal_zero",
        array=[{"k": "a", "v": Decimal128("0E-6176")}],
        expected={"a": Decimal128("0E-6176")},
        msg="Should preserve Decimal128 subnormal zero",
    ),
]

# ---------------------------------------------------------------------------
# Boundary values
# ---------------------------------------------------------------------------
BOUNDARY_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="value_int32_max",
        array=[{"k": "a", "v": INT32_MAX}],
        expected={"a": INT32_MAX},
        msg="Should preserve INT32_MAX value",
    ),
    ArrayToObjectTest(
        id="value_int32_min",
        array=[{"k": "a", "v": INT32_MIN}],
        expected={"a": INT32_MIN},
        msg="Should preserve INT32_MIN value",
    ),
    ArrayToObjectTest(
        id="value_int64_max",
        array=[{"k": "a", "v": INT64_MAX}],
        expected={"a": INT64_MAX},
        msg="Should preserve INT64_MAX value",
    ),
    ArrayToObjectTest(
        id="value_int64_min",
        array=[{"k": "a", "v": INT64_MIN}],
        expected={"a": INT64_MIN},
        msg="Should preserve INT64_MIN value",
    ),
    ArrayToObjectTest(
        id="value_decimal128_max",
        array=[{"k": "a", "v": DECIMAL128_MAX}],
        expected={"a": DECIMAL128_MAX},
        msg="Should preserve DECIMAL128_MAX value",
    ),
    ArrayToObjectTest(
        id="value_decimal128_min",
        array=[{"k": "a", "v": DECIMAL128_MIN}],
        expected={"a": DECIMAL128_MIN},
        msg="Should preserve DECIMAL128_MIN value",
    ),
]

# ---------------------------------------------------------------------------
# Nested BSON values
# ---------------------------------------------------------------------------
NESTED_BSON_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="nested_bson_in_object_value",
        array=[{"k": "a", "v": {"x": Int64(1), "y": Decimal128("2.5")}}],
        expected={"a": {"x": Int64(1), "y": Decimal128("2.5")}},
        msg="Should preserve nested BSON types in object value",
    ),
    ArrayToObjectTest(
        id="nested_bson_in_array_value",
        array=[
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
        msg="Should preserve nested BSON types in array value",
    ),
    ArrayToObjectTest(
        id="deeply_nested_bson",
        array=[{"k": "a", "v": {"x": [{"y": Decimal128("1.5")}, Timestamp(0, 0)]}}],
        expected={"a": {"x": [{"y": Decimal128("1.5")}, Timestamp(0, 0)]}},
        msg="Should preserve deeply nested BSON types",
    ),
    ArrayToObjectTest(
        id="nested_array_not_interpreted_as_kv",
        array=[{"k": "a", "v": [["level2", {"x": 1}]]}],
        expected={"a": [["level2", {"x": 1}]]},
        msg="Should preserve nested array as value without interpreting as k/v",
    ),
]

# ---------------------------------------------------------------------------
# Numeric type equivalence — duplicate keys with different numeric types
# ---------------------------------------------------------------------------
NUMERIC_EQUIVALENCE_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="duplicate_key_int_then_int64",
        array=[{"k": "a", "v": 1}, {"k": "a", "v": Int64(2)}],
        expected={"a": Int64(2)},
        msg="Int64 value should win as last duplicate key",
    ),
    ArrayToObjectTest(
        id="duplicate_key_int_then_decimal128",
        array=[{"k": "a", "v": 1}, {"k": "a", "v": Decimal128("2")}],
        expected={"a": Decimal128("2")},
        msg="Decimal128 value should win as last duplicate key",
    ),
    ArrayToObjectTest(
        id="duplicate_key_decimal128_then_double",
        array=[{"k": "a", "v": Decimal128("1")}, {"k": "a", "v": 2.0}],
        expected={"a": 2.0},
        msg="Double value should win as last duplicate key",
    ),
]

# ---------------------------------------------------------------------------
# Mixed BSON types in a single array
# ---------------------------------------------------------------------------
MIXED_BSON_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="kv_mixed_bson_types",
        array=[
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
        msg="Should preserve multiple mixed BSON types in one conversion",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
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
    BSON_KV_TESTS[0],  # kv_int64
    BSON_KV_TESTS[10],  # kv_binary
    BSON_KV_TESTS[12],  # kv_uuid
    BSON_PAIR_TESTS[0],  # pair_int64
    SPECIAL_NUMERIC_TESTS[0],  # value_infinity
    BOUNDARY_TESTS[0],  # value_int32_max
    NESTED_BSON_TESTS[0],  # nested_bson_in_object_value
    MIXED_BSON_TESTS[0],  # kv_mixed_bson_types
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayToObject_bson_literal(collection, test):
    """Test $arrayToObject BSON types with literal values."""
    result = execute_expression(collection, {"$arrayToObject": {"$literal": test.array}})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_arrayToObject_bson_insert(collection, test):
    """Test $arrayToObject BSON types with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayToObject": "$arr"}, {"arr": test.array}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# ---------------------------------------------------------------------------
# Float NaN — requires special handling since nan != nan
# ---------------------------------------------------------------------------
def test_arrayToObject_float_nan_value(collection):
    """Test $arrayToObject preserves float NaN value."""
    import math

    result = execute_expression(collection, {"$arrayToObject": {"$literal": [["a", float("nan")]]}})
    assertSuccess(
        result,
        expected=[{"result": True}],
        transform=lambda batch: [{"result": math.isnan(batch[0]["result"]["a"])}],
        msg="NaN value should be preserved",
    )
