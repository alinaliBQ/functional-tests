"""Tests for $add argument handling.

Count variations, valid/invalid types per position, shorthand.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AddTest(BaseTestCase):
    """Test case for $add operator."""

    args: Any = None


# --- Argument count variations ---

ARGUMENT_COUNT_TESTS: list[AddTest] = [
    AddTest("no_args", args=[], expected=0, msg="Should return 0 for empty argument list"),
    AddTest("single_int", args=[5], expected=5, msg="Should return value for single int argument"),
    AddTest(
        "single_long",
        args=[Int64(5)],
        expected=Int64(5),
        msg="Should return value for single long argument",
    ),
    AddTest(
        "single_double",
        args=[3.14],
        expected=3.14,
        msg="Should return value for single double argument",
    ),
    AddTest(
        "single_decimal128",
        args=[Decimal128("5")],
        expected=Decimal128("5"),
        msg="Should return value for single decimal128 argument",
    ),
    AddTest(
        "single_date",
        args=[datetime(2024, 1, 1)],
        expected=datetime(2024, 1, 1),
        msg="Should return date unchanged for single date argument",
    ),
    AddTest(
        "single_null", args=[None], expected=None, msg="Should return null for single null argument"
    ),
    AddTest("two_args", args=[1, 2], expected=3, msg="Should add two int arguments"),
    AddTest("three_args", args=[1, 2, 3], expected=6, msg="Should add three int arguments"),
    AddTest(
        "ten_args",
        args=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        expected=55,
        msg="Should add ten int arguments",
    ),
    AddTest("twenty_ones", args=[1] * 20, expected=20, msg="Should add twenty arguments"),
    AddTest("fifty_ones", args=[1] * 50, expected=50, msg="Should add fifty arguments"),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_COUNT_TESTS))
def test_add_argument_count(collection, test):
    """Test $add with various argument counts."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Shorthand (non-array) argument ---

SHORTHAND_TESTS: list[AddTest] = [
    AddTest(
        "shorthand_int", args=5, expected=5, msg="Should accept single int without array wrapper"
    ),
    AddTest(
        "shorthand_long",
        args=Int64(5),
        expected=Int64(5),
        msg="Should accept single long without array wrapper",
    ),
    AddTest(
        "shorthand_double",
        args=3.14,
        expected=3.14,
        msg="Should accept single double without array wrapper",
    ),
    AddTest(
        "shorthand_decimal128",
        args=Decimal128("5"),
        expected=Decimal128("5"),
        msg="Should accept single decimal128 without array wrapper",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SHORTHAND_TESTS))
def test_add_shorthand(collection, test):
    """Test $add with non-array shorthand argument."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Per-input-position valid types (position 1) ---

VALID_FIRST_POSITION_TESTS: list[AddTest] = [
    AddTest("first_int", args=[5, 1], expected=6, msg="Should accept int in first position"),
    AddTest(
        "first_long",
        args=[Int64(5), 1],
        expected=Int64(6),
        msg="Should accept long in first position",
    ),
    AddTest(
        "first_double", args=[5.5, 1], expected=6.5, msg="Should accept double in first position"
    ),
    AddTest(
        "first_decimal128",
        args=[Decimal128("5"), 1],
        expected=Decimal128("6"),
        msg="Should accept decimal128 in first position",
    ),
    AddTest(
        "first_date",
        args=[datetime(2024, 1, 1), 1000],
        expected=datetime(2024, 1, 1, 0, 0, 1),
        msg="Should accept date in first position",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_FIRST_POSITION_TESTS))
def test_add_valid_first_position(collection, test):
    """Test $add with valid types in first position."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Per-input-position valid types (position 2) ---

VALID_SECOND_POSITION_TESTS: list[AddTest] = [
    AddTest("second_int", args=[1, 5], expected=6, msg="Should accept int in second position"),
    AddTest(
        "second_long",
        args=[1, Int64(5)],
        expected=Int64(6),
        msg="Should accept long in second position",
    ),
    AddTest(
        "second_double", args=[1, 5.5], expected=6.5, msg="Should accept double in second position"
    ),
    AddTest(
        "second_decimal128",
        args=[1, Decimal128("5")],
        expected=Decimal128("6"),
        msg="Should accept decimal128 in second position",
    ),
    AddTest(
        "second_date",
        args=[1000, datetime(2024, 1, 1)],
        expected=datetime(2024, 1, 1, 0, 0, 1),
        msg="Should accept date in second position",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_SECOND_POSITION_TESTS))
def test_add_valid_second_position(collection, test):
    """Test $add with valid types in second position."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Per-input-position invalid types ---

INVALID_TYPE_FIRST_POSITION_TESTS: list[AddTest] = [
    AddTest(
        "first_string",
        args=["hello", 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string in first position",
    ),
    AddTest(
        "first_bool",
        args=[True, 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject bool in first position",
    ),
    AddTest(
        "first_object",
        args=[{"a": 1}, 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject object in first position",
    ),
    AddTest(
        "first_array",
        args=[[1, 2], 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array in first position",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_TYPE_FIRST_POSITION_TESTS))
def test_add_invalid_first_position(collection, test):
    """Test $add rejects invalid types in first position."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


INVALID_TYPE_SECOND_POSITION_TESTS: list[AddTest] = [
    AddTest(
        "second_string",
        args=[1, "hello"],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string in second position",
    ),
    AddTest(
        "second_bool",
        args=[1, True],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject bool in second position",
    ),
    AddTest(
        "second_object",
        args=[1, {"a": 1}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject object in second position",
    ),
    AddTest(
        "second_array",
        args=[1, [1, 2]],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array in second position",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_TYPE_SECOND_POSITION_TESTS))
def test_add_invalid_second_position(collection, test):
    """Test $add rejects invalid types in second position."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
