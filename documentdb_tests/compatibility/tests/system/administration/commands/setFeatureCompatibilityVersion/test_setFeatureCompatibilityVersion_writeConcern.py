"""
Tests for setFeatureCompatibilityVersion writeConcern field validation.

Covers: writeConcern type validation, null-as-omitted, empty doc, wtimeout coercion.
"""

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
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


# --- writeConcern type validation ---


@dataclass(frozen=True)
class WriteConcernTypeTest(BaseTestCase):
    """Test case for writeConcern type validation."""

    wc_value: Any = None


WC_INVALID_TYPE_TESTS: list[WriteConcernTypeTest] = [
    WriteConcernTypeTest(
        "string",
        wc_value="majority",
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string writeConcern",
    ),
    WriteConcernTypeTest(
        "int",
        wc_value=1,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject int writeConcern",
    ),
    WriteConcernTypeTest(
        "long",
        wc_value=Int64(1),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject long writeConcern",
    ),
    WriteConcernTypeTest(
        "double",
        wc_value=1.0,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject double writeConcern",
    ),
    WriteConcernTypeTest(
        "decimal128",
        wc_value=Decimal128("1"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject decimal128 writeConcern",
    ),
    WriteConcernTypeTest(
        "bool",
        wc_value=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject bool writeConcern",
    ),
    WriteConcernTypeTest(
        "array",
        wc_value=[{"w": 1}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array writeConcern",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WC_INVALID_TYPE_TESTS))
def test_setFeatureCompatibilityVersion_writeConcern_invalid_type(collection, test):
    """Test setFeatureCompatibilityVersion rejects non-document writeConcern."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": test.wc_value,
        },
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)


# --- writeConcern accepted values ---


def test_setFeatureCompatibilityVersion_writeConcern_null_treated_as_omitted(collection):
    """Test writeConcern=null is treated as omitted (command succeeds)."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": None,
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="writeConcern=null should be treated as omitted")


def test_setFeatureCompatibilityVersion_writeConcern_empty_doc_accepted(collection):
    """Test writeConcern={} (empty doc) is accepted with defaults applied."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {},
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="writeConcern={} should be accepted")


def test_setFeatureCompatibilityVersion_writeConcern_with_wtimeout(collection):
    """Test writeConcern with wtimeout numeric value is accepted."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_fcv,
            "confirm": True,
            "writeConcern": {"wtimeout": 60000},
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="writeConcern with wtimeout should be accepted")


def test_setFeatureCompatibilityVersion_omit_writeConcern_succeeds(collection):
    """Test omitting writeConcern uses defaults and succeeds."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_fcv, "confirm": True},
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Omitting writeConcern should succeed")
