"""Tests for $sum accumulator in $group context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
    assertSuccess,
)
from documentdb_tests.framework.error_codes import (
    ACCUMULATOR_UNARY_OPERATOR_ERROR,
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
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


@dataclass(frozen=True)
class SumAccumulatorTest(BaseTestCase):
    """Test case for $sum accumulator."""

    docs: list[dict] | None = None
    expression: Any = None


# Property [Null and Missing Behavior]: null and missing values are ignored
# by $sum, producing 0 (int32) when no numeric values remain.
SUM_NULL_MISSING_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "null_all",
        docs=[{"v": None}, {"v": None}],
        expression="$v",
        expected=0,
        msg="$sum should return 0 when all values are null",
    ),
    SumAccumulatorTest(
        "null_all_missing",
        docs=[{"x": 1}, {"x": 2}],
        expression="$v",
        expected=0,
        msg="$sum should return 0 when all documents have missing field",
    ),
    SumAccumulatorTest(
        "null_mixed_null_and_missing",
        docs=[{"v": None}, {"x": 1}],
        expression="$v",
        expected=0,
        msg="$sum should return 0 when group has only null and missing values",
    ),
    SumAccumulatorTest(
        "null_with_numerics",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        expression="$v",
        expected=8,
        msg="$sum should ignore null and sum only numeric values",
    ),
    SumAccumulatorTest(
        "null_missing_with_numerics",
        docs=[{"x": 1}, {"v": 7}, {"v": 2}],
        expression="$v",
        expected=9,
        msg="$sum should ignore missing fields and sum only numeric values",
    ),
    SumAccumulatorTest(
        "null_mixed_null_missing_with_numerics",
        docs=[{"v": None}, {"x": 1}, {"v": 10}],
        expression="$v",
        expected=10,
        msg="$sum should ignore both null and missing, summing only numerics",
    ),
    SumAccumulatorTest(
        "null_constant_null",
        docs=[{"x": 1}, {"x": 2}],
        expression=None,
        expected=0,
        msg="$sum should return 0 for a constant null expression",
    ),
    SumAccumulatorTest(
        "null_literal_null",
        docs=[{"x": 1}, {"x": 2}],
        expression={"$literal": None},
        expected=0,
        msg="$sum should return 0 when expression evaluates to null",
    ),
    SumAccumulatorTest(
        "null_remove_only",
        docs=[{"v": 5}],
        expression={"$cond": [False, 1, "$$REMOVE"]},
        expected=0,
        msg="$sum should treat $$REMOVE as missing and return 0",
    ),
]

# Property [Non-Numeric Types Ignored]: all non-numeric BSON types are
# silently ignored, contributing nothing to the result. Returns 0 (int32)
# when no numeric values remain.
SUM_NON_NUMERIC_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "non_numeric_string",
        docs=[{"v": "hello"}, {"v": 10}],
        expression="$v",
        expected=10,
        msg="$sum should ignore string values and sum only numerics",
    ),
    SumAccumulatorTest(
        "non_numeric_boolean_true",
        docs=[{"v": True}, {"v": 7}],
        expression="$v",
        expected=7,
        msg="$sum should ignore boolean true without coercing to 1",
    ),
    SumAccumulatorTest(
        "non_numeric_boolean_false",
        docs=[{"v": False}, {"v": 3}],
        expression="$v",
        expected=3,
        msg="$sum should ignore boolean false without coercing to 0",
    ),
    SumAccumulatorTest(
        "non_numeric_object",
        docs=[{"v": {"a": 1}}, {"v": 6}],
        expression="$v",
        expected=6,
        msg="$sum should ignore embedded document values",
    ),
    SumAccumulatorTest(
        "non_numeric_empty_object",
        docs=[{"v": {}}, {"v": 4}],
        expression="$v",
        expected=4,
        msg="$sum should ignore empty document values",
    ),
    SumAccumulatorTest(
        "non_numeric_objectid",
        docs=[{"v": ObjectId()}, {"v": 8}],
        expression="$v",
        expected=8,
        msg="$sum should ignore ObjectId values",
    ),
    SumAccumulatorTest(
        "non_numeric_datetime",
        docs=[
            {"v": datetime(2023, 1, 1, tzinfo=timezone.utc)},
            {"v": 2},
        ],
        expression="$v",
        expected=2,
        msg="$sum should ignore datetime values",
    ),
    SumAccumulatorTest(
        "non_numeric_timestamp",
        docs=[{"v": Timestamp(1, 1)}, {"v": 9}],
        expression="$v",
        expected=9,
        msg="$sum should ignore Timestamp values",
    ),
    SumAccumulatorTest(
        "non_numeric_binary",
        docs=[{"v": Binary(b"\x01\x02")}, {"v": 5}],
        expression="$v",
        expected=5,
        msg="$sum should ignore Binary values",
    ),
    SumAccumulatorTest(
        "non_numeric_regex",
        docs=[{"v": Regex("abc", "i")}, {"v": 11}],
        expression="$v",
        expected=11,
        msg="$sum should ignore Regex values",
    ),
    SumAccumulatorTest(
        "non_numeric_code",
        docs=[{"v": Code("function(){}")}, {"v": 12}],
        expression="$v",
        expected=12,
        msg="$sum should ignore Code values",
    ),
    SumAccumulatorTest(
        "non_numeric_minkey",
        docs=[{"v": MinKey()}, {"v": 14}],
        expression="$v",
        expected=14,
        msg="$sum should ignore MinKey values",
    ),
    SumAccumulatorTest(
        "non_numeric_maxkey",
        docs=[{"v": MaxKey()}, {"v": 15}],
        expression="$v",
        expected=15,
        msg="$sum should ignore MaxKey values",
    ),
    SumAccumulatorTest(
        "non_numeric_array",
        docs=[{"v": [1, 2, 3]}, {"v": 20}],
        expression="$v",
        expected=20,
        msg="$sum should treat arrays as non-numeric in $group context",
    ),
    SumAccumulatorTest(
        "non_numeric_single_element_array",
        docs=[{"v": [5]}, {"v": 10}],
        expression="$v",
        expected=10,
        msg="$sum should not unwrap single-element numeric arrays",
    ),
    SumAccumulatorTest(
        "non_numeric_empty_array",
        docs=[{"v": []}, {"v": 7}],
        expression="$v",
        expected=7,
        msg="$sum should treat empty arrays as non-numeric",
    ),
    SumAccumulatorTest(
        "non_numeric_nested_array",
        docs=[{"v": [[1, 2]]}, {"v": 3}],
        expression="$v",
        expected=3,
        msg="$sum should treat nested arrays as non-numeric",
    ),
    SumAccumulatorTest(
        "non_numeric_array_from_expression",
        docs=[{"v": 1}],
        expression={"$literal": [1, 2, 3]},
        expected=0,
        msg="$sum should treat array expressions as non-numeric",
    ),
    SumAccumulatorTest(
        "non_numeric_all_non_numeric",
        docs=[{"v": "abc"}, {"v": True}, {"v": [1]}, {"v": {"a": 1}}],
        expression="$v",
        expected=0,
        msg="$sum should return 0 when all values are non-numeric",
    ),
    SumAccumulatorTest(
        "non_numeric_numeric_string",
        docs=[{"v": "123"}, {"v": 5}],
        expression="$v",
        expected=5,
        msg="$sum should not coerce numeric strings to numbers",
    ),
]

# Property [Special Float Values]: NaN propagates through summation and
# dominates all other values; Infinity arithmetic follows IEEE 754 rules.
SUM_SPECIAL_FLOAT_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "special_inf_plus_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_INFINITY}],
        expression="$v",
        expected=FLOAT_INFINITY,
        msg="$sum should produce Infinity when summing Infinity + Infinity",
    ),
    SumAccumulatorTest(
        "special_neg_inf_plus_neg_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        expression="$v",
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should produce -Infinity when summing -Infinity + -Infinity",
    ),
    SumAccumulatorTest(
        "special_inf_plus_finite",
        docs=[{"v": FLOAT_INFINITY}, {"v": 42.0}],
        expression="$v",
        expected=FLOAT_INFINITY,
        msg="$sum should produce Infinity when summing Infinity + finite",
    ),
    SumAccumulatorTest(
        "special_neg_inf_plus_finite",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": 42.0}],
        expression="$v",
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should produce -Infinity when summing -Infinity + finite",
    ),
    SumAccumulatorTest(
        "special_nan_propagates",
        docs=[{"v": FLOAT_NAN}, {"v": 5.0}],
        expression="$v",
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should propagate NaN through summation",
    ),
    SumAccumulatorTest(
        "special_nan_dominates_inf",
        docs=[{"v": FLOAT_NAN}, {"v": FLOAT_INFINITY}],
        expression="$v",
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should produce NaN when NaN is summed with Infinity",
    ),
    SumAccumulatorTest(
        "special_inf_plus_neg_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        expression="$v",
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should produce NaN for Infinity + (-Infinity)",
    ),
    SumAccumulatorTest(
        "special_non_numeric_with_nan",
        docs=[{"v": "hello"}, {"v": FLOAT_NAN}],
        expression="$v",
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should ignore non-numeric values and preserve NaN",
    ),
]

# Property [Decimal128 Special Values]: Decimal128 NaN and Infinity follow
# the same propagation rules in the Decimal128 domain.
SUM_DECIMAL128_SPECIAL_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "special_decimal_nan_propagates",
        docs=[{"v": DECIMAL128_NAN}, {"v": Decimal128("5")}],
        expression="$v",
        expected=DECIMAL128_NAN,
        msg="$sum should propagate Decimal128 NaN through summation",
    ),
    SumAccumulatorTest(
        "special_decimal_inf_plus_neg_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_NEGATIVE_INFINITY}],
        expression="$v",
        expected=DECIMAL128_NAN,
        msg="$sum should produce Decimal128 NaN for Decimal128 Infinity + -Infinity",
    ),
    SumAccumulatorTest(
        "special_decimal_inf_plus_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_INFINITY}],
        expression="$v",
        expected=DECIMAL128_INFINITY,
        msg="$sum should produce Decimal128 Infinity for Decimal128 Infinity + Infinity",
    ),
]

# Property [Precision]: Decimal128 provides exact arithmetic and preserves
# trailing zeros; double follows IEEE 754 with precision loss for large
# values; subnormal values are handled correctly.
SUM_PRECISION_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "precision_decimal128_exact",
        docs=[{"v": Decimal128("0.1")} for _ in range(100)],
        expression="$v",
        expected=Decimal128("10.0"),
        msg="$sum should produce exact Decimal128 result for 100 x 0.1",
    ),
    SumAccumulatorTest(
        "precision_decimal128_trailing_zeros",
        docs=[{"v": Decimal128("1.100")}, {"v": Decimal128("2.20")}],
        expression="$v",
        expected=Decimal128("3.300"),
        msg="$sum should preserve trailing zeros based on highest-precision operand",
    ),
    SumAccumulatorTest(
        "precision_double_accumulation",
        docs=[{"v": 0.1} for _ in range(100)],
        expression="$v",
        expected=10.0,
        msg="$sum should produce 10.0 for 100 x double 0.1 due to accumulation",
    ),
    SumAccumulatorTest(
        "precision_double_loss_large_value",
        docs=[{"v": 1e16}, {"v": 1.0}],
        expression="$v",
        expected=1e16,
        msg="$sum should lose precision for double when adding 1.0 to 1e16",
    ),
    SumAccumulatorTest(
        "precision_int64_max_plus_decimal128_exact",
        docs=[{"v": INT64_MAX}, {"v": Decimal128("1")}],
        expression="$v",
        expected=DECIMAL128_INT64_OVERFLOW,
        msg="$sum should preserve exact value for Int64_max + Decimal128(1)",
    ),
    SumAccumulatorTest(
        "precision_int64_max_plus_double_loses",
        docs=[{"v": INT64_MAX}, {"v": 1.0}],
        expression="$v",
        expected=DOUBLE_FROM_INT64_MAX,
        msg="$sum should lose precision for Int64_max + double(1.0)",
    ),
    SumAccumulatorTest(
        "precision_subnormal_double_addition",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": DOUBLE_MIN_SUBNORMAL}],
        expression="$v",
        expected=1e-323,
        msg="$sum should correctly add subnormal double values",
    ),
    SumAccumulatorTest(
        "precision_subnormal_double_negative",
        docs=[
            {"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
            {"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        ],
        expression="$v",
        expected=-1e-323,
        msg="$sum should correctly add negative subnormal double values",
    ),
    SumAccumulatorTest(
        "precision_subnormal_double_cancellation",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        expression="$v",
        expected=DOUBLE_ZERO,
        msg="$sum should produce 0.0 when subnormal values cancel",
    ),
    SumAccumulatorTest(
        "precision_decimal128_subnormal",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": DECIMAL128_MIN_POSITIVE}],
        expression="$v",
        expected=Decimal128("2E-6176"),
        msg="$sum should correctly add Decimal128 subnormal values",
    ),
    SumAccumulatorTest(
        "precision_decimal128_large_exponent",
        docs=[{"v": DECIMAL128_LARGE_EXPONENT}, {"v": DECIMAL128_LARGE_EXPONENT}],
        expression="$v",
        expected=Decimal128("2.000000000000000000000000000000000E+6144"),
        msg="$sum should correctly add Decimal128 large exponent values",
    ),
    SumAccumulatorTest(
        "precision_decimal128_34_digit_overflow",
        docs=[{"v": DECIMAL128_MAX_COEFFICIENT}, {"v": Decimal128("1")}],
        expression="$v",
        expected=Decimal128("1.000000000000000000000000000000000E+34"),
        msg="$sum should round correctly when Decimal128 34-digit precision overflows",
    ),
]

# Property [Constant Expression Behavior]: a numeric constant counts documents
# by multiplying the constant by the group size; a non-numeric constant
# produces 0 (int32); NaN and Infinity constants propagate.
SUM_CONSTANT_EXPRESSION_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "constant_int32",
        docs=[{"x": 1}, {"x": 2}, {"x": 3}],
        expression=1,
        expected=3,
        msg="$sum should count documents when given an int32 constant of 1",
    ),
    SumAccumulatorTest(
        "constant_int32_larger",
        docs=[{"x": 1}, {"x": 2}],
        expression=5,
        expected=10,
        msg="$sum should multiply int32 constant by group size",
    ),
    SumAccumulatorTest(
        "constant_non_numeric_true",
        docs=[{"x": 1}, {"x": 2}],
        expression=True,
        expected=0,
        msg="$sum should return 0 for non-numeric constant True",
    ),
    SumAccumulatorTest(
        "constant_non_numeric_false",
        docs=[{"x": 1}, {"x": 2}],
        expression=False,
        expected=0,
        msg="$sum should return 0 for non-numeric constant False",
    ),
    SumAccumulatorTest(
        "constant_non_numeric_string",
        docs=[{"x": 1}, {"x": 2}],
        expression="hello",
        expected=0,
        msg="$sum should return 0 for non-numeric string constant without $",
    ),
    SumAccumulatorTest(
        "constant_non_numeric_empty_object",
        docs=[{"x": 1}, {"x": 2}],
        expression={},
        expected=0,
        msg="$sum should return 0 for empty object constant",
    ),
    SumAccumulatorTest(
        "constant_non_numeric_non_operator_object",
        docs=[{"x": 1}, {"x": 2}],
        expression={"a": 1},
        expected=0,
        msg="$sum should return 0 for non-operator object constant",
    ),
    SumAccumulatorTest(
        "constant_nan_propagates",
        docs=[{"x": 1}, {"x": 2}],
        expression=FLOAT_NAN,
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should propagate NaN constant",
    ),
    SumAccumulatorTest(
        "constant_inf_propagates",
        docs=[{"x": 1}, {"x": 2}],
        expression=FLOAT_INFINITY,
        expected=FLOAT_INFINITY,
        msg="$sum should propagate Infinity constant",
    ),
    SumAccumulatorTest(
        "constant_neg_inf_propagates",
        docs=[{"x": 1}, {"x": 2}],
        expression=FLOAT_NEGATIVE_INFINITY,
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should propagate negative Infinity constant",
    ),
]

# Property [Expression Arguments]: $sum accepts any expression that resolves
# to a value; numeric results are summed, non-numeric results are ignored,
# and nested $sum (array summation) is supported.
SUM_EXPRESSION_ARGS_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "expr_args_arithmetic",
        docs=[{"a": 3, "b": 2}, {"a": 5, "b": 1}],
        expression={"$add": ["$a", "$b"]},
        expected=11,
        msg="$sum should accept an arithmetic expression and sum its numeric results",
    ),
    SumAccumulatorTest(
        "expr_args_non_numeric_ignored",
        docs=[{"a": "hello", "b": " world"}, {"a": "foo", "b": "bar"}],
        expression={"$concat": ["$a", "$b"]},
        expected=0,
        msg="$sum should ignore non-numeric expression results and return 0",
    ),
    SumAccumulatorTest(
        "expr_args_nested_sum_array",
        docs=[{"v": [1, 2, 3]}, {"v": [4, 5]}],
        expression={"$sum": "$v"},
        expected=15,
        msg="$sum should accept nested $sum (array summation) as its expression",
    ),
]

SUM_SUCCESS_TESTS = (
    SUM_NULL_MISSING_TESTS
    + SUM_NON_NUMERIC_TESTS
    + SUM_SPECIAL_FLOAT_TESTS
    + SUM_DECIMAL128_SPECIAL_TESTS
    + SUM_PRECISION_TESTS
    + SUM_CONSTANT_EXPRESSION_TESTS
    + SUM_EXPRESSION_ARGS_TESTS
)

# Property [Expression Error Propagation]: errors from sub-expressions
# propagate through $sum without being caught or suppressed.
SUM_EXPRESSION_ERROR_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "error_prop_toint_non_convertible",
        docs=[{"v": "abc"}],
        expression={"$toInt": "$v"},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$sum should propagate $toInt conversion error for non-convertible value",
    ),
    SumAccumulatorTest(
        "error_prop_divide_by_zero",
        docs=[{"v": 10}],
        expression={"$divide": ["$v", 0]},
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$sum should propagate $divide by zero error",
    ),
]

# Property [Syntax Validation]: invalid FieldPath syntax is rejected.
SUM_SYNTAX_ERROR_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "syntax_bare_dollar",
        docs=[{"v": 1}],
        expression="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$sum should reject '$' as an invalid FieldPath",
    ),
]

SUM_TESTS = SUM_SUCCESS_TESTS + SUM_EXPRESSION_ERROR_TESTS + SUM_SYNTAX_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUM_TESTS))
def test_accumulator_sum(collection, test_case: SumAccumulatorTest):
    """Test $sum accumulator behavior."""
    collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "result": {"$sum": test_case.expression}}},
                {"$project": {"_id": 0, "result": 1}},
            ],
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=[{"result": test_case.expected}] if test_case.error_code is None else None,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


def test_accumulator_sum_empty_collection(collection):
    """Test $sum returns no documents for an empty collection."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "result": {"$sum": "$v"}}},
                {"$project": {"_id": 0, "result": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [],
        msg="$sum should produce no group output for an empty collection",
    )


# Property [Return Type and Type Promotion]: the result type is the widest
# numeric type present in the group following int32 < Int64 < double <
# Decimal128, with no demotion. When all values are non-numeric, the result
# is int32 zero.
SUM_RETURN_TYPE_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "type_single_int32",
        docs=[{"v": 5}],
        expression="$v",
        expected={"value": 5, "type": "int"},
        msg="$sum should preserve int32 type for a single int32 value",
    ),
    SumAccumulatorTest(
        "type_single_int64",
        docs=[{"v": Int64(5)}],
        expression="$v",
        expected={"value": Int64(5), "type": "long"},
        msg="$sum should preserve Int64 type for a single Int64 value",
    ),
    SumAccumulatorTest(
        "type_single_double",
        docs=[{"v": 5.5}],
        expression="$v",
        expected={"value": 5.5, "type": "double"},
        msg="$sum should preserve double type for a single double value",
    ),
    SumAccumulatorTest(
        "type_single_decimal128",
        docs=[{"v": Decimal128("5.5")}],
        expression="$v",
        expected={"value": Decimal128("5.5"), "type": "decimal"},
        msg="$sum should preserve Decimal128 type for a single Decimal128 value",
    ),
    SumAccumulatorTest(
        "type_int32_int64_promotes",
        docs=[{"v": 5}, {"v": Int64(10)}],
        expression="$v",
        expected={"value": Int64(15), "type": "long"},
        msg="$sum should promote int32 + Int64 to Int64",
    ),
    SumAccumulatorTest(
        "type_int32_double_promotes",
        docs=[{"v": 5}, {"v": 2.5}],
        expression="$v",
        expected={"value": 7.5, "type": "double"},
        msg="$sum should promote int32 + double to double",
    ),
    SumAccumulatorTest(
        "type_int64_double_promotes",
        docs=[{"v": Int64(5)}, {"v": 2.5}],
        expression="$v",
        expected={"value": 7.5, "type": "double"},
        msg="$sum should promote Int64 + double to double",
    ),
    SumAccumulatorTest(
        "type_int32_decimal128_promotes",
        docs=[{"v": 5}, {"v": DECIMAL128_TWO_AND_HALF}],
        expression="$v",
        expected={"value": Decimal128("7.5"), "type": "decimal"},
        msg="$sum should promote int32 + Decimal128 to Decimal128",
    ),
    SumAccumulatorTest(
        "type_int64_decimal128_promotes",
        docs=[{"v": Int64(5)}, {"v": Decimal128("3")}],
        expression="$v",
        expected={"value": Decimal128("8"), "type": "decimal"},
        msg="$sum should promote Int64 + Decimal128 to Decimal128",
    ),
    SumAccumulatorTest(
        "type_double_decimal128_promotes",
        docs=[{"v": 2.5}, {"v": Decimal128("3.5")}],
        expression="$v",
        expected={"value": Decimal128("6.0"), "type": "decimal"},
        msg="$sum should promote double + Decimal128 to Decimal128",
    ),
    SumAccumulatorTest(
        "type_no_demotion_int64_fits_int32",
        docs=[{"v": Int64(1)}, {"v": Int64(2)}],
        expression="$v",
        expected={"value": Int64(3), "type": "long"},
        msg="$sum should not demote Int64 to int32 even when result fits int32",
    ),
    SumAccumulatorTest(
        "type_all_non_numeric_is_int32",
        docs=[{"v": "abc"}, {"v": True}],
        expression="$v",
        expected={"value": 0, "type": "int"},
        msg="$sum should return int32 zero when all values are non-numeric",
    ),
]

