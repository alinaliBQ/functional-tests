"""Tests for $add date arithmetic — positions, rounding, left-to-right, boundaries, errors."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    MORE_THAN_ONE_DATE_ERROR,
    OVERFLOW_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AddTest(BaseTestCase):
    """Test case for $add operator."""

    args: Any = None


# --- Date + numeric types ---

DATE_NUMERIC_TESTS: list[AddTest] = [
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
]


@pytest.mark.parametrize("test", pytest_params(DATE_NUMERIC_TESTS))
def test_add_date_numeric(collection, test):
    """Test $add date + numeric types."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Date position variations ---

DATE_POSITION_TESTS: list[AddTest] = [
    AddTest(
        "date_first",
        args=[datetime(2024, 1, 1), 1000],
        expected=datetime(2024, 1, 1, 0, 0, 1),
        msg="Should accept date in first position",
    ),
    AddTest(
        "date_second",
        args=[1000, datetime(2024, 1, 1)],
        expected=datetime(2024, 1, 1, 0, 0, 1),
        msg="Should accept date in second position",
    ),
    AddTest(
        "date_middle",
        args=[500, datetime(2024, 1, 1), 500],
        expected=datetime(2024, 1, 1, 0, 0, 1),
        msg="Should accept date in middle position",
    ),
    AddTest(
        "date_last",
        args=[500, 500, datetime(2024, 1, 1)],
        expected=datetime(2024, 1, 1, 0, 0, 1),
        msg="Should accept date in last position",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATE_POSITION_TESTS))
def test_add_date_position(collection, test):
    """Test $add with date in various positions."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Date + fractional values (rounding) ---

DATE_ROUNDING_TESTS: list[AddTest] = [
    AddTest(
        "date_plus_0.1",
        args=[datetime(2024, 1, 1), 0.1],
        expected=datetime(2024, 1, 1),
        msg="Should round 0.1 to 0ms",
    ),
    AddTest(
        "date_plus_0.49",
        args=[datetime(2024, 1, 1), 0.49],
        expected=datetime(2024, 1, 1),
        msg="Should round 0.49 to 0ms",
    ),
    AddTest(
        "date_plus_0.5",
        args=[datetime(2024, 1, 1), 0.5],
        expected=datetime(2024, 1, 1, 0, 0, 0, 1000),
        msg="Should round 0.5 to 1ms",
    ),
    AddTest(
        "date_plus_0.51",
        args=[datetime(2024, 1, 1), 0.51],
        expected=datetime(2024, 1, 1, 0, 0, 0, 1000),
        msg="Should round 0.51 to 1ms",
    ),
    AddTest(
        "date_plus_0.6",
        args=[datetime(2024, 1, 1), 0.6],
        expected=datetime(2024, 1, 1, 0, 0, 0, 1000),
        msg="Should round 0.6 to 1ms",
    ),
    AddTest(
        "date_plus_1.5",
        args=[datetime(2024, 1, 1), 1.5],
        expected=datetime(2024, 1, 1, 0, 0, 0, 2000),
        msg="Should round 1.5 to 2ms",
    ),
    AddTest(
        "date_plus_neg0.5",
        args=[datetime(2024, 1, 1), -0.5],
        expected=datetime(2023, 12, 31, 23, 59, 59, 999000),
        msg="Should round -0.5 to -1ms",
    ),
    AddTest(
        "date_plus_neg0.51",
        args=[datetime(2024, 1, 1), -0.51],
        expected=datetime(2023, 12, 31, 23, 59, 59, 999000),
        msg="Should round -0.51 to -1ms",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATE_ROUNDING_TESTS))
def test_add_date_rounding(collection, test):
    """Test $add date + fractional value rounding behavior."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Left-to-right evaluation with date and fractional values ---

LEFT_TO_RIGHT_TESTS: list[AddTest] = [
    AddTest(
        "ltr_full",
        args=[1.5, 1.6, datetime(2024, 1, 1), 1.5, 1.5],
        expected=datetime(2024, 1, 1, 0, 0, 0, 7000),
        msg="Should evaluate left-to-right with rounding per step",
    ),
    AddTest(
        "ltr_frac_before_date",
        args=[0.4, 0.4, datetime(2024, 1, 1)],
        expected=datetime(2024, 1, 1, 0, 0, 0, 1000),
        msg="Should sum fractional before date then round",
    ),
    AddTest(
        "ltr_frac_after_date",
        args=[datetime(2024, 1, 1), 0.4, 0.4],
        expected=datetime(2024, 1, 1),
        msg="Should round each fractional individually after date",
    ),
    AddTest(
        "ltr_int_before_frac_after",
        args=[3, datetime(2024, 1, 1), 0.6],
        expected=datetime(2024, 1, 1, 0, 0, 0, 4000),
        msg="Should add int before date then round fractional after",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LEFT_TO_RIGHT_TESTS))
