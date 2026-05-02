"""Tests for $add overflow, underflow, double precision boundaries, and precision loss."""

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    DECIMAL128_MAX,
    DECIMAL128_MIN_POSITIVE,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)


@dataclass(frozen=True)
class AddTest(BaseTestCase):
    """Test case for $add operator."""

    args: Any = None


# --- Int32 overflow → long ---

INT32_OVERFLOW_TESTS: list[AddTest] = [
    AddTest(
        "int32_max_plus_1",
        args=[INT32_MAX, 1],
        expected=Int64(2147483648),
        msg="Should promote int32 max + 1 to long",
    ),
    AddTest(
        "int32_min_minus_1",
        args=[INT32_MIN, -1],
        expected=Int64(-2147483649),
        msg="Should promote int32 min - 1 to long",
    ),
    AddTest(
        "int32_max_plus_int32_max",
        args=[INT32_MAX, INT32_MAX],
        expected=Int64(4294967294),
        msg="Should promote int32 max + int32 max to long",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INT32_OVERFLOW_TESTS))
def test_add_int32_overflow(collection, test):
    """Test $add int32 overflow promotes to long."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Int64 overflow → double ---

INT64_OVERFLOW_TESTS: list[AddTest] = [
    AddTest(
        "int64_max_plus_1",
        args=[INT64_MAX, Int64(1)],
        expected=9.223372036854776e18,
        msg="Should promote int64 max + 1 to double",
    ),
    AddTest(
        "int64_min_minus_1",
        args=[INT64_MIN, Int64(-1)],
        expected=-9.223372036854776e18,
        msg="Should promote int64 min - 1 to double",
    ),
    AddTest(
        "int64_max_plus_int32",
        args=[INT64_MAX, 1],
        expected=9.223372036854776e18,
        msg="Should promote int64 max + int32 to double",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INT64_OVERFLOW_TESTS))
def test_add_int64_overflow(collection, test):
    """Test $add int64 overflow promotes to double."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Double overflow → Infinity ---

DOUBLE_OVERFLOW_TESTS: list[AddTest] = [
    AddTest(
        "double_max_plus_double_max",
        args=[DOUBLE_MAX, DOUBLE_MAX],
        expected=FLOAT_INFINITY,
        msg="Should return Infinity for double max + double max",
    ),
    AddTest(
        "double_min_plus_double_min",
        args=[-DOUBLE_MAX, -DOUBLE_MAX],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should return -Infinity for -double max + -double max",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DOUBLE_OVERFLOW_TESTS))
def test_add_double_overflow(collection, test):
    """Test $add double overflow to Infinity."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Decimal128 overflow ---

DECIMAL128_OVERFLOW_TESTS: list[AddTest] = [
    AddTest(
        "decimal128_max_plus_max",
        args=[DECIMAL128_MAX, DECIMAL128_MAX],
        expected=Decimal128("Infinity"),
        msg="Should return Decimal128 Infinity for decimal128 max + max",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DECIMAL128_OVERFLOW_TESTS))
def test_add_decimal128_overflow(collection, test):
    """Test $add decimal128 overflow."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Underflow ---

UNDERFLOW_TESTS: list[AddTest] = [
    AddTest(
        "double_subnormal_cancel",
        args=[DOUBLE_MIN_SUBNORMAL, -DOUBLE_MIN_SUBNORMAL],
        expected=0.0,
        msg="Should return 0.0 for subnormal + negative subnormal",
    ),
    AddTest(
        "decimal128_min_cancel",
        args=[DECIMAL128_MIN_POSITIVE, Decimal128("-1E-6176")],
        expected=Decimal128("0E-6176"),
        msg="Should return Decimal128 0 for min positive + max negative",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNDERFLOW_TESTS))
def test_add_underflow(collection, test):
    """Test $add underflow handling."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Double precision boundaries ---

DOUBLE_PRECISION_TESTS: list[AddTest] = [
    AddTest(
        "near_max_plus_small",
        args=[DOUBLE_NEAR_MAX, 1.0],
        expected=1e308,
        msg="Should handle near-max double + small value",
    ),
    AddTest(
        "subnormal_plus_subnormal",
        args=[DOUBLE_MIN_SUBNORMAL, DOUBLE_MIN_SUBNORMAL],
        expected=1e-323,
        msg="Should handle subnormal + subnormal",
    ),
    AddTest(
        "safe_int_plus_1",
        args=[DOUBLE_MAX_SAFE_INTEGER, 1.0],
        expected=9007199254740992.0,
        msg="Should show precision loss at max safe integer boundary",
    ),
    AddTest(
        "near_min_plus_near_min",
        args=[DOUBLE_NEAR_MIN, DOUBLE_NEAR_MIN],
        expected=2e-308,
        msg="Should handle near-min double + near-min double",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DOUBLE_PRECISION_TESTS))
def test_add_double_precision(collection, test):
    """Test $add double precision boundary behavior."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Chained overflow across multiple arguments ---

CHAINED_OVERFLOW_TESTS: list[AddTest] = [
    AddTest(
        "three_int32_max",
        args=[INT32_MAX, INT32_MAX, INT32_MAX],
        expected=Int64(6442450941),
        msg="Should handle chained int32 overflow across three values",
    ),
    AddTest(
        "int64_max_plus_int32_1",
        args=[INT64_MAX, 1],
        expected=9.223372036854776e18,
        msg="Should handle int64 max + int32 1 overflow to double",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CHAINED_OVERFLOW_TESTS))
def test_add_chained_overflow(collection, test):
    """Test $add chained overflow across multiple arguments."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Precision loss scenarios ---

PRECISION_LOSS_TESTS: list[AddTest] = [
    AddTest(
        "large_int64_plus_double",
        args=[Int64(9007199254740993), 1.0],
        expected=9007199254740992.0,
        msg="Should show precision loss when large int64 promotes to double",
    ),
    AddTest(
        "decimal128_preserves",
        args=[Decimal128("0.1"), Decimal128("0.2")],
        expected=Decimal128("0.3"),
        msg="Should preserve exact precision with decimal128",
    ),
    AddTest(
        "double_precision_loss",
        args=[0.1, 0.2],
        expected=0.30000000000000004,
        msg="Should show IEEE 754 precision loss with double",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PRECISION_LOSS_TESTS))
def test_add_precision_loss(collection, test):
    """Test $add precision loss scenarios."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)
