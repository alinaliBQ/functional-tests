"""Tests for commitTransaction command field type acceptance.

Validates that the commitTransaction command's primary field accepts all BSON
types. All types produce error 125 (NoSuchTransaction) because no transaction
is active, confirming the field value itself is not type-checked.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_command_test_case import (  # noqa: E501
    SessionCommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import NO_SUCH_TRANSACTION_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [Field Type Acceptance]: commitTransaction accepts any BSON type as
# the command field value without a type error.
FIELD_TYPE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "field_int32_positive",
        command={"commitTransaction": 1},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept int32 positive value",
    ),
    SessionCommandTestCase(
        "field_int32_negative",
        command={"commitTransaction": -1},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept int32 negative value",
    ),
    SessionCommandTestCase(
        "field_int32_zero",
        command={"commitTransaction": 0},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept int32 zero value",
    ),
    SessionCommandTestCase(
        "field_int64",
        command={"commitTransaction": Int64(1)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept int64 value",
    ),
    SessionCommandTestCase(
        "field_int64_max",
        command={"commitTransaction": Int64(9_223_372_036_854_775_807)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept int64 max value",
    ),
    SessionCommandTestCase(
        "field_double",
        command={"commitTransaction": 1.0},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept double value",
    ),
    SessionCommandTestCase(
        "field_double_negative",
        command={"commitTransaction": -1.0},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept negative double value",
    ),
    SessionCommandTestCase(
        "field_double_zero",
        command={"commitTransaction": 0.0},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept double zero value",
    ),
    SessionCommandTestCase(
        "field_decimal128",
        command={"commitTransaction": Decimal128("1")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept Decimal128 value",
    ),
    SessionCommandTestCase(
        "field_bool_true",
        command={"commitTransaction": True},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept bool true value",
    ),
    SessionCommandTestCase(
        "field_bool_false",
        command={"commitTransaction": False},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept bool false value",
    ),
    SessionCommandTestCase(
        "field_nan",
        command={"commitTransaction": float("nan")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept NaN value",
    ),
    SessionCommandTestCase(
        "field_infinity",
        command={"commitTransaction": float("inf")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept Infinity value",
    ),
    SessionCommandTestCase(
        "field_string",
        command={"commitTransaction": "commitTransaction"},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept string value",
    ),
    SessionCommandTestCase(
        "field_string_empty",
        command={"commitTransaction": ""},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept empty string value",
    ),
    SessionCommandTestCase(
        "field_null",
        command={"commitTransaction": None},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept null value",
    ),
    SessionCommandTestCase(
        "field_object_empty",
        command={"commitTransaction": {}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept empty object value",
    ),
    SessionCommandTestCase(
        "field_object_nonempty",
        command={"commitTransaction": {"key": "value"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept non-empty object value",
    ),
    SessionCommandTestCase(
        "field_array_empty",
        command={"commitTransaction": []},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept empty array value",
    ),
    SessionCommandTestCase(
        "field_array_nonempty",
        command={"commitTransaction": [1, 2]},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept non-empty array value",
    ),
    SessionCommandTestCase(
        "field_binary",
        command={"commitTransaction": Binary(b"\x00")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept Binary value",
    ),
    SessionCommandTestCase(
        "field_objectid",
        command={"commitTransaction": ObjectId()},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept ObjectId value",
    ),
    SessionCommandTestCase(
        "field_datetime",
        command={"commitTransaction": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept datetime value",
    ),
    SessionCommandTestCase(
        "field_regex",
        command={"commitTransaction": Regex(".*")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept Regex value",
    ),
    SessionCommandTestCase(
        "field_timestamp",
        command={"commitTransaction": Timestamp(0, 0)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept Timestamp value",
    ),
    SessionCommandTestCase(
        "field_code",
        command={"commitTransaction": Code("function(){}")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept Code value",
    ),
    SessionCommandTestCase(
        "field_minkey",
        command={"commitTransaction": MinKey()},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept MinKey value",
    ),
    SessionCommandTestCase(
        "field_maxkey",
        command={"commitTransaction": MaxKey()},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept MaxKey value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_TYPE_TESTS))
def test_commitTransaction_field_types(collection, test):
    """Test commitTransaction command field type acceptance."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