def test_add_left_to_right(collection, test):
    """Test $add left-to-right evaluation with date and fractional values."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Negative milliseconds with date ---

DATE_NEGATIVE_MS_TESTS: list[AddTest] = [
    AddTest(
        "date_minus_day",
        args=[datetime(2024, 1, 2), -86400000],
        expected=datetime(2024, 1, 1),
        msg="Should subtract one day with negative int",
    ),
    AddTest(
        "date_plus_zero",
        args=[datetime(2024, 1, 1), 0],
        expected=datetime(2024, 1, 1),
        msg="Should return same date when adding zero",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATE_NEGATIVE_MS_TESTS))
def test_add_date_negative_ms(collection, test):
    """Test $add date + negative milliseconds."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Date + negative zero ---

DATE_NEG_ZERO_TESTS: list[AddTest] = [
    AddTest(
        "date_plus_double_neg_zero",
        args=[datetime(2024, 1, 1), -0.0],
        expected=datetime(2024, 1, 1),
        msg="Should return same date for date + double -0.0",
    ),
    AddTest(
        "date_plus_dec128_neg_zero",
        args=[datetime(2024, 1, 1), Decimal128("-0")],
        expected=datetime(2024, 1, 1),
        msg="Should return same date for date + Decimal128 -0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATE_NEG_ZERO_TESTS))
def test_add_date_negative_zero(collection, test):
    """Test $add date + negative zero."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Date + Decimal128 milliseconds ---

DATE_DECIMAL128_TESTS: list[AddTest] = [
    AddTest(
        "date_dec_whole",
        args=[datetime(2024, 1, 1), Decimal128("1000")],
        expected=datetime(2024, 1, 1, 0, 0, 1),
        msg="Should add date + Decimal128 whole number ms",
    ),
    AddTest(
        "date_dec_frac",
        args=[datetime(2024, 1, 1), Decimal128("1000.5")],
        expected=datetime(2024, 1, 1, 0, 0, 1),
        msg="Should round Decimal128 fractional ms",
    ),
    AddTest(
        "date_dec_tiny",
        args=[datetime(2024, 1, 1), Decimal128("0.0001")],
        expected=datetime(2024, 1, 1),
        msg="Should round Decimal128 tiny value to 0ms",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATE_DECIMAL128_TESTS))
def test_add_date_decimal128(collection, test):
    """Test $add date + Decimal128 milliseconds."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Date boundaries ---

DATE_BOUNDARY_TESTS: list[AddTest] = [
    AddTest(
        "before_epoch",
        args=[datetime(1960, 1, 1), 1000],
        expected=datetime(1960, 1, 1, 0, 0, 1),
        msg="Should handle date before epoch",
    ),
    AddTest(
        "cross_epoch",
        args=[datetime(1970, 1, 1), -1000],
        expected=datetime(1969, 12, 31, 23, 59, 59),
        msg="Should cross epoch boundary",
    ),
    AddTest(
        "year_1",
        args=[datetime(1, 1, 1), 1],
        expected=datetime(1, 1, 1, 0, 0, 0, 1000),
        msg="Should handle very early date",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATE_BOUNDARY_TESTS))
def test_add_date_boundaries(collection, test):
    """Test $add with date boundary values."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Invalid date combinations ---

DATE_ERROR_TESTS: list[AddTest] = [
    AddTest(
        "two_dates",
        args=[datetime(2024, 1, 1), datetime(2024, 1, 2)],
        error_code=MORE_THAN_ONE_DATE_ERROR,
        msg="Should reject two dates",
    ),
    AddTest(
        "date_num_date",
        args=[datetime(2024, 1, 1), 1000, datetime(2024, 1, 2)],
        error_code=MORE_THAN_ONE_DATE_ERROR,
        msg="Should reject date + numeric + date",
    ),
    AddTest(
        "date_inf",
        args=[datetime(2024, 1, 1), float("inf")],
        error_code=OVERFLOW_ERROR,
        msg="Should reject date + Infinity",
    ),
    AddTest(
        "date_nan",
        args=[datetime(2024, 1, 1), float("nan")],
        error_code=OVERFLOW_ERROR,
        msg="Should reject date + NaN",
    ),
    AddTest(
        "date_string",
        args=[datetime(2024, 1, 1), "hello"],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject date + string",
    ),
    AddTest(
        "date_bool",
        args=[datetime(2024, 1, 1), True],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject date + bool",
    ),
    AddTest(
        "date_null",
        args=[datetime(2024, 1, 1), None],
        expected=None,
        msg="Should return null for date + null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATE_ERROR_TESTS))
def test_add_date_errors(collection, test):
    """Test $add invalid date combinations."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