# Property [Overflow Behavior]: double and Decimal128 overflow produces
# infinity without type promotion.
SUM_OVERFLOW_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "overflow_double_positive",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MAX}],
        expression="$v",
        expected={"value": FLOAT_INFINITY, "type": "double"},
        msg="$sum should produce positive Infinity on double overflow",
    ),
    SumAccumulatorTest(
        "overflow_double_negative",
        docs=[{"v": DOUBLE_MIN}, {"v": DOUBLE_MIN}],
        expression="$v",
        expected={"value": FLOAT_NEGATIVE_INFINITY, "type": "double"},
        msg="$sum should produce negative Infinity on double overflow",
    ),
    SumAccumulatorTest(
        "overflow_decimal128_positive",
        docs=[{"v": DECIMAL128_MAX}, {"v": DECIMAL128_MAX}],
        expression="$v",
        expected={"value": DECIMAL128_INFINITY, "type": "decimal"},
        msg="$sum should produce Decimal128 Infinity on positive overflow",
    ),
    SumAccumulatorTest(
        "overflow_decimal128_negative",
        docs=[{"v": DECIMAL128_MIN}, {"v": DECIMAL128_MIN}],
        expression="$v",
        expected={"value": DECIMAL128_NEGATIVE_INFINITY, "type": "decimal"},
        msg="$sum should produce Decimal128 -Infinity on negative overflow",
    ),
]

