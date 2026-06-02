"""Tests for commitTransaction comment parameter type acceptance.

Validates that the comment parameter accepts any BSON type. All types produce
NoSuchTransaction (125) because no transaction is active, confirming the
comment field itself is not type-checked.
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


# Property [comment Type Acceptance]: comment accepts any BSON type.
COMMENT_TYPE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "comment_string",
        command={"commitTransaction": 1, "comment": "test comment"},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:string",
    ),
    SessionCommandTestCase(
        "comment_string_empty",
        command={"commitTransaction": 1, "comment": ""},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:empty string",
    ),
    SessionCommandTestCase(
        "comment_int32",
        command={"commitTransaction": 1, "comment": 42},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:int32",
    ),
    SessionCommandTestCase(
        "comment_int64",
        command={"commitTransaction": 1, "comment": Int64(42)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:Int64",
    ),
    SessionCommandTestCase(
        "comment_double",
        command={"commitTransaction": 1, "comment": 3.14},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:double",
    ),
    SessionCommandTestCase(
        "comment_decimal128",
        command={"commitTransaction": 1, "comment": Decimal128("1.5")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:Decimal128",
    ),
    SessionCommandTestCase(
        "comment_bool_true",
        command={"commitTransaction": 1, "comment": True},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:true",
    ),
    SessionCommandTestCase(
        "comment_bool_false",
        command={"commitTransaction": 1, "comment": False},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:false",
    ),
    SessionCommandTestCase(
        "comment_null",
        command={"commitTransaction": 1, "comment": None},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:null",
    ),
    SessionCommandTestCase(
        "comment_object",
        command={"commitTransaction": 1, "comment": {"key": "value"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:object",
    ),
    SessionCommandTestCase(
        "comment_object_empty",
        command={"commitTransaction": 1, "comment": {}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:empty object",
    ),
    SessionCommandTestCase(
        "comment_array",
        command={"commitTransaction": 1, "comment": [1, 2, 3]},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:array",
    ),
    SessionCommandTestCase(
        "comment_array_empty",
        command={"commitTransaction": 1, "comment": []},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:empty array",
    ),
    SessionCommandTestCase(
        "comment_objectid",
        command={"commitTransaction": 1, "comment": ObjectId()},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:ObjectId",
    ),
    SessionCommandTestCase(
        "comment_datetime",
        command={"commitTransaction": 1, "comment": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:datetime",
    ),
    SessionCommandTestCase(
        "comment_binary",
        command={"commitTransaction": 1, "comment": Binary(b"\x00")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:Binary",
    ),
    SessionCommandTestCase(
        "comment_regex",
        command={"commitTransaction": 1, "comment": Regex(".*")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:Regex",
    ),
    SessionCommandTestCase(
        "comment_timestamp",
        command={"commitTransaction": 1, "comment": Timestamp(0, 0)},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:Timestamp",
    ),
    SessionCommandTestCase(
        "comment_minkey",
        command={"commitTransaction": 1, "comment": MinKey()},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:MinKey",
    ),
    SessionCommandTestCase(
        "comment_maxkey",
        command={"commitTransaction": 1, "comment": MaxKey()},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:MaxKey",
    ),
    SessionCommandTestCase(
        "comment_code",
        command={"commitTransaction": 1, "comment": Code("function(){}")},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept comment:Code",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMENT_TYPE_TESTS))
def test_commitTransaction_comment(collection, test):
    """Test commitTransaction comment parameter type acceptance."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
