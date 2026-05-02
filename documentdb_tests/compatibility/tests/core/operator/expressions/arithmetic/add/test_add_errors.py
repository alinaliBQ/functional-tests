"""Tests for $add error code validation with all invalid BSON types."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
class AddErrorTest(BaseTestCase):
    """Test case for $add error validation."""

    args: Any = None


# --- Invalid types in first position ---

INVALID_FIRST_TESTS: list[AddErrorTest] = [
    AddErrorTest(
        "first_string",
        args=["hello", 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string in first position",
    ),
    AddErrorTest(
        "first_bool",
        args=[True, 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject bool in first position",
    ),
    AddErrorTest(
        "first_object",
        args=[{"a": 1}, 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject object in first position",
    ),
    AddErrorTest(
        "first_array",
        args=[[1, 2], 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array in first position",
    ),
    AddErrorTest(
        "first_binData",
        args=[Binary(b"\x00"), 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject binData in first position",
    ),
    AddErrorTest(
        "first_objectId",
        args=[ObjectId(), 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject objectId in first position",
    ),
    AddErrorTest(
        "first_regex",
        args=[Regex("abc"), 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject regex in first position",
    ),
    AddErrorTest(
        "first_javascript",
        args=[Code("function(){}"), 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject javascript in first position",
    ),
    AddErrorTest(
        "first_timestamp",
        args=[Timestamp(1, 1), 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject timestamp in first position",
    ),
    AddErrorTest(
        "first_minKey",
        args=[MinKey(), 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject minKey in first position",
    ),
    AddErrorTest(
        "first_maxKey",
        args=[MaxKey(), 1],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject maxKey in first position",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_FIRST_TESTS))
def test_add_invalid_type_first(collection, test):
    """Test $add rejects invalid BSON types in first position."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


# --- Invalid types in second position ---

INVALID_SECOND_TESTS: list[AddErrorTest] = [
    AddErrorTest(
        "second_string",
        args=[1, "hello"],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string in second position",
    ),
    AddErrorTest(
        "second_bool",
        args=[1, True],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject bool in second position",
    ),
    AddErrorTest(
        "second_object",
        args=[1, {"a": 1}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject object in second position",
    ),
    AddErrorTest(
        "second_array",
        args=[1, [1, 2]],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array in second position",
    ),
    AddErrorTest(
        "second_binData",
        args=[1, Binary(b"\x00")],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject binData in second position",
    ),
    AddErrorTest(
        "second_objectId",
        args=[1, ObjectId()],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject objectId in second position",
    ),
    AddErrorTest(
        "second_regex",
        args=[1, Regex("abc")],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject regex in second position",
    ),
    AddErrorTest(
        "second_javascript",
        args=[1, Code("function(){}")],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject javascript in second position",
    ),
    AddErrorTest(
        "second_timestamp",
        args=[1, Timestamp(1, 1)],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject timestamp in second position",
    ),
    AddErrorTest(
        "second_minKey",
        args=[1, MinKey()],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject minKey in second position",
    ),
    AddErrorTest(
        "second_maxKey",
        args=[1, MaxKey()],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject maxKey in second position",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_SECOND_TESTS))
def test_add_invalid_type_second(collection, test):
    """Test $add rejects invalid BSON types in second position."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


# --- Date-specific errors ---

DATE_ERROR_TESTS: list[AddErrorTest] = [
    AddErrorTest(
        "two_dates",
        args=[datetime(2024, 1, 1), datetime(2024, 1, 2)],
        error_code=MORE_THAN_ONE_DATE_ERROR,
        msg="Should reject two dates",
    ),
    AddErrorTest(
        "date_plus_inf",
        args=[datetime(2024, 1, 1), float("inf")],
        error_code=OVERFLOW_ERROR,
        msg="Should reject date + Infinity",
    ),
    AddErrorTest(
        "date_plus_nan",
        args=[datetime(2024, 1, 1), float("nan")],
        error_code=OVERFLOW_ERROR,
        msg="Should reject date + NaN",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATE_ERROR_TESTS))
def test_add_date_errors(collection, test):
    """Test $add date-specific error codes."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