# Property [Overflow Recovery]: if intermediate values overflow but the final
# sum fits the original type, the result is returned in the original type.
# Double and Decimal128 overflow does not recover once infinity is reached.
SUM_OVERFLOW_RECOVERY_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "recovery_int32_positive",
        docs=[{"v": INT32_MAX}, {"v": 1000}, {"v": -1000}],
        expression="$v",
        expected={"value": INT32_MAX, "type": "int"},
        msg="$sum should recover int32 when intermediate overflows but final fits int32",
    ),
    SumAccumulatorTest(
        "recovery_int32_negative",
        docs=[{"v": INT32_MIN}, {"v": -1000}, {"v": 1000}],
        expression="$v",
        expected={"value": INT32_MIN, "type": "int"},
        msg="$sum should recover int32 when intermediate underflows but final fits int32",
    ),
    SumAccumulatorTest(
        "recovery_int64_positive",
        docs=[{"v": INT64_MAX}, {"v": Int64(100)}, {"v": Int64(-100)}],
        expression="$v",
        expected={"value": INT64_MAX, "type": "long"},
        msg="$sum should recover Int64 when intermediate overflows but final fits Int64",
    ),
    SumAccumulatorTest(
        "recovery_int64_negative",
        docs=[{"v": INT64_MIN}, {"v": Int64(-1000)}, {"v": Int64(1000)}],
        expression="$v",
        expected={"value": INT64_MIN, "type": "long"},
        msg="$sum should recover Int64 when intermediate underflows but final fits Int64",
    ),
    SumAccumulatorTest(
        "recovery_double_no_recover",
        docs=[{"v": DOUBLE_MAX}, {"v": DOUBLE_MAX}, {"v": DOUBLE_MIN}],
        expression="$v",
        expected={"value": FLOAT_INFINITY, "type": "double"},
        msg="$sum should not recover double once intermediate reaches Infinity",
    ),
    SumAccumulatorTest(
        "recovery_decimal128_no_recover",
        docs=[
            {"v": DECIMAL128_MAX},
            {"v": DECIMAL128_MAX},
            {"v": DECIMAL128_MIN},
        ],
        expression="$v",
        expected={"value": DECIMAL128_INFINITY, "type": "decimal"},
        msg="$sum should not recover Decimal128 once intermediate reaches Infinity",
    ),
]

