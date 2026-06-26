"""
Tests for setFeatureCompatibilityVersion error handling.

Covers: admin-database-only enforcement, unknown/extra fields, response structure,
argument handling combinations, setParameter rejection.
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertExceptionType,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import (
    TYPE_MISMATCH_ERROR,
    UNAUTHORIZED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_fcv(collection) -> str:
    """Read back the current FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        pytest.skip("Cannot read FCV via getParameter")
    return result["featureCompatibilityVersion"]["version"]


# --- Admin-database-only enforcement ---


def test_setFeatureCompatibilityVersion_on_admin_db_accepted(collection):
    """Test command on the admin database is accepted."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Command on admin db should succeed")


def test_setFeatureCompatibilityVersion_on_user_db_fails(collection):
    """Test command on a user database fails with UNAUTHORIZED_ERROR."""
    current_fcv = _get_fcv(collection)
    result = execute_command(
        collection,
        {"setFeatureCompatibilityVersion": current_fcv, "confirm": True},
    )
    assertResult(
        result,
        error_code=UNAUTHORIZED_ERROR,
        msg="Command on user db should fail with UNAUTHORIZED_ERROR",
    )


# --- Unknown / extra fields ---


def test_setFeatureCompatibilityVersion_unrecognized_field_fails(collection):
    """Test an unrecognized top-level field fails with UNRECOGNIZED_COMMAND_FIELD_ERROR."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "unknownField": 1,
        },
    )
    assertResult(
        result,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown field should return error 40415",
    )


def test_setFeatureCompatibilityVersion_misspelled_confirm_treated_as_unknown(collection):
    """Test a misspelled confirm field is treated as unknown field."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confrim": True,
        },
    )
    assertResult(
        result,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Misspelled confirm should be treated as unknown field",
    )


# --- setParameter rejection ---


def test_setFeatureCompatibilityVersion_cannot_set_via_setParameter(collection):
    """Test the FCV cannot be set through the setParameter command."""
    result = execute_admin_command(
        collection,
        {"setParameter": 1, "featureCompatibilityVersion": "8.0"},
    )
    assertExceptionType(result, Exception, msg="setParameter should not allow setting FCV")


# --- Response structure ---


def test_setFeatureCompatibilityVersion_success_response_shape(collection):
    """Test success response matches documented shape with ok:1."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Response should have ok:1.0")


def test_setFeatureCompatibilityVersion_error_response_has_code(collection):
    """Test error response contains a numeric error code."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": "invalid_version", "confirm": True},
    )
    # MongoDB 8.2 uses error code 4926900 for invalid FCV version strings
    assertResult(result, error_code=4926900, msg="Invalid version should return FCV-specific error")


# --- Unknown field rejection fires at parse time ---


def test_setFeatureCompatibilityVersion_unknown_field_no_state_change(collection):
    """Test unknown-field rejection happens before any FCV state change."""
    # Send command with unknown field — should fail at parse time
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": "8.0",
            "confirm": True,
            "badField": True,
        },
    )
    assertResult(
        result,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown field should be rejected at parse time",
    )


# --- Argument independence ---


def test_setFeatureCompatibilityVersion_version_type_error_with_confirm_true(collection):
    """Test version-value type errors hold when confirm is true."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": 123, "confirm": True}
    )
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Int version should fail regardless of confirm value",
    )


def test_setFeatureCompatibilityVersion_version_type_error_without_confirm(collection):
    """Test version-value type errors hold when confirm is omitted."""
    result = execute_admin_command(collection, {"setFeatureCompatibilityVersion": 123})
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Int version should fail without confirm too",
    )
