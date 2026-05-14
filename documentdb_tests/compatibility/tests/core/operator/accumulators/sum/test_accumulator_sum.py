"""Tests for $sum accumulator in $group stage."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_common import (  # noqa: E501
    execute_accumulator,
)
from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    ACCUMULATOR_UNARY_OPERATOR_ERROR,
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_COEFFICIENT,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

# Property [Null and Missing Behavior]: null and missing values are ignored by
# $sum, producing 0 (int32) when no numeric values remain.
SUM_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=0,
        msg="$sum should return 0 when all values are null",
    ),
    AccumulatorTestCase(
        "missing_all",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=0,
        msg="$sum should return 0 when all documents have missing field",
    ),
    AccumulatorTestCase(
        "null_and_missing_mix",
        docs=[{"v": None}, {"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=0,
        msg="$sum should return 0 when group has only null and missing values",
    ),
    AccumulatorTestCase(
        "null_with_numeric",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=8,
        msg="$sum should ignore null and sum only numeric values",
    ),
    AccumulatorTestCase(
        "missing_with_numeric",
        docs=[{"x": 1}, {"v": 7}, {"v": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=9,
        msg="$sum should ignore missing and sum only numeric values",
    ),
    AccumulatorTestCase(
        "null_and_missing_with_numeric",
        docs=[{"v": None}, {"x": 1}, {"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=10,
        msg="$sum should ignore both null and missing, summing only numeric values",
    ),
    AccumulatorTestCase(
        "constant_null",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": None}}}],
        expected=0,
        msg="$sum should return 0 for a constant null expression",
    ),
    AccumulatorTestCase(
        "literal_null_expr",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$literal": None}}}}],
        expected=0,
        msg="$sum should return 0 when expression evaluates to null",
    ),
    AccumulatorTestCase(
        "remove_only",
        docs=[{"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$cond": [False, 1, "$$REMOVE"]}}}}],
        expected=0,
        msg="$sum should treat $$REMOVE as missing and return 0",
    ),
]

# Property [Non-Numeric Type Handling]: non-numeric BSON types are silently
# ignored by $sum, contributing nothing to the result.
SUM_NON_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "non_numeric_string_ignored",
        docs=[{"v": "hello"}, {"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=10,
        msg="$sum should ignore string values and sum only numeric values",
    ),
    AccumulatorTestCase(
        "non_numeric_bool_true_ignored",
        docs=[{"v": True}, {"v": 7}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=7,
        msg="$sum should ignore boolean True (not coerce to 1)",
    ),
    AccumulatorTestCase(
        "non_numeric_bool_false_ignored",
        docs=[{"v": False}, {"v": 3}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=3,
        msg="$sum should ignore boolean False (not coerce to 0)",
    ),
    AccumulatorTestCase(
        "non_numeric_array_ignored",
        docs=[{"v": ["a", "b"]}, {"v": 4}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=4,
        msg="$sum should ignore array values",
    ),
    AccumulatorTestCase(
        "non_numeric_object_ignored",
        docs=[{"v": {"a": 1}}, {"v": 6}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=6,
        msg="$sum should ignore embedded object values",
    ),
    AccumulatorTestCase(
        "non_numeric_empty_object_ignored",
        docs=[{"v": {}}, {"v": 4}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=4,
        msg="$sum should ignore empty document values",
    ),
    AccumulatorTestCase(
        "non_numeric_objectid_ignored",
        docs=[{"v": ObjectId()}, {"v": 8}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=8,
        msg="$sum should ignore ObjectId values",
    ),
    AccumulatorTestCase(
        "non_numeric_datetime_ignored",
        docs=[{"v": datetime(2023, 1, 1, tzinfo=timezone.utc)}, {"v": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=2,
        msg="$sum should ignore datetime values",
    ),
    AccumulatorTestCase(
        "non_numeric_timestamp_ignored",
        docs=[{"v": Timestamp(1, 1)}, {"v": 9}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=9,
        msg="$sum should ignore Timestamp values",
    ),
    AccumulatorTestCase(
        "non_numeric_binary_ignored",
        docs=[{"v": Binary(b"\x01\x02")}, {"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=5,
        msg="$sum should ignore Binary values",
    ),
    AccumulatorTestCase(
        "non_numeric_regex_ignored",
        docs=[{"v": Regex("abc", "i")}, {"v": 11}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=11,
        msg="$sum should ignore Regex values",
    ),
    AccumulatorTestCase(
        "non_numeric_code_ignored",
        docs=[{"v": Code("function(){}")}, {"v": 12}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=12,
        msg="$sum should ignore Code values",
    ),
    AccumulatorTestCase(
        "non_numeric_minkey_ignored",
        docs=[{"v": MinKey()}, {"v": 14}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=14,
        msg="$sum should ignore MinKey values",
    ),
    AccumulatorTestCase(
        "non_numeric_maxkey_ignored",
        docs=[{"v": MaxKey()}, {"v": 15}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=15,
        msg="$sum should ignore MaxKey values",
    ),
    AccumulatorTestCase(
        "non_numeric_all_non_numeric",
        docs=[{"v": "abc"}, {"v": True}, {"v": [1]}, {"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=0,
        msg="$sum should return 0 when all values in a group are non-numeric",
    ),
    AccumulatorTestCase(
        "non_numeric_numeric_string_not_coerced",
        docs=[{"v": "123"}, {"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=5,
        msg="$sum should not coerce numeric strings to numbers",
    ),
    AccumulatorTestCase(
        "non_numeric_array_single_element",
        docs=[{"v": [5]}, {"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=10,
        msg="$sum should treat single-element numeric array as non-numeric",
    ),
    AccumulatorTestCase(
        "non_numeric_array_empty",
        docs=[{"v": []}, {"v": 7}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=7,
        msg="$sum should treat empty array as non-numeric",
    ),
    AccumulatorTestCase(
        "non_numeric_array_nested",
        docs=[{"v": [[1, 2]]}, {"v": 3}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=3,
        msg="$sum should treat nested array as non-numeric",
    ),
    AccumulatorTestCase(
        "non_numeric_array_of_numbers",
        docs=[{"v": [1, 2, 3]}, {"v": 20}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=20,
        msg="$sum should treat array of numbers as non-numeric in accumulator context",
    ),
    AccumulatorTestCase(
        "non_numeric_array_from_expression",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$literal": [1, 2, 3]}}}}],
        expected=0,
        msg="$sum should treat array expressions as non-numeric",
    ),
]

# Property [Special Float Values]: NaN propagates through summation and
# dominates all other values; inf + (-inf) produces NaN; inf + inf produces
# inf; inf + finite produces inf; non-numeric values are ignored.
SUM_SPECIAL_FLOAT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "special_float_inf_plus_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=FLOAT_INFINITY,
        msg="$sum should produce inf when summing inf + inf",
    ),
    AccumulatorTestCase(
        "special_float_neg_inf_plus_neg_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should produce -inf when summing -inf + -inf",
    ),
    AccumulatorTestCase(
        "special_float_inf_plus_finite",
        docs=[{"v": FLOAT_INFINITY}, {"v": 42.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=FLOAT_INFINITY,
        msg="$sum should produce inf when summing inf + finite",
    ),
    AccumulatorTestCase(
        "special_float_neg_inf_plus_finite",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": 42.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should produce -inf when summing -inf + finite",
    ),
    AccumulatorTestCase(
        "special_float_nan_propagates",
        docs=[{"v": FLOAT_NAN}, {"v": 5.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should propagate NaN through summation",
    ),
    AccumulatorTestCase(
        "special_float_nan_dominates_inf",
        docs=[{"v": FLOAT_NAN}, {"v": FLOAT_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should produce NaN when NaN is summed with inf",
    ),
    AccumulatorTestCase(
        "special_float_inf_plus_neg_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should produce NaN for inf + (-inf) indeterminate form",
    ),
    AccumulatorTestCase(
        "special_float_non_numeric_with_nan",
        docs=[{"v": "hello"}, {"v": FLOAT_NAN}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should ignore non-numeric values and preserve NaN",
    ),
]

# Property [Decimal128 Special Values]: Decimal128 NaN propagates through
# summation, Decimal128 Infinity + Decimal128 -Infinity produces Decimal128
# NaN, and Decimal128 Infinity + Decimal128 Infinity produces Decimal128
# Infinity.
SUM_DECIMAL128_SPECIAL_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal128_special_nan_propagates",
        docs=[{"v": DECIMAL128_NAN}, {"v": Decimal128("5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DECIMAL128_NAN,
        msg="$sum should propagate Decimal128 NaN through summation",
    ),
    AccumulatorTestCase(
        "decimal128_special_inf_plus_neg_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_NEGATIVE_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DECIMAL128_NAN,
        msg="$sum should produce Decimal128 NaN for Decimal128 Infinity + -Infinity",
    ),
    AccumulatorTestCase(
        "decimal128_special_inf_plus_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DECIMAL128_INFINITY,
        msg="$sum should produce Decimal128 Infinity for Decimal128 Infinity + Infinity",
    ),
]

# Property [Precision]: Decimal128 provides exact arithmetic and preserves
# trailing zeros based on the highest-precision operand, while double follows
# IEEE 754 rules with precision loss for large values and correct handling of
# subnormal values.
SUM_PRECISION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "precision_decimal128_exact",
        docs=[{"v": Decimal128("0.1")} for _ in range(100)],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=Decimal128("10.0"),
        msg="$sum should produce exact Decimal128 result for 100 x 0.1",
    ),
    AccumulatorTestCase(
        "precision_decimal128_trailing_zeros",
        docs=[{"v": Decimal128("1.100")}, {"v": Decimal128("2.20")}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=Decimal128("3.300"),
        msg="$sum should preserve trailing zeros based on highest-precision operand",
    ),
    AccumulatorTestCase(
        "precision_double_accumulation",
        docs=[{"v": 0.1} for _ in range(100)],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=10.0,
        msg="$sum should produce 10.0 for 100 x double 0.1 due to accumulation",
    ),
    AccumulatorTestCase(
        "precision_double_loss_large_value",
        docs=[{"v": 1e16}, {"v": 1.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=1e16,
        msg="$sum should lose precision for double when adding 1.0 to 1e16",
    ),
    AccumulatorTestCase(
        "precision_int64_max_plus_decimal128_exact",
        docs=[{"v": INT64_MAX}, {"v": Decimal128("1")}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DECIMAL128_INT64_OVERFLOW,
        msg="$sum should preserve exact value for Int64_max + Decimal128(1)",
    ),
    AccumulatorTestCase(
        "precision_int64_max_plus_double_loses",
        docs=[{"v": INT64_MAX}, {"v": 1.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DOUBLE_FROM_INT64_MAX,
        msg="$sum should lose precision for Int64_max + double(1.0)",
    ),
    AccumulatorTestCase(
        "precision_subnormal_double_addition",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": DOUBLE_MIN_SUBNORMAL}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=1e-323,
        msg="$sum should correctly add subnormal double values",
    ),
    AccumulatorTestCase(
        "precision_subnormal_double_negative",
        docs=[{"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}, {"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=-1e-323,
        msg="$sum should correctly add negative subnormal double values",
    ),
    AccumulatorTestCase(
        "precision_subnormal_double_cancellation",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DOUBLE_ZERO,
        msg="$sum should produce 0.0 when subnormal values cancel",
    ),
    AccumulatorTestCase(
        "precision_decimal128_subnormal",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": DECIMAL128_MIN_POSITIVE}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=Decimal128("2E-6176"),
        msg="$sum should correctly add Decimal128 subnormal values",
    ),
    AccumulatorTestCase(
        "precision_decimal128_large_exponent",
        docs=[{"v": DECIMAL128_LARGE_EXPONENT}, {"v": DECIMAL128_LARGE_EXPONENT}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=Decimal128("2.000000000000000000000000000000000E+6144"),
        msg="$sum should correctly add Decimal128 large exponent values",
    ),
    AccumulatorTestCase(
        "precision_decimal128_34_digit_overflow",
        docs=[{"v": DECIMAL128_MAX_COEFFICIENT}, {"v": Decimal128("1")}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=Decimal128("1.000000000000000000000000000000000E+34"),
        msg="$sum should round correctly when Decimal128 34-digit precision overflows",
    ),
]

# Property [Constant Expression Behavior]: a numeric constant counts documents
# by multiplying the constant by the group size; a non-numeric constant
# produces 0 (int32); NaN and Infinity constants propagate.
SUM_CONSTANT_EXPRESSION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "constant_int32",
        docs=[{"x": 1}, {"x": 2}, {"x": 3}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": 1}}}],
        expected=3,
        msg="$sum should count documents when given an int32 constant",
    ),
    AccumulatorTestCase(
        "constant_int32_larger",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": 5}}}],
        expected=10,
        msg="$sum should multiply int32 constant by group size",
    ),
    AccumulatorTestCase(
        "constant_non_numeric_true",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": True}}}],
        expected=0,
        msg="$sum should return 0 for non-numeric constant True",
    ),
    AccumulatorTestCase(
        "constant_non_numeric_false",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": False}}}],
        expected=0,
        msg="$sum should return 0 for non-numeric constant False",
    ),
    AccumulatorTestCase(
        "constant_non_numeric_string",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "hello"}}}],
        expected=0,
        msg="$sum should return 0 for non-numeric string constant without $",
    ),
    AccumulatorTestCase(
        "constant_non_numeric_empty_object",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {}}}}],
        expected=0,
        msg="$sum should return 0 for empty object constant",
    ),
    AccumulatorTestCase(
        "constant_non_numeric_non_operator_object",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"a": 1}}}}],
        expected=0,
        msg="$sum should return 0 for non-operator object constant",
    ),
    AccumulatorTestCase(
        "constant_nan_propagates",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": FLOAT_NAN}}}],
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should propagate NaN constant",
    ),
    AccumulatorTestCase(
        "constant_inf_propagates",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": FLOAT_INFINITY}}}],
        expected=FLOAT_INFINITY,
        msg="$sum should propagate infinity constant",
    ),
    AccumulatorTestCase(
        "constant_neg_inf_propagates",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": FLOAT_NEGATIVE_INFINITY}}}],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should propagate negative infinity constant",
    ),
]

# Property [Expression Arguments]: $sum accepts any expression that resolves
# to a value; numeric results are summed, non-numeric results are ignored, and
# nested $sum (array summation) is supported.
SUM_EXPRESSION_ARGS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_args_arithmetic_expression",
        docs=[{"a": 3, "b": 2}, {"a": 5, "b": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$add": ["$a", "$b"]}}}}],
        expected=11,
        msg="$sum should accept an arithmetic expression and sum its numeric results",
    ),
    AccumulatorTestCase(
        "expr_args_non_numeric_expression_ignored",
        docs=[{"a": "hello", "b": " world"}, {"a": "foo", "b": "bar"}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$concat": ["$a", "$b"]}}}}],
        expected=0,
        msg="$sum should ignore non-numeric expression results and return 0",
    ),
    AccumulatorTestCase(
        "expr_args_nested_sum_array",
        docs=[{"v": [1, 2, 3]}, {"v": [4, 5]}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$sum": "$v"}}}}],
        expected=15,
        msg="$sum should accept nested $sum (array summation) as its expression",
    ),
]

SUM_TESTS = (
    SUM_NULL_MISSING_TESTS
    + SUM_NON_NUMERIC_TESTS
    + SUM_SPECIAL_FLOAT_TESTS
    + SUM_DECIMAL128_SPECIAL_TESTS
    + SUM_PRECISION_TESTS
    + SUM_CONSTANT_EXPRESSION_TESTS
    + SUM_EXPRESSION_ARGS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_TESTS))
def test_accumulator_sum(collection, test_case: AccumulatorTestCase):
    """Test $sum accumulator cases."""
    result = execute_accumulator(collection, test_case.docs, test_case.pipeline)
    assertSuccess(
        result,
        [{"result": test_case.expected}],
        msg=test_case.msg,
        transform=lambda docs: [{"result": docs[0]["result"]}],
    )


# Property [Return Type and Type Promotion]: the result type is the widest
# numeric type present in the group following int32 < Int64 < double < Decimal128,
# with no demotion.
SUM_TYPE_PROMOTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_single_int32",
        docs=[{"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 5, "type": "int"},
        msg="$sum should preserve int32 type for a single int32 value",
    ),
    AccumulatorTestCase(
        "type_single_int64",
        docs=[{"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(5), "type": "long"},
        msg="$sum should preserve Int64 type for a single Int64 value",
    ),
    AccumulatorTestCase(
        "type_single_double",
        docs=[{"v": 5.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 5.5, "type": "double"},
        msg="$sum should preserve double type for a single double value",
    ),
    AccumulatorTestCase(
        "type_single_decimal128",
        docs=[{"v": Decimal128("5.5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Decimal128("5.5"), "type": "decimal"},
        msg="$sum should preserve Decimal128 type for a single Decimal128 value",
    ),
    AccumulatorTestCase(
        "type_int32_int64_promotes",
        docs=[{"v": 5}, {"v": Int64(10)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(15), "type": "long"},
        msg="$sum should promote int32 + Int64 to Int64",
    ),
    AccumulatorTestCase(
        "type_int32_double_promotes",
        docs=[{"v": 5}, {"v": 2.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 7.5, "type": "double"},
        msg="$sum should promote int32 + double to double",
    ),
    AccumulatorTestCase(
        "type_int64_double_promotes",
        docs=[{"v": Int64(5)}, {"v": 2.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 7.5, "type": "double"},
        msg="$sum should promote Int64 + double to double",
    ),
    AccumulatorTestCase(
        "type_int32_decimal128_promotes",
        docs=[{"v": 5}, {"v": DECIMAL128_TWO_AND_HALF}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Decimal128("7.5"), "type": "decimal"},
        msg="$sum should promote int32 + Decimal128 to Decimal128",
    ),
    AccumulatorTestCase(
        "type_int64_decimal128_promotes",
        docs=[{"v": Int64(5)}, {"v": Decimal128("3")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Decimal128("8"), "type": "decimal"},
        msg="$sum should promote Int64 + Decimal128 to Decimal128",
    ),
    AccumulatorTestCase(
        "type_double_decimal128_promotes",
        docs=[{"v": 2.5}, {"v": Decimal128("3.5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Decimal128("6.0"), "type": "decimal"},
        msg="$sum should promote double + Decimal128 to Decimal128",
    ),
    AccumulatorTestCase(
        "type_no_demotion_int64_fits_int32",
        docs=[{"v": Int64(1)}, {"v": Int64(2)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(3), "type": "long"},
        msg="$sum should not demote Int64 to int32 even when result fits int32",
    ),
    AccumulatorTestCase(
        "type_all_non_numeric_is_int32",
        docs=[{"v": "abc"}, {"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 0, "type": "int"},
        msg="$sum should return int32 zero when all values are non-numeric",
    ),
]

# Property [Overflow Behavior]: double and Decimal128 overflow produces
# infinity without type promotion.
SUM_OVERFLOW_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "overflow_double_positive",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": FLOAT_INFINITY, "type": "double"},
        msg="$sum should produce positive infinity on double overflow",
    ),
    AccumulatorTestCase(
        "overflow_double_negative",
        docs=[{"v": DOUBLE_MIN}, {"v": DOUBLE_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": FLOAT_NEGATIVE_INFINITY, "type": "double"},
        msg="$sum should produce negative infinity on double overflow",
    ),
    AccumulatorTestCase(
        "overflow_decimal128_positive",
        docs=[{"v": DECIMAL128_MAX}, {"v": DECIMAL128_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INFINITY, "type": "decimal"},
        msg="$sum should produce Decimal128 Infinity on positive overflow",
    ),
    AccumulatorTestCase(
        "overflow_decimal128_negative",
        docs=[{"v": DECIMAL128_MIN}, {"v": DECIMAL128_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_NEGATIVE_INFINITY, "type": "decimal"},
        msg="$sum should produce Decimal128 -Infinity on negative overflow",
    ),
]

# Property [Overflow Recovery]: if intermediate values overflow but the final
# sum fits the original type, the result is returned in the original type.
# Double and Decimal128 overflow does not recover once infinity is reached.
SUM_OVERFLOW_RECOVERY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "recovery_int32_positive",
        docs=[{"v": INT32_MAX}, {"v": 1000}, {"v": -1000}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MAX, "type": "int"},
        msg="$sum should recover int32 when intermediate overflows but final fits int32",
    ),
    AccumulatorTestCase(
        "recovery_int32_negative",
        docs=[{"v": INT32_MIN}, {"v": -1000}, {"v": 1000}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MIN, "type": "int"},
        msg="$sum should recover int32 when intermediate underflows but final fits int32",
    ),
    AccumulatorTestCase(
        "recovery_int64_positive",
        docs=[{"v": INT64_MAX}, {"v": Int64(100)}, {"v": Int64(-100)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MAX, "type": "long"},
        msg="$sum should recover Int64 when intermediate overflows but final fits Int64",
    ),
    AccumulatorTestCase(
        "recovery_int64_negative",
        docs=[{"v": INT64_MIN}, {"v": Int64(-1000)}, {"v": Int64(1000)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MIN, "type": "long"},
        msg="$sum should recover Int64 when intermediate underflows but final fits Int64",
    ),
    AccumulatorTestCase(
        "recovery_double_no_recover",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MAX}, {"v": DOUBLE_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": FLOAT_INFINITY, "type": "double"},
        msg="$sum should not recover double once intermediate reaches infinity",
    ),
    AccumulatorTestCase(
        "recovery_decimal128_no_recover",
        docs=[
            {"v": DECIMAL128_MAX},
            {"v": DECIMAL128_MAX},
            {"v": DECIMAL128_MIN},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INFINITY, "type": "decimal"},
        msg="$sum should not recover Decimal128 once intermediate reaches Infinity",
    ),
]

# Property [Decimal128 Presence Changes Overflow Path]: when Int64 values
# overflow and a Decimal128 value is present in the group, the result is
# Decimal128 with exact precision instead of promoting to double.
SUM_DECIMAL128_OVERFLOW_PATH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal128_path_int64_overflow_with_decimal_zero",
        docs=[{"v": INT64_MAX}, {"v": Int64(1)}, {"v": DECIMAL128_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INT64_OVERFLOW, "type": "decimal"},
        msg="$sum should produce exact Decimal128 when Int64 overflows with Decimal128(0) present",
    ),
    AccumulatorTestCase(
        "decimal128_path_decimal_first",
        docs=[{"v": DECIMAL128_ZERO}, {"v": INT64_MAX}, {"v": Int64(1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INT64_OVERFLOW, "type": "decimal"},
        msg="$sum should produce Decimal128 regardless of Decimal128 position in group",
    ),
    AccumulatorTestCase(
        "decimal128_path_double_does_not_redirect",
        docs=[{"v": INT64_MAX}, {"v": Int64(1)}, {"v": DOUBLE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DOUBLE_FROM_INT64_MAX, "type": "double"},
        msg="$sum should not redirect Int64 overflow to Decimal128 when only double is present",
    ),
    AccumulatorTestCase(
        "decimal128_path_both_double_and_decimal128",
        docs=[
            {"v": INT64_MAX},
            {"v": Int64(1)},
            {"v": DOUBLE_ZERO},
            {"v": DECIMAL128_ZERO},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INT64_OVERFLOW, "type": "decimal"},
        msg="$sum should produce Decimal128 when both double and Decimal128 present with overflow",
    ),
]

# Property [Cross-Type NaN/Infinity Interactions]: when double NaN or infinity
# is mixed with Decimal128 values, the result is promoted to Decimal128 with
# NaN or Infinity propagating in the Decimal128 domain.
SUM_CROSS_TYPE_NAN_INF_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "cross_type_double_nan_plus_decimal128",
        docs=[{"v": FLOAT_NAN}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_NAN, "type": "decimal"},
        msg="$sum should promote double NaN + Decimal128 to Decimal128 NaN",
    ),
    AccumulatorTestCase(
        "cross_type_decimal128_nan_plus_double",
        docs=[{"v": DECIMAL128_NAN}, {"v": 5.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_NAN, "type": "decimal"},
        msg="$sum should promote Decimal128 NaN + double to Decimal128 NaN",
    ),
    AccumulatorTestCase(
        "cross_type_double_inf_plus_decimal128",
        docs=[{"v": FLOAT_INFINITY}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_INFINITY, "type": "decimal"},
        msg="$sum should promote double inf + Decimal128 to Decimal128 Infinity",
    ),
    AccumulatorTestCase(
        "cross_type_double_neg_inf_plus_decimal128_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": DECIMAL128_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DECIMAL128_NAN, "type": "decimal"},
        msg="$sum should produce Decimal128 NaN for double -inf + Decimal128 Infinity",
    ),
]

# Property [Constant Type Preservation]: the result type of a numeric constant
# matches the constant's input type.
SUM_CONSTANT_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "constant_type_int32",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": 1}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 2, "type": "int"},
        msg="$sum should preserve int32 type for int32 constant",
    ),
    AccumulatorTestCase(
        "constant_type_int64",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": Int64(1)}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(2), "type": "long"},
        msg="$sum should preserve Int64 type for Int64 constant",
    ),
    AccumulatorTestCase(
        "constant_type_double",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": 2.5}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 5.0, "type": "double"},
        msg="$sum should preserve double type for double constant",
    ),
    AccumulatorTestCase(
        "constant_type_decimal128",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": Decimal128("3")}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Decimal128("6"), "type": "decimal"},
        msg="$sum should preserve Decimal128 type for Decimal128 constant",
    ),
]

# Property [Integer Boundary Values]: boundary values at the edges of int32
# and Int64 ranges stay in their original type when no overflow occurs, and
# promote to the next wider type when the sum crosses the boundary by one.
SUM_INTEGER_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boundary_int32_max_single",
        docs=[{"v": INT32_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MAX, "type": "int"},
        msg="$sum should keep int32_max as int32 when it is the only value",
    ),
    AccumulatorTestCase(
        "boundary_int32_min_single",
        docs=[{"v": INT32_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MIN, "type": "int"},
        msg="$sum should keep int32_min as int32 when it is the only value",
    ),
    AccumulatorTestCase(
        "boundary_int64_max_single",
        docs=[{"v": INT64_MAX}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MAX, "type": "long"},
        msg="$sum should keep int64_max as Int64 when it is the only value",
    ),
    AccumulatorTestCase(
        "boundary_int64_min_single",
        docs=[{"v": INT64_MIN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MIN, "type": "long"},
        msg="$sum should keep int64_min as Int64 when it is the only value",
    ),
    AccumulatorTestCase(
        "boundary_int32_max_no_overflow",
        docs=[{"v": INT32_MAX_MINUS_1}, {"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MAX, "type": "int"},
        msg="$sum should stay int32 when int32_max-1 + 1 equals int32_max",
    ),
    AccumulatorTestCase(
        "boundary_int32_max_overflow",
        docs=[{"v": INT32_MAX_MINUS_1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(INT32_OVERFLOW), "type": "long"},
        msg="$sum should promote to Int64 when int32_max-1 + 2 overflows int32",
    ),
    AccumulatorTestCase(
        "boundary_int32_min_no_overflow",
        docs=[{"v": INT32_MIN_PLUS_1}, {"v": -1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT32_MIN, "type": "int"},
        msg="$sum should stay int32 when int32_min+1 + (-1) equals int32_min",
    ),
    AccumulatorTestCase(
        "boundary_int32_min_overflow",
        docs=[{"v": INT32_MIN_PLUS_1}, {"v": -2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(INT32_UNDERFLOW), "type": "long"},
        msg="$sum should promote to Int64 when int32_min+1 + (-2) overflows int32",
    ),
    AccumulatorTestCase(
        "boundary_int64_max_no_overflow",
        docs=[{"v": INT64_MAX_MINUS_1}, {"v": Int64(1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MAX, "type": "long"},
        msg="$sum should stay Int64 when int64_max-1 + 1 equals int64_max",
    ),
    AccumulatorTestCase(
        "boundary_int64_max_overflow",
        docs=[{"v": INT64_MAX_MINUS_1}, {"v": Int64(2)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": DOUBLE_FROM_INT64_MAX, "type": "double"},
        msg="$sum should promote to double when int64_max-1 + 2 overflows Int64",
    ),
    AccumulatorTestCase(
        "boundary_int64_min_no_overflow",
        docs=[{"v": INT64_MIN_PLUS_1}, {"v": Int64(-1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": INT64_MIN, "type": "long"},
        msg="$sum should stay Int64 when int64_min+1 + (-1) equals int64_min",
    ),
    AccumulatorTestCase(
        "boundary_int64_min_overflow",
        docs=[{"v": INT64_MIN_PLUS_1}, {"v": Int64(-2)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": -DOUBLE_FROM_INT64_MAX, "type": "double"},
        msg="$sum should promote to double when int64_min+1 + (-2) overflows Int64",
    ),
]

# Property [Large Groups]: $sum correctly accumulates values across large
# groups without precision loss or type promotion.
SUM_LARGE_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "large_group_10k_int1",
        docs=[{"v": 1} for _ in range(10_000)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 10_000, "type": "int"},
        msg="$sum should produce 10000 (int32) for 10000 documents with int(1)",
    ),
]

SUM_TYPE_TESTS = (
    SUM_TYPE_PROMOTION_TESTS
    + SUM_OVERFLOW_TESTS
    + SUM_OVERFLOW_RECOVERY_TESTS
    + SUM_DECIMAL128_OVERFLOW_PATH_TESTS
    + SUM_CROSS_TYPE_NAN_INF_TESTS
    + SUM_CONSTANT_TYPE_TESTS
    + SUM_INTEGER_BOUNDARY_TESTS
    + SUM_LARGE_GROUP_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_TYPE_TESTS))
def test_accumulator_sum_return_type(collection, test_case: AccumulatorTestCase):
    """Test $sum return type and type promotion."""
    result = execute_accumulator(collection, test_case.docs, test_case.pipeline)
    assertSuccess(
        result,
        [test_case.expected],
        msg=test_case.msg,
        transform=lambda docs: [{"value": docs[0]["value"], "type": docs[0]["type"]}],
    )


# Property [Negative Zero Normalization]: $sum normalizes negative zero to
# positive zero for both double and Decimal128.
SUM_NEGATIVE_ZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "neg_zero_double_single",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "str": {"$toString": "$result"}}},
        ],
        expected="0",
        msg="$sum should normalize a single double -0.0 to +0.0",
    ),
    AccumulatorTestCase(
        "neg_zero_double_sum",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": DOUBLE_NEGATIVE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "str": {"$toString": "$result"}}},
        ],
        expected="0",
        msg="$sum should normalize -0.0 + -0.0 to +0.0",
    ),
    AccumulatorTestCase(
        "neg_zero_decimal128_single",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "str": {"$toString": "$result"}}},
        ],
        expected="0",
        msg="$sum should normalize a single Decimal128('-0') to Decimal128('0')",
    ),
    AccumulatorTestCase(
        "neg_zero_decimal128_sum",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": DECIMAL128_NEGATIVE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": "$v"}}},
            {"$project": {"_id": 0, "str": {"$toString": "$result"}}},
        ],
        expected="0",
        msg="$sum should normalize Decimal128('-0') + Decimal128('-0') to Decimal128('0')",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUM_NEGATIVE_ZERO_TESTS))
def test_accumulator_sum_negative_zero(collection, test_case: AccumulatorTestCase):
    """Test $sum negative zero normalization."""
    result = execute_accumulator(collection, test_case.docs, test_case.pipeline)
    assertSuccess(
        result,
        [{"str": test_case.expected}],
        msg=test_case.msg,
        transform=lambda docs: [{"str": docs[0]["str"]}],
    )


# Property [Syntax Validation]: "$" by itself is not a valid FieldPath and
# produces an error.
SUM_SYNTAX_VALIDATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "syntax_bare_dollar",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$"}}}],
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$sum should reject '$' as an invalid FieldPath",
    ),
]

# Property [Arity Errors]: array syntax is rejected in accumulator context,
# and multi-key expression objects produce an expression parsing error.
SUM_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": []}}}],
        error_code=ACCUMULATOR_UNARY_OPERATOR_ERROR,
        msg="$sum should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": [1]}}}],
        error_code=ACCUMULATOR_UNARY_OPERATOR_ERROR,
        msg="$sum should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": ["$v"]}}}],
        error_code=ACCUMULATOR_UNARY_OPERATOR_ERROR,
        msg="$sum should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": [1, 2, 3]}}}],
        error_code=ACCUMULATOR_UNARY_OPERATOR_ERROR,
        msg="$sum should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": {"$add": [1, 2], "$multiply": [3, 4]}}}}
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$sum should reject multi-key expression object",
    ),
]

# Property [Expression Error Propagation]: when the accumulator expression
# errors for any document in the group, the error propagates to the caller.
SUM_EXPRESSION_ERROR_PROPAGATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_error_to_int_invalid_string",
        docs=[{"v": "abc"}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$toInt": "$v"}}}}],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$sum should propagate $toInt conversion error from expression",
    ),
]

# Property [Expression Error Propagation - Divide by Zero]: $divide by zero
# errors propagate through $sum in $group and $bucket stages; $bucketAuto
# wraps this error with a different code (BAD_VALUE_ERROR).
SUM_EXPRESSION_ERROR_DIVIDE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_error_divide_by_zero",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$divide": ["$v", 0]}}}}],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$sum should propagate $divide by zero error from expression",
    ),
]

SUM_ERROR_TESTS = (
    SUM_SYNTAX_VALIDATION_TESTS
    + SUM_ARITY_ERROR_TESTS
    + SUM_EXPRESSION_ERROR_PROPAGATION_TESTS
    + SUM_EXPRESSION_ERROR_DIVIDE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_ERROR_TESTS))
def test_accumulator_sum_errors(collection, test_case):
    """Test $sum error cases."""
    result = execute_accumulator(collection, test_case.docs, test_case.pipeline)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