# Property [Decimal128 Presence Changes Overflow Path]: when Int64 values
# overflow and a Decimal128 value is present in the group, the result is
# Decimal128 with exact precision instead of promoting to double.
SUM_DECIMAL128_OVERFLOW_PATH_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "decimal128_path_int64_overflow_with_decimal_zero",
        docs=[{"v": INT64_MAX}, {"v": Int64(1)}, {"v": DECIMAL128_ZERO}],
        expression="$v",
        expected={"value": DECIMAL128_INT64_OVERFLOW, "type": "decimal"},
        msg="$sum should produce exact Decimal128 when Int64 overflows with Decimal128(0) present",
    ),
    SumAccumulatorTest(
        "decimal128_path_decimal_first",
        docs=[{"v": DECIMAL128_ZERO}, {"v": INT64_MAX}, {"v": Int64(1)}],
        expression="$v",
        expected={"value": DECIMAL128_INT64_OVERFLOW, "type": "decimal"},
        msg="$sum should produce Decimal128 regardless of Decimal128 position in group",
    ),
    SumAccumulatorTest(
        "decimal128_path_double_does_not_redirect",
        docs=[{"v": INT64_MAX}, {"v": Int64(1)}, {"v": DOUBLE_ZERO}],
        expression="$v",
        expected={"value": DOUBLE_FROM_INT64_MAX, "type": "double"},
        msg="$sum should not redirect Int64 overflow to Decimal128 when only double is present",
    ),
    SumAccumulatorTest(
        "decimal128_path_both_double_and_decimal128",
        docs=[
            {"v": INT64_MAX},
            {"v": Int64(1)},
            {"v": DOUBLE_ZERO},
            {"v": DECIMAL128_ZERO},
        ],
        expression="$v",
        expected={"value": DECIMAL128_INT64_OVERFLOW, "type": "decimal"},
        msg="$sum should produce Decimal128 when both double and Decimal128 present with overflow",
    ),
]

