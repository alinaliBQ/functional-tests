"""Tests for $add type conversion, sign handling, negative zero, and input correlation."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import DOUBLE_NEGATIVE_ZERO


@dataclass(frozen=True)
class AddTest(BaseTestCase):
    """Test case for $add operator."""

    args: Any = None


# --- Two-input type combinations and result types ---

TYPE_COMBINATION_TESTS: list[AddTest] = [
    AddTest("int_int", args=[3, 4], expected=7, msg="Should return int for int + int"),
    AddTest(
        "int_long", args=[3, Int64(4)], expected=Int64(7), msg="Should return long for int + long"
    ),
    AddTest("int_double", args=[3, 4.5], expected=7.5, msg="Should return double for int + double"),
    AddTest(
        "int_decimal128",
        args=[3, Decimal128("4")],
        expected=Decimal128("7"),
        msg="Should return decimal128 for int + decimal128",
    ),
    AddTest(
        "long_long",
        args=[Int64(3), Int64(4)],
        expected=Int64(7),
        msg="Should return long for long + long",
    ),
    AddTest(
        "long_double",
        args=[Int64(3), 4.5],
        expected=7.5,
        msg="Should return double for long + double",
    ),
    AddTest(
        "long_decimal128",
        args=[Int64(3), Decimal128("4")],
        expected=Decimal128("7"),
        msg="Should return decimal128 for long + decimal128",
    ),
    AddTest(
        "double_double",
        args=[3.5, 4.5],
        expected=8.0,
        msg="Should return double for double + double",
    ),
    AddTest(
        "double_decimal128",
        args=[3.5, Decimal128("4")],
        expected=Decimal128("7.50000000000000"),
        msg="Should return decimal128 for double + decimal128",
    ),
    AddTest(
        "decimal128_decimal128",
        args=[Decimal128("3"), Decimal128("4")],
        expected=Decimal128("7"),
        msg="Should return decimal128 for decimal128 + decimal128",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TYPE_COMBINATION_TESTS))
def test_add_type_combinations(collection, test):
    """Test $add numeric type promotion rules."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Commutativity ---

COMMUTATIVITY_TESTS: list[AddTest] = [
    AddTest(
        "long_int", args=[Int64(3), 4], expected=Int64(7), msg="Should return long for long + int"
    ),
    AddTest("double_int", args=[4.5, 3], expected=7.5, msg="Should return double for double + int"),
    AddTest(
        "decimal128_int",
        args=[Decimal128("4"), 3],
        expected=Decimal128("7"),
        msg="Should return decimal128 for decimal128 + int",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMUTATIVITY_TESTS))
def test_add_commutativity(collection, test):
    """Test $add commutativity — same result regardless of argument order."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Progressive type promotion with 3+ arguments ---

PROGRESSIVE_PROMOTION_TESTS: list[AddTest] = [
    AddTest(
        "int_long_double",
        args=[1, Int64(2), 3.5],
        expected=6.5,
        msg="Should promote to double for int + long + double",
    ),
    AddTest(
        "int_long_decimal128",
        args=[1, Int64(2), Decimal128("3")],
        expected=Decimal128("6"),
        msg="Should promote to decimal128 for int + long + decimal128",
    ),
    AddTest(
        "int_long_double_decimal128",
        args=[1, Int64(2), 3.5, Decimal128("4")],
        expected=Decimal128("10.50000000000000"),
        msg="Should promote to decimal128 for all four types",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROGRESSIVE_PROMOTION_TESTS))
def test_add_progressive_promotion(collection, test):
    """Test $add progressive type promotion with 3+ arguments."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Sign handling ---

SIGN_TESTS: list[AddTest] = [
    AddTest("pos_pos", args=[5, 3], expected=8, msg="Should add positive + positive"),
    AddTest("pos_neg", args=[5, -3], expected=2, msg="Should add positive + negative"),
    AddTest("neg_neg", args=[-5, -3], expected=-8, msg="Should add negative + negative"),
    AddTest("pos_zero", args=[5, 0], expected=5, msg="Should add positive + zero"),
    AddTest("neg_zero", args=[-5, 0], expected=-5, msg="Should add negative + zero"),
    AddTest("zero_zero", args=[0, 0], expected=0, msg="Should add zero + zero"),
]


@pytest.mark.parametrize("test", pytest_params(SIGN_TESTS))
def test_add_sign(collection, test):
    """Test $add sign handling."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Negative zero handling ---

NEGATIVE_ZERO_TESTS: list[AddTest] = [
    AddTest(
        "neg_zero_plus_zero",
        args=[DOUBLE_NEGATIVE_ZERO, 0.0],
        expected=0.0,
        msg="Should return 0.0 for -0.0 + 0.0",
    ),
    AddTest(
        "neg_zero_plus_neg_zero",
        args=[DOUBLE_NEGATIVE_ZERO, DOUBLE_NEGATIVE_ZERO],
        expected=0.0,
        msg="Should return 0.0 for -0.0 + -0.0",
    ),
    AddTest(
        "neg_zero_plus_positive",
        args=[DOUBLE_NEGATIVE_ZERO, 1.0],
        expected=1.0,
        msg="Should return 1.0 for -0.0 + 1.0",
    ),
    AddTest(
        "dec128_neg_zero_plus_zero",
        args=[Decimal128("-0"), Decimal128("0")],
        expected=Decimal128("0"),
        msg="Should return 0 for Decimal128 -0 + 0",
    ),
    AddTest(
        "dec128_neg_zero_plus_neg_zero",
        args=[Decimal128("-0"), Decimal128("-0")],
        expected=Decimal128("0"),
        msg="Should return 0 for Decimal128 -0 + -0",
    ),
    AddTest(
        "neg_zero_plus_int_zero",
        args=[DOUBLE_NEGATIVE_ZERO, 0],
        expected=0.0,
        msg="Should return 0.0 for -0.0 + int 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NEGATIVE_ZERO_TESTS))
def test_add_negative_zero(collection, test):
    """Test $add negative zero handling."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Input correlation: date + numeric types ---

DATE_CORRELATION_TESTS: list[AddTest] = [
    AddTest(
        "date_plus_int",
        args=[datetime(2024, 1, 1), 86400000],
        expected=datetime(2024, 1, 2),
        msg="Should add date + int milliseconds",
    ),
    AddTest(
        "date_plus_long",
        args=[datetime(2024, 1, 1), Int64(86400000)],
        expected=datetime(2024, 1, 2),
        msg="Should add date + long milliseconds",
    ),
    AddTest(
        "date_plus_double",
        args=[datetime(2024, 1, 1), 86400000.0],
        expected=datetime(2024, 1, 2),
        msg="Should add date + double milliseconds",
    ),
    AddTest(
        "date_plus_decimal128",
        args=[datetime(2024, 1, 1), Decimal128("86400000")],
        expected=datetime(2024, 1, 2),
        msg="Should add date + decimal128 milliseconds",
    ),
    AddTest(
        "date_int_long",
        args=[datetime(2024, 1, 1), 1000, Int64(2000)],
        expected=datetime(2024, 1, 1, 0, 0, 3),
        msg="Should add date + int + long",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATE_CORRELATION_TESTS))
def test_add_date_correlation(collection, test):
    """Test $add date + numeric type correlations."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)
