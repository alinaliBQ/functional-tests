"""
Tests for setFeatureCompatibilityVersion confirm field.

Covers: confirm semantics (required for version change), confirm type coercion
matrix, confirm gating behavior.
"""

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import (
    assertExceptionType,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_fcv(collection) -> str:
    """Read back the current FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        pytest.skip("Cannot read FCV via getParameter")
    return result["featureCompatibilityVersion"]["version"]


def _set_fcv(collection, version: str):
    """Set FCV to a specific version with confirm:true."""
    return execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": version, "confirm": True}
    )


# --- Confirm semantics ---


def test_setFeatureCompatibilityVersion_confirm_true_allows_change(collection):
    """Test confirm:true allows a version change to proceed."""
    current_fcv = _get_fcv(collection)
    target = "8.0" if current_fcv != "8.0" else pytest.skip("Need different target")
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": True}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="confirm:true should allow change")
    # Restore
    _set_fcv(collection, current_fcv)


def test_setFeatureCompatibilityVersion_confirm_omitted_fails(collection):
    """Test confirm omitted on a version change fails."""
    current_fcv = _get_fcv(collection)
    target = "8.0" if current_fcv != "8.0" else pytest.skip("Need different target")
    result = execute_admin_command(collection, {"setFeatureCompatibilityVersion": target})
    assertExceptionType(result, Exception, msg="Should fail when confirm is omitted")


def test_setFeatureCompatibilityVersion_confirm_false_fails(collection):
    """Test confirm:false on a version change fails."""
    current_fcv = _get_fcv(collection)
    target = "8.0" if current_fcv != "8.0" else pytest.skip("Need different target")
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": target, "confirm": False}
    )
    assertExceptionType(result, Exception, msg="Should fail when confirm is false")


def test_setFeatureCompatibilityVersion_confirm_omitted_returns_error_7369100(collection):
    """Test the confirm-gate failure returns error code 7369100."""
    current_fcv = _get_fcv(collection)
    target = "8.0" if current_fcv != "8.0" else pytest.skip("Need different target")
    result = execute_admin_command(collection, {"setFeatureCompatibilityVersion": target})
    assertResult(result, error_code=7369100, msg="Confirm-gate should return code 7369100")


# --- Confirm type coercion matrix (Rule 20) ---


@dataclass(frozen=True)
class ConfirmCoercionTest(BaseTestCase):
    """Test case for confirm field type coercion."""

    confirm_value: Any = None


CONFIRM_COERCION_SUCCESS_TESTS: list[ConfirmCoercionTest] = [
    ConfirmCoercionTest(
        "true", confirm_value=True, expected={"ok": 1.0}, msg="bool true should be accepted"
    ),
    ConfirmCoercionTest(
        "int_1", confirm_value=1, expected={"ok": 1.0}, msg="int 1 treated as true"
    ),
    ConfirmCoercionTest(
        "double_1_0", confirm_value=1.0, expected={"ok": 1.0}, msg="double 1.0 treated as true"
    ),
    ConfirmCoercionTest(
        "long_1", confirm_value=Int64(1), expected={"ok": 1.0}, msg="Int64(1) treated as true"
    ),
    ConfirmCoercionTest(
        "decimal128_1",
        confirm_value=Decimal128("1"),
        expected={"ok": 1.0},
        msg="Decimal128('1') treated as true",
    ),
    ConfirmCoercionTest(
        "nan", confirm_value=float("nan"), expected={"ok": 1.0}, msg="NaN treated as truthy"
    ),
    ConfirmCoercionTest(
        "infinity",
        confirm_value=float("inf"),
        expected={"ok": 1.0},
        msg="Infinity treated as truthy",
    ),
]

CONFIRM_COERCION_ERROR_TESTS: list[ConfirmCoercionTest] = [
    ConfirmCoercionTest("int_0", confirm_value=0, error_code=7369100, msg="int 0 treated as false"),
    ConfirmCoercionTest(
        "double_0_0", confirm_value=0.0, error_code=7369100, msg="double 0.0 treated as false"
    ),
    ConfirmCoercionTest(
        "long_0", confirm_value=Int64(0), error_code=7369100, msg="Int64(0) treated as false"
    ),
    ConfirmCoercionTest(
        "decimal128_0",
        confirm_value=Decimal128("0"),
        error_code=7369100,
        msg="Decimal128('0') treated as false",
    ),
    ConfirmCoercionTest(
        "null", confirm_value=None, error_code=7369100, msg="null treated as false"
    ),
    ConfirmCoercionTest(
        "negative_zero", confirm_value=-0.0, error_code=7369100, msg="-0.0 treated as false"
    ),
    ConfirmCoercionTest(
        "string",
        confirm_value="true",
        error_code=TYPE_MISMATCH_ERROR,
        msg="string rejected as type mismatch",
    ),
    ConfirmCoercionTest(
        "object",
        confirm_value={},
        error_code=TYPE_MISMATCH_ERROR,
        msg="object rejected as type mismatch",
    ),
    ConfirmCoercionTest(
        "array",
        confirm_value=[],
        error_code=TYPE_MISMATCH_ERROR,
        msg="array rejected as type mismatch",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONFIRM_COERCION_SUCCESS_TESTS))
def test_setFeatureCompatibilityVersion_confirm_coercion_truthy(collection, test):
    """Test setFeatureCompatibilityVersion confirm truthy coercion succeeds."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_fcv, "confirm": test.confirm_value},
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(CONFIRM_COERCION_ERROR_TESTS))
def test_setFeatureCompatibilityVersion_confirm_coercion_falsy(collection, test):
    """Test setFeatureCompatibilityVersion confirm falsy coercion fails."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_fcv, "confirm": test.confirm_value},
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)