# Property [Cross-Type NaN/Infinity Interactions]: when double NaN or
# infinity is mixed with Decimal128 values, the result is promoted to
# Decimal128 with NaN or Infinity propagating in the Decimal128 domain.
SUM_CROSS_TYPE_NAN_INF_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "cross_type_double_nan_plus_decimal128",
        docs=[{"v": FLOAT_NAN}, {"v": Decimal128("5")}],
        expression="$v",
        expected={"value": DECIMAL128_NAN, "type": "decimal"},
        msg="$sum should promote double NaN + Decimal128 to Decimal128 NaN",
    ),
    SumAccumulatorTest(
        "cross_type_decimal128_nan_plus_double",
        docs=[{"v": DECIMAL128_NAN}, {"v": 5.0}],
        expression="$v",
        expected={"value": DECIMAL128_NAN, "type": "decimal"},
        msg="$sum should promote Decimal128 NaN + double to Decimal128 NaN",
    ),
    SumAccumulatorTest(
        "cross_type_double_inf_plus_decimal128",
        docs=[{"v": FLOAT_INFINITY}, {"v": Decimal128("5")}],
        expression="$v",
        expected={"value": DECIMAL128_INFINITY, "type": "decimal"},
        msg="$sum should promote double Infinity + Decimal128 to Decimal128 Infinity",
    ),
    SumAccumulatorTest(
        "cross_type_double_neg_inf_plus_decimal128_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": DECIMAL128_INFINITY}],
        expression="$v",
        expected={"value": DECIMAL128_NAN, "type": "decimal"},
        msg="$sum should produce Decimal128 NaN for double -Infinity + Decimal128 Infinity",
    ),
]

