"""Tests for setFeatureCompatibilityVersion command core behavior.

Verifies idempotency, getParameter readback, success response shape,
setParameter rejection, and argument combinations (version + confirm +
writeConcern). All success-path tests use the current deployment FCV so
no FCV state change occurs.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import ILLEGAL_OPERATION_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_current_version(collection):
    """Return the current FCV version string from the running deployment."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    return result["featureCompatibilityVersion"]["version"]


# Property [Core Success]: setFeatureCompatibilityVersion with confirm:true and
# the current version succeeds and returns ok:1.
def test_setFeatureCompatibilityVersion_same_version_succeeds(collection):
    """Test setting FCV to the current version (no-op) returns ok:1."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_version, "confirm": True},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should return ok:1 when setting the current version.",
    )


# Property [Idempotency]: issuing the same successful command twice both return ok:1.
def test_setFeatureCompatibilityVersion_idempotent(collection):
    """Test calling setFeatureCompatibilityVersion twice with the same version both succeed."""
    current_version = _get_current_version(collection)
    execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_version, "confirm": True},
    )
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_version, "confirm": True},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should be idempotent when called twice.",
    )


# Property [getParameter readback]: getParameter reflects the version set by setFCV.
def test_setFeatureCompatibilityVersion_getParameter_readback(collection):
    """Test that getParameter reports the version that was just set."""
    current_version = _get_current_version(collection)
    execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_version, "confirm": True},
    )
    readback = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    read_version = readback["featureCompatibilityVersion"]["version"]
    if read_version != current_version:
        raise AssertionError(
            f"Expected getParameter to return version '{current_version}', got '{read_version}'"
        )


# Property [Response Shape]: success response contains only the ok field (plus
# replica-set gossip fields which are topology-dependent and not part of the spec).
_GOSSIP_FIELDS = frozenset({"$clusterTime", "operationTime", "electionId", "opTime"})


def test_setFeatureCompatibilityVersion_success_response_has_only_ok(collection):
    """Test that the success response contains no unexpected payload fields."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_version, "confirm": True},
    )
    if isinstance(result, Exception):
        raise AssertionError(f"Expected success but got error: {result}")
    unexpected = {k for k in result.keys() if k not in {"ok"} | _GOSSIP_FIELDS}
    if unexpected:
        raise AssertionError(
            f"Unexpected fields in setFeatureCompatibilityVersion success response: {unexpected}"
        )


# Property [setParameter rejection]: featureCompatibilityVersion cannot be set
# via the setParameter command (ILLEGAL_OPERATION_ERROR 20).
def test_setFeatureCompatibilityVersion_setParameter_rejected(collection):
    """Test that featureCompatibilityVersion cannot be set via setParameter."""
    result = execute_admin_command(
        collection, {"setParameter": 1, "featureCompatibilityVersion": "8.0"}
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg="featureCompatibilityVersion must not be settable via setParameter.",
    )


# Property [Combinations]: version + confirm:true + writeConcern document succeeds.
def test_setFeatureCompatibilityVersion_with_write_concern(collection):
    """Test setFeatureCompatibilityVersion accepts a writeConcern document."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_version,
            "confirm": True,
            "writeConcern": {"w": 1},
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept a writeConcern document.",
    )


# Property [Combinations]: version + confirm:true + writeConcern.wtimeout succeeds.
def test_setFeatureCompatibilityVersion_with_write_concern_wtimeout(collection):
    """Test setFeatureCompatibilityVersion accepts writeConcern with wtimeout."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_version,
            "confirm": True,
            "writeConcern": {"wtimeout": 60000},
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept writeConcern.wtimeout.",
    )
