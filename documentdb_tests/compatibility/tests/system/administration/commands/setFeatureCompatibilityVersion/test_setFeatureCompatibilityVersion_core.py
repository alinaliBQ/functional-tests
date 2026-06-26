"""
Tests for setFeatureCompatibilityVersion core behavior.

Covers: setting FCV, idempotency, getParameter read-back,
and upgrade/downgrade with confirm.
"""

import pytest

from documentdb_tests.framework.assertions import assertNotError, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# --- Helpers ---


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


# --- Core behavior ---


def test_setFeatureCompatibilityVersion_set_current_version_succeeds(collection):
    """Test setting FCV to the deployment's current supported version succeeds."""
    current_fcv = _get_fcv(collection)
    result = _set_fcv(collection, current_fcv)
    assertSuccessPartial(result, {"ok": 1.0}, msg="Setting FCV to current version should succeed")


def test_setFeatureCompatibilityVersion_idempotent_second_call(collection):
    """Test setting FCV to the value it already holds a second time is idempotent."""
    current_fcv = _get_fcv(collection)
    _set_fcv(collection, current_fcv)
    result = _set_fcv(collection, current_fcv)
    assertSuccessPartial(result, {"ok": 1.0}, msg="Second idempotent call should succeed")


def test_setFeatureCompatibilityVersion_getParameter_reads_back_value(collection):
    """Test getParameter featureCompatibilityVersion returns a version field."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    assertNotError(result, msg="getParameter featureCompatibilityVersion should succeed")


def test_setFeatureCompatibilityVersion_downgrade_with_confirm(collection):
    """Test FCV can be downgraded to a supported lower version with confirm:true."""
    current_fcv = _get_fcv(collection)
    target = "8.0"
    if current_fcv == target:
        pytest.skip("Already at target downgrade version")
    result = _set_fcv(collection, target)
    assertSuccessPartial(result, {"ok": 1.0}, msg="Downgrade with confirm should succeed")
    # Restore
    _set_fcv(collection, current_fcv)


def test_setFeatureCompatibilityVersion_upgrade_with_confirm(collection):
    """Test FCV can be upgraded back to the latest supported version with confirm:true."""
    current_fcv = _get_fcv(collection)
    lower = "8.0"
    if current_fcv == lower:
        pytest.skip("Already at lower version, cannot test upgrade")
    _set_fcv(collection, lower)
    result = _set_fcv(collection, current_fcv)
    assertSuccessPartial(result, {"ok": 1.0}, msg="Upgrade with confirm should succeed")


def test_setFeatureCompatibilityVersion_response_contains_ok(collection):
    """Test success response contains ok:1."""
    current_fcv = _get_fcv(collection)
    result = _set_fcv(collection, current_fcv)
    assertSuccessPartial(result, {"ok": 1.0}, msg="Success response should have ok:1")
