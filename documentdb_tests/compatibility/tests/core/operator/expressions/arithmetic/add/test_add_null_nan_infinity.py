"""Tests for $add null/missing handling, NaN handling, and infinity handling."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccessNaN
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)


@dataclass(frozen=True)
class AddTest(BaseTestCase):
    """Test case for $add operator."""

    args: Any = None
    doc: Optional[dict] = None


# --- Null/Missing handling ---

NULL_TESTS: list[AddTest] = [
    AddTest(
        "null_first",
        args=[None, 1],
        expected=None,
        msg="Should return null when null in first position",
    ),
    AddTest(
        "null_second",
        args=[1, None],
        expected=None,
        msg="Should return null when null in second position",
    ),
    AddTest("null_both", args=[None, None], expected=None, msg="Should return null when both null"),
    AddTest(
        "null_and_date",
        args=[None, datetime(2024, 1, 1)],
        expected=None,
        msg="Should return null when null with date",
    ),
    AddTest(
        "null_among_many",
        args=[1, None, 3],
        expected=None,
        msg="Should return null when null among valid values",
    ),
    AddTest(
        "null_date_numeric",
        args=[None, datetime(2024, 1, 1), 1000],
        expected=None,
        msg="Should return null when null with date and numeric",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_TESTS))
def test_add_null(collection, test):
    """Test $add null propagation."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


MISSING_TESTS: list[AddTest] = [
    AddTest(
        "missing_first",
        args=["$nonexistent", 1],
        doc={},
        expected=None,
        msg="Should return null when missing field in first position",
    ),
    AddTest(
        "missing_second",
        args=[1, "$nonexistent"],
        doc={},
        expected=None,
        msg="Should return null when missing field in second position",
    ),
    AddTest(
        "missing_and_date",
        args=["$nonexistent", datetime(2024, 1, 1)],
        doc={},
        expected=None,
        msg="Should return null when missing field with date",
    ),
    AddTest(
        "missing_among_many",
        args=[1, "$nonexistent", 3],
        doc={},
        expected=None,
        msg="Should return null when missing field among valid values",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MISSING_TESTS))
