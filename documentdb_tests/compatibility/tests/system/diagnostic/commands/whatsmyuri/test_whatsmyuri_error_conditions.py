"""Tests for whatsmyuri command error conditions.

Validates that invalid usages of whatsmyuri produce appropriate errors.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import COMMAND_NOT_FOUND_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


# Property [Case Sensitivity]: whatsmyuri is case-sensitive and rejects mismatched casing.
CASE_SENSITIVITY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="case_sensitive",
        command={"WhatsMyUri": 1},
        use_admin=True,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="whatsmyuri should reject case-mismatched command name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CASE_SENSITIVITY_TESTS))
def test_whatsmyuri_error_conditions(collection, test):
    """Test whatsmyuri error conditions."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [Extra Fields Ignored]: whatsmyuri ignores unrecognized fields.
EXTRA_FIELD_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="extra_field_ignored",
        command={"whatsmyuri": 1, "unknownField": 1},
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should succeed even with unrecognized fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EXTRA_FIELD_TESTS))
def test_whatsmyuri_extra_fields(collection, test):
    """Test whatsmyuri with extra fields."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
