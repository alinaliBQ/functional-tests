"""Tests for commitTransaction writeConcern.wtimeout sub-field validation.

Validates type and value acceptance for the writeConcern.wtimeout sub-field.
wtimeout accepts numeric types broadly. Most values produce NoSuchTransaction
(125). Int64 max value produces FailedToParse (9) due to overflow.
"""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_command_test_case import (  # noqa: E501
    SessionCommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    NO_SUCH_TRANSACTION_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [wtimeout Accepted Values]: wtimeout accepts numeric types broadly.
WTIMEOUT_ACCEPTANCE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "wtimeout_int32_positive",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": 1000}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:1000",
    ),
    SessionCommandTestCase(
        "wtimeout_int32_zero",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:0 (no timeout)",
    ),
    SessionCommandTestCase(
        "wtimeout_int64",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": Int64(1000)}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:Int64(1000)",
    ),
    SessionCommandTestCase(
        "wtimeout_double_whole",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": 1000.0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:1000.0",
    ),
    SessionCommandTestCase(
        "wtimeout_negative",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": -1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:-1",
    ),
    SessionCommandTestCase(
        "wtimeout_string",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": "1000"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:'1000'",
    ),
    SessionCommandTestCase(
        "wtimeout_bool",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:true",
    ),
    SessionCommandTestCase(
        "wtimeout_null",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": None}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:null",
    ),
    SessionCommandTestCase(
        "wtimeout_object",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": {}}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:{}",
    ),
    SessionCommandTestCase(
        "wtimeout_array",
        command={"commitTransaction": 1, "writeConcern": {"wtimeout": []}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.wtimeout:[]",
    ),
]

# Property [wtimeout Overflow]: Int64 max value overflows and produces FailedToParse.
WTIMEOUT_OVERFLOW_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "wtimeout_int64_max",
        command={
            "commitTransaction": 1,
            "writeConcern": {"wtimeout": Int64(9_223_372_036_854_775_807)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.wtimeout:Int64 max with FailedToParse",
    ),
]

WTIMEOUT_TESTS: list[SessionCommandTestCase] = WTIMEOUT_ACCEPTANCE_TESTS + WTIMEOUT_OVERFLOW_TESTS


@pytest.mark.parametrize("test", pytest_params(WTIMEOUT_TESTS))
def test_commitTransaction_writeconcern_wtimeout(collection, test):
    """Test commitTransaction writeConcern.wtimeout sub-field validation."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