def test_add_missing(collection, test):
    """Test $add missing field propagation."""
    result = execute_expression_with_insert(collection, {"$add": test.args}, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- NaN handling ---

NAN_TESTS: list[AddTest] = [
    AddTest(
        "nan_plus_int",
        args=[FLOAT_NAN, 1],
        expected=FLOAT_NAN,
        msg="Should return NaN for NaN + int",
    ),
    AddTest(
        "nan_plus_long",
        args=[FLOAT_NAN, Int64(1)],
        expected=FLOAT_NAN,
        msg="Should return NaN for NaN + long",
    ),
    AddTest(
        "nan_plus_double",
        args=[FLOAT_NAN, 1.5],
        expected=FLOAT_NAN,
        msg="Should return NaN for NaN + double",
    ),
    AddTest(
        "nan_plus_decimal128",
        args=[FLOAT_NAN, Decimal128("1")],
        expected=DECIMAL128_NAN,
        msg="Should return Decimal128 NaN for NaN + decimal128",
    ),
    AddTest(
        "decimal128_nan_plus_int",
        args=[DECIMAL128_NAN, 1],
        expected=DECIMAL128_NAN,
        msg="Should return Decimal128 NaN for Decimal128 NaN + int",
    ),
    AddTest(
        "nan_plus_nan",
        args=[FLOAT_NAN, FLOAT_NAN],
        expected=FLOAT_NAN,
        msg="Should return NaN for NaN + NaN",
    ),
    AddTest(
        "float_nan_plus_decimal128_nan",
        args=[FLOAT_NAN, DECIMAL128_NAN],
        expected=DECIMAL128_NAN,
        msg="Should return Decimal128 NaN for float NaN + Decimal128 NaN",
    ),
    AddTest(
        "int_plus_nan",
        args=[1, FLOAT_NAN],
        expected=FLOAT_NAN,
        msg="Should return NaN for int + NaN (commutative)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAN_TESTS))
def test_add_nan(collection, test):
    """Test $add NaN propagation."""
    result = execute_expression(collection, {"$add": test.args})
    assertSuccessNaN(result, [{"result": test.expected}], msg=test.msg)


# --- Infinity handling ---

INFINITY_TESTS: list[AddTest] = [
    AddTest(
        "inf_plus_int",
        args=[FLOAT_INFINITY, 1],
        expected=FLOAT_INFINITY,
        msg="Should return Infinity for Infinity + int",
    ),
    AddTest(
        "neg_inf_plus_int",
        args=[FLOAT_NEGATIVE_INFINITY, 1],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should return -Infinity for -Infinity + int",
    ),
    AddTest(
        "inf_plus_inf",
        args=[FLOAT_INFINITY, FLOAT_INFINITY],
        expected=FLOAT_INFINITY,
        msg="Should return Infinity for Infinity + Infinity",
    ),
    AddTest(
        "neg_inf_plus_neg_inf",
        args=[FLOAT_NEGATIVE_INFINITY, FLOAT_NEGATIVE_INFINITY],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should return -Infinity for -Infinity + -Infinity",
    ),
    AddTest(
        "dec128_inf_plus_int",
        args=[DECIMAL128_INFINITY, 1],
        expected=DECIMAL128_INFINITY,
        msg="Should return Decimal128 Infinity for Decimal128 Infinity + int",
    ),
    AddTest(
        "dec128_neg_inf_plus_dec128_neg_inf",
        args=[DECIMAL128_NEGATIVE_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="Should return Decimal128 -Infinity for Decimal128 -Infinity + Decimal128 -Infinity",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INFINITY_TESTS))
def test_add_infinity(collection, test):
    """Test $add infinity handling."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


INFINITY_NAN_RESULT_TESTS: list[AddTest] = [
    AddTest(
        "inf_plus_neg_inf",
        args=[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY],
        expected=FLOAT_NAN,
        msg="Should return NaN for Infinity + -Infinity",
    ),
    AddTest(
        "inf_plus_nan",
        args=[FLOAT_INFINITY, FLOAT_NAN],
        expected=FLOAT_NAN,
        msg="Should return NaN for Infinity + NaN",
    ),
    AddTest(
        "dec128_inf_plus_dec128_neg_inf",
        args=[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        expected=DECIMAL128_NAN,
        msg="Should return Decimal128 NaN for Decimal128 Infinity + Decimal128 -Infinity",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INFINITY_NAN_RESULT_TESTS))
def test_add_infinity_nan_result(collection, test):
    """Test $add infinity combinations that produce NaN."""
    result = execute_expression(collection, {"$add": test.args})
    assertSuccessNaN(result, [{"result": test.expected}], msg=test.msg)


# --- NaN/Infinity + invalid type errors ---

NAN_INF_TYPE_ERROR_TESTS: list[AddTest] = [
    AddTest(
        "nan_plus_string",
        args=[FLOAT_NAN, "hello"],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject NaN + string",
    ),
    AddTest(
        "string_plus_nan",
        args=["hello", FLOAT_NAN],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string + NaN",
    ),
    AddTest(
        "inf_plus_string",
        args=[FLOAT_INFINITY, "hello"],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject Infinity + string",
    ),
    AddTest(
        "string_plus_inf",
        args=["hello", FLOAT_INFINITY],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string + Infinity",
    ),
    AddTest(
        "dec128_nan_plus_string",
        args=[DECIMAL128_NAN, "hello"],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject Decimal128 NaN + string",
    ),
    AddTest(
        "dec128_inf_plus_string",
        args=[DECIMAL128_INFINITY, "hello"],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject Decimal128 Infinity + string",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NAN_INF_TYPE_ERROR_TESTS))
def test_add_nan_inf_type_errors(collection, test):
    """Test $add rejects invalid types even with NaN/Infinity operands."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