# Property [Constant Type Preservation]: the result type of a numeric
# constant matches the constant's input type.
SUM_CONSTANT_TYPE_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "constant_type_int32",
        docs=[{"x": 1}, {"x": 2}],
        expression=1,
        expected={"value": 2, "type": "int"},
        msg="$sum should preserve int32 type for int32 constant",
    ),
    SumAccumulatorTest(
        "constant_type_int64",
        docs=[{"x": 1}, {"x": 2}],
        expression=Int64(1),
        expected={"value": Int64(2), "type": "long"},
        msg="$sum should preserve Int64 type for Int64 constant",
    ),
    SumAccumulatorTest(
        "constant_type_double",
        docs=[{"x": 1}, {"x": 2}],
        expression=2.5,
        expected={"value": 5.0, "type": "double"},
        msg="$sum should preserve double type for double constant",
    ),
    SumAccumulatorTest(
        "constant_type_decimal128",
        docs=[{"x": 1}, {"x": 2}],
        expression=Decimal128("3"),
        expected={"value": Decimal128("6"), "type": "decimal"},
        msg="$sum should preserve Decimal128 type for Decimal128 constant",
    ),
]

# Property [Integer Boundary Values]: boundary values at the edges of int32
# and Int64 ranges stay in their original type when no overflow occurs, and
# promote to the next wider type when the sum crosses the boundary by one.
SUM_INTEGER_BOUNDARY_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "boundary_int32_max_single",
        docs=[{"v": INT32_MAX}],
        expression="$v",
        expected={"value": INT32_MAX, "type": "int"},
        msg="$sum should keep INT32_MAX as int32 when it is the only value",
    ),
    SumAccumulatorTest(
        "boundary_int32_min_single",
        docs=[{"v": INT32_MIN}],
        expression="$v",
        expected={"value": INT32_MIN, "type": "int"},
        msg="$sum should keep INT32_MIN as int32 when it is the only value",
    ),
    SumAccumulatorTest(
        "boundary_int64_max_single",
        docs=[{"v": INT64_MAX}],
        expression="$v",
        expected={"value": INT64_MAX, "type": "long"},
        msg="$sum should keep INT64_MAX as Int64 when it is the only value",
    ),
    SumAccumulatorTest(
        "boundary_int64_min_single",
        docs=[{"v": INT64_MIN}],
        expression="$v",
        expected={"value": INT64_MIN, "type": "long"},
        msg="$sum should keep INT64_MIN as Int64 when it is the only value",
    ),
    SumAccumulatorTest(
        "boundary_int32_max_no_overflow",
        docs=[{"v": INT32_MAX_MINUS_1}, {"v": 1}],
        expression="$v",
        expected={"value": INT32_MAX, "type": "int"},
        msg="$sum should stay int32 when INT32_MAX-1 + 1 equals INT32_MAX",
    ),
    SumAccumulatorTest(
        "boundary_int32_max_overflow",
        docs=[{"v": INT32_MAX_MINUS_1}, {"v": 2}],
        expression="$v",
        expected={"value": Int64(INT32_OVERFLOW), "type": "long"},
        msg="$sum should promote to Int64 when INT32_MAX-1 + 2 overflows int32",
    ),
    SumAccumulatorTest(
        "boundary_int32_min_no_overflow",
        docs=[{"v": INT32_MIN_PLUS_1}, {"v": -1}],
        expression="$v",
        expected={"value": INT32_MIN, "type": "int"},
        msg="$sum should stay int32 when INT32_MIN+1 + (-1) equals INT32_MIN",
    ),
    SumAccumulatorTest(
        "boundary_int32_min_overflow",
        docs=[{"v": INT32_MIN_PLUS_1}, {"v": -2}],
        expression="$v",
        expected={"value": Int64(INT32_UNDERFLOW), "type": "long"},
        msg="$sum should promote to Int64 when INT32_MIN+1 + (-2) overflows int32",
    ),
    SumAccumulatorTest(
        "boundary_int64_max_no_overflow",
        docs=[{"v": INT64_MAX_MINUS_1}, {"v": Int64(1)}],
        expression="$v",
        expected={"value": INT64_MAX, "type": "long"},
        msg="$sum should stay Int64 when INT64_MAX-1 + 1 equals INT64_MAX",
    ),
    SumAccumulatorTest(
        "boundary_int64_max_overflow",
        docs=[{"v": INT64_MAX_MINUS_1}, {"v": Int64(2)}],
        expression="$v",
        expected={"value": DOUBLE_FROM_INT64_MAX, "type": "double"},
        msg="$sum should promote to double when INT64_MAX-1 + 2 overflows Int64",
    ),
    SumAccumulatorTest(
        "boundary_int64_min_no_overflow",
        docs=[{"v": INT64_MIN_PLUS_1}, {"v": Int64(-1)}],
        expression="$v",
        expected={"value": INT64_MIN, "type": "long"},
        msg="$sum should stay Int64 when INT64_MIN+1 + (-1) equals INT64_MIN",
    ),
    SumAccumulatorTest(
        "boundary_int64_min_overflow",
        docs=[{"v": INT64_MIN_PLUS_1}, {"v": Int64(-2)}],
        expression="$v",
        expected={"value": -DOUBLE_FROM_INT64_MAX, "type": "double"},
        msg="$sum should promote to double when INT64_MIN+1 + (-2) overflows Int64",
    ),
]

