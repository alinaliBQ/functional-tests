"""Tests for commitTransaction writeConcern edge cases.

Validates structural edge cases for the writeConcern parameter including
combined sub-fields, unknown sub-fields, legacy fsync, and conflicting options.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_command_test_case import (  # noqa: E501
    SessionCommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    NO_SUCH_TRANSACTION_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [writeConcern Combined Sub-Fields]: combined w + j + wtimeout is accepted.
WRITECONCERN_COMBINED_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "wc_combined_w_j_wtimeout",
        command={
            "commitTransaction": 1,
            "writeConcern": {"w": "majority", "j": True, "wtimeout": 10_000},
        },
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept combined w + j + wtimeout",
    ),
    SessionCommandTestCase(
        "wc_w0_j_true",
        command={"commitTransaction": 1, "writeConcern": {"w": 0, "j": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept conflicting w:0 with j:true",
    ),
]

# Property [writeConcern Unknown Sub-Field]: unknown writeConcern sub-fields are rejected.
WRITECONCERN_UNKNOWN_SUBFIELD_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "wc_unknown_subfield",
        command={"commitTransaction": 1, "writeConcern": {"w": 1, "unknownOption": True}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="commitTransaction should reject unknown writeConcern sub-field",
    ),
]

# Property [writeConcern Legacy fsync]: the legacy fsync sub-field is accepted.
WRITECONCERN_FSYNC_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "wc_fsync_true",
        command={"commitTransaction": 1, "writeConcern": {"fsync": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept legacy writeConcern.fsync:true",
    ),
]

WRITECONCERN_EDGE_TESTS: list[SessionCommandTestCase] = (
    WRITECONCERN_COMBINED_TESTS + WRITECONCERN_UNKNOWN_SUBFIELD_TESTS + WRITECONCERN_FSYNC_TESTS
)


@pytest.mark.parametrize("test", pytest_params(WRITECONCERN_EDGE_TESTS))
def test_commitTransaction_writeconcern_edge_cases(collection, test):
    """Test commitTransaction writeConcern edge cases."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
