"""Tests for whatsmyuri command error conditions.

Validates that invalid usages of whatsmyuri produce appropriate errors.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_FOUND_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="case_sensitive",
        command={"WhatsMyUri": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="Case-mismatched command name should fail",
    ),
    DiagnosticTestCase(
        id="unrecognized_field",
        command={"whatsmyuri": 1, "unknownField": 1},
        use_admin=True,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Should reject unrecognized fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_whatsmyuri_error_conditions(collection, test):
    """Verify whatsmyuri rejects invalid usages with appropriate error codes."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
