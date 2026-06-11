"""Tests for abortTransaction command core error cases.

Validates fundamental command error behavior including parameter acceptance,
parameter interactions, and the admin database requirement.
"""

from __future__ import annotations

import pytest
from bson import Binary, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_FAILED_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin

# Property [Parameter Acceptance]: all valid parameters combined are syntactically accepted.
CORE_PARAMETER_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "all_valid_params",
        command={
            "abortTransaction": 1,
            "autocommit": False,
            "txnNumber": Int64(1),
            "writeConcern": {"w": "majority", "j": True, "wtimeout": 10_000},
            "comment": "full abort",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="abortTransaction with all valid params should not produce a parsing error",
    ),
]

# Property [Parameter Interactions]: combinations of valid parameters behave correctly.
CORE_PARAMETER_INTERACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "interaction_autocommit_only",
        command={"abortTransaction": 1, "autocommit": False},
        error_code=INVALID_OPTIONS_ERROR,
        msg="abortTransaction with autocommit:false only should fail with InvalidOptions",
    ),
    CommandTestCase(
        "interaction_txn_number_only",
        command={"abortTransaction": 1, "txnNumber": Int64(1)},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="abortTransaction with txnNumber only should fail with IllegalOperation",
    ),
    CommandTestCase(
        "interaction_autocommit_txn_number",
        command={"abortTransaction": 1, "autocommit": False, "txnNumber": Int64(1)},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="abortTransaction with autocommit + txnNumber should fail with IllegalOperation",
    ),
    CommandTestCase(
        "interaction_lsid",
        command={"abortTransaction": 1, "lsid": {"id": Binary(b"\x00" * 16, 4)}},
        error_code=COMMAND_FAILED_ERROR,
        msg="abortTransaction with explicit lsid should accept the field",
    ),
]

CORE_ERROR_TESTS: list[CommandTestCase] = (
    CORE_PARAMETER_ACCEPTANCE_TESTS + CORE_PARAMETER_INTERACTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(CORE_ERROR_TESTS))
def test_abortTransaction_core_error(collection, test):
    """Test abortTransaction core error cases."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [Admin Database Requirement]: abortTransaction must run against the admin database.
ADMIN_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "non_admin_database",
        command={"abortTransaction": 1},
        error_code=UNAUTHORIZED_ERROR,
        msg="abortTransaction on a non-admin database should fail with Unauthorized",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ADMIN_DB_TESTS))
def test_abortTransaction_admin_db_required(collection, test):
    """Test abortTransaction requires admin database."""
    result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