# Property [Large Groups]: $sum correctly accumulates values across large
# groups without precision loss or type promotion.
SUM_LARGE_GROUP_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "large_group_10k_int1",
        docs=[{"v": 1} for _ in range(10_000)],
        expression="$v",
        expected={"value": 10_000, "type": "int"},
        msg="$sum should produce 10000 (int32) for 10000 documents with int(1)",
    ),
]

SUM_TYPE_TESTS = (
    SUM_RETURN_TYPE_TESTS
    + SUM_OVERFLOW_TESTS
    + SUM_OVERFLOW_RECOVERY_TESTS
    + SUM_DECIMAL128_OVERFLOW_PATH_TESTS
    + SUM_CROSS_TYPE_NAN_INF_TESTS
    + SUM_CONSTANT_TYPE_TESTS
    + SUM_INTEGER_BOUNDARY_TESTS
    + SUM_LARGE_GROUP_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_TYPE_TESTS))
def test_accumulator_sum_return_type(collection, test_case: SumAccumulatorTest):
    """Test $sum return type and type promotion."""
    collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "result": {"$sum": test_case.expression}}},
                {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [test_case.expected],
        msg=test_case.msg,
        transform=lambda docs: [{"value": docs[0]["value"], "type": docs[0]["type"]}],
    )


