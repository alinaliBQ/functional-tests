"""Tests for commitTransaction writeConcern.w sub-field validation.

Validates type and value acceptance for the writeConcern.w sub-field. w accepts
int and string values. Valid values pass through to NoSuchTransaction. Invalid
values produce FailedToParse or BadValue.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_command_test_case import (  # noqa: E501
    SessionCommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    NO_SUCH_TRANSACTION_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [w Accepted Values]: w accepts int and string "majority" values.
W_ACCEPTANCE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "w_int32_one",
        command={"commitTransaction": 1, "writeConcern": {"w": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:1",
    ),
    SessionCommandTestCase(
        "w_int32_zero",
        command={"commitTransaction": 1, "writeConcern": {"w": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:0 (unacknowledged)",
    ),
    SessionCommandTestCase(
        "w_majority",
        command={"commitTransaction": 1, "writeConcern": {"w": "majority"}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:'majority'",
    ),
    SessionCommandTestCase(
        "w_int64",
        command={"commitTransaction": 1, "writeConcern": {"w": Int64(1)}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:Int64(1)",
    ),
    SessionCommandTestCase(
        "w_double_whole",
        command={"commitTransaction": 1, "writeConcern": {"w": 1.0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:1.0",
    ),
    SessionCommandTestCase(
        "w_double_fractional",
        command={"commitTransaction": 1, "writeConcern": {"w": 1.5}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:1.5",
    ),
    SessionCommandTestCase(
        "w_decimal128",
        command={"commitTransaction": 1, "writeConcern": {"w": Decimal128("1")}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.w:Decimal128('1')",
    ),
]

# Property [w Invalid Values]: invalid w values are rejected with BadValue or FailedToParse.
W_INVALID_VALUE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "w_custom_tag",
        command={"commitTransaction": 1, "writeConcern": {"w": "myTag"}},
        error_code=BAD_VALUE_ERROR,
        msg="commitTransaction should reject writeConcern.w:'myTag' with BadValue",
    ),
    SessionCommandTestCase(
        "w_empty_string",
        command={"commitTransaction": 1, "writeConcern": {"w": ""}},
        error_code=BAD_VALUE_ERROR,
        msg="commitTransaction should reject writeConcern.w:'' with BadValue",
    ),
    SessionCommandTestCase(
        "w_null",
        command={"commitTransaction": 1, "writeConcern": {"w": None}},
        error_code=BAD_VALUE_ERROR,
        msg="commitTransaction should reject writeConcern.w:null with BadValue",
    ),
    SessionCommandTestCase(
        "w_negative_int",
        command={"commitTransaction": 1, "writeConcern": {"w": -1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:-1 with FailedToParse",
    ),
    SessionCommandTestCase(
        "w_int32_max",
        command={"commitTransaction": 1, "writeConcern": {"w": 2_147_483_647}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:INT32_MAX with FailedToParse",
    ),
    SessionCommandTestCase(
        "w_bool_false",
        command={"commitTransaction": 1, "writeConcern": {"w": False}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:false with FailedToParse",
    ),
    SessionCommandTestCase(
        "w_bool_true",
        command={"commitTransaction": 1, "writeConcern": {"w": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:true with FailedToParse",
    ),
    SessionCommandTestCase(
        "w_object",
        command={"commitTransaction": 1, "writeConcern": {"w": {}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:{} with FailedToParse",
    ),
    SessionCommandTestCase(
        "w_array",
        command={"commitTransaction": 1, "writeConcern": {"w": []}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="commitTransaction should reject writeConcern.w:[] with FailedToParse",
    ),
]

W_TESTS: list[SessionCommandTestCase] = W_ACCEPTANCE_TESTS + W_INVALID_VALUE_TESTS


@pytest.mark.parametrize("test", pytest_params(W_TESTS))
def test_commitTransaction_writeconcern_w(collection, test):
    """Test commitTransaction writeConcern.w sub-field validation."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