# Property [Negative Zero Normalization]: $sum normalizes negative zero to
# positive zero for both double and Decimal128.
SUM_NEGATIVE_ZERO_TESTS: list[SumAccumulatorTest] = [
    SumAccumulatorTest(
        "neg_zero_double_single",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}],
        expression="$v",
        expected="0",
        msg="$sum should normalize a single double -0.0 to +0.0",
    ),
    SumAccumulatorTest(
        "neg_zero_double_sum",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": DOUBLE_NEGATIVE_ZERO}],
        expression="$v",
        expected="0",
        msg="$sum should normalize -0.0 + -0.0 to +0.0",
    ),
    SumAccumulatorTest(
        "neg_zero_decimal128_single",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}],
        expression="$v",
        expected="0",
        msg="$sum should normalize a single Decimal128('-0') to Decimal128('0')",
    ),
    SumAccumulatorTest(
        "neg_zero_decimal128_sum",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": DECIMAL128_NEGATIVE_ZERO}],
        expression="$v",
        expected="0",
        msg="$sum should normalize Decimal128('-0') + Decimal128('-0') to Decimal128('0')",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUM_NEGATIVE_ZERO_TESTS))
def test_accumulator_sum_negative_zero(collection, test_case: SumAccumulatorTest):
    """Test $sum negative zero normalization."""
    collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "result": {"$sum": test_case.expression}}},
                {"$project": {"_id": 0, "str": {"$toString": "$result"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"str": test_case.expected}],
        msg=test_case.msg,
        transform=lambda docs: [{"str": docs[0]["str"]}],
    )


@dataclass(frozen=True)
class SumArityTest(BaseTestCase):
    """Test case for $sum arity rejection."""

    pipeline: list[dict] = None  # type: ignore[assignment]


# Property [Arity]: $sum in accumulator context is a unary operator and
# rejects array syntax in $group, $bucket, and $bucketAuto.
SUM_ARITY_TESTS: list[SumArityTest] = [
    SumArityTest(
        "arity_multi_element_group",
        pipeline=[{"$group": {"_id": None, "result": {"$sum": ["$v", "$v"]}}}],
        msg="$sum should reject multi-element array syntax in $group",
    ),
    SumArityTest(
        "arity_empty_array_group",
        pipeline=[{"$group": {"_id": None, "result": {"$sum": []}}}],
        msg="$sum should reject empty array syntax in $group",
    ),
    SumArityTest(
        "arity_single_element_group",
        pipeline=[{"$group": {"_id": None, "result": {"$sum": ["$v"]}}}],
        msg="$sum should reject single-element array syntax in $group",
    ),
    SumArityTest(
        "arity_multi_element_bucket",
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$sum": ["$v", "$v"]}},
                }
            }
        ],
        msg="$sum should reject multi-element array syntax in $bucket",
    ),
    SumArityTest(
        "arity_empty_array_bucket",
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$sum": []}},
                }
            }
        ],
        msg="$sum should reject empty array syntax in $bucket",
    ),
    SumArityTest(
        "arity_single_element_bucket",
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$sum": ["$v"]}},
                }
            }
        ],
        msg="$sum should reject single-element array syntax in $bucket",
    ),
    SumArityTest(
        "arity_multi_element_bucket_auto",
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$sum": ["$v", "$v"]}},
                }
            }
        ],
        msg="$sum should reject multi-element array syntax in $bucketAuto",
    ),
    SumArityTest(
        "arity_empty_array_bucket_auto",
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$sum": []}},
                }
            }
        ],
        msg="$sum should reject empty array syntax in $bucketAuto",
    ),
    SumArityTest(
        "arity_single_element_bucket_auto",
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$sum": ["$v"]}},
                }
            }
        ],
        msg="$sum should reject single-element array syntax in $bucketAuto",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUM_ARITY_TESTS))
def test_accumulator_sum_arity(collection, test_case: SumArityTest):
    """Test $sum rejects array syntax in accumulator context."""
    collection.insert_one({"v": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        ACCUMULATOR_UNARY_OPERATOR_ERROR,
        msg=test_case.msg,
    )
