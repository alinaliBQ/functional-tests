"""Tests for setFeatureCompatibilityVersion confirm field semantics and type coercion.

The confirm field (added in MongoDB 7.0) gates any version-changing call.
Semantics tests verify confirm:true proceeds, confirm:false and confirm omitted
both fail with FCV_CONFIRM_REQUIRED_ERROR (7369100).

Coercion matrix tests verify how MongoDB coerces non-boolean types:
- Numeric non-zero values (int, double, Int64, Decimal128, NaN, Inf) → treated as true
- Numeric zero values (0, 0.0, -0.0) and null → treated as false (7369100)
- String, object, array → TYPE_MISMATCH_ERROR (14)

All coercion tests target the current deployment FCV (no-op set) so no FCV
state change occurs regardless of the coercion outcome.
"""

from dataclasses import dataclass
from typing import Any, Optional

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import FCV_CONFIRM_REQUIRED_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_current_version(collection):
    """Return the current FCV version string from the running deployment."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    return result["featureCompatibilityVersion"]["version"]


# Property [confirm Semantics]: confirm:true allows the command to proceed;
# confirm:false and confirm omitted both return FCV_CONFIRM_REQUIRED_ERROR (7369100).
def test_setFeatureCompatibilityVersion_confirm_true_proceeds(collection):
    """Test setFeatureCompatibilityVersion with confirm:true returns ok:1."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_version, "confirm": True},
    )
    assertResult(
        result,
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should proceed when confirm is True.",
        raw_res=True,
    )


def test_setFeatureCompatibilityVersion_confirm_false_rejected(collection):
    """Test setFeatureCompatibilityVersion confirm:false fails with FCV_CONFIRM_REQUIRED_ERROR."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_version, "confirm": False},
    )
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should reject confirm:False.",
    )


def test_setFeatureCompatibilityVersion_confirm_omitted_rejected(collection):
    """Test setFeatureCompatibilityVersion without confirm fails with FCV_CONFIRM_REQUIRED_ERROR."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_version},
    )
    assertFailureCode(
        result,
        FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should require the confirm field.",
    )


# Property [confirm Coercion]: MongoDB coerces non-boolean BSON types for the
# confirm field. Numeric non-zero values are treated as true; zero values and
# null are treated as false; string/object/array cause TYPE_MISMATCH_ERROR (14).


@dataclass(frozen=True)
class ConfirmCoercionTestCase(BaseTestCase):
    """Test case for confirm field type coercion."""

    confirm_value: Any = None
    error_code: Optional[int] = None


CONFIRM_COERCION_TESTS: list[ConfirmCoercionTestCase] = [
    # Numeric non-zero → treated as true (ok:1)
    ConfirmCoercionTestCase(
        "confirm_int_1",
        confirm_value=1,
        expected={"ok": 1.0},
        msg="confirm=1 (int32) should be coerced to true.",
    ),
    ConfirmCoercionTestCase(
        "confirm_double_1",
        confirm_value=1.0,
        expected={"ok": 1.0},
        msg="confirm=1.0 (double) should be coerced to true.",
    ),
    ConfirmCoercionTestCase(
        "confirm_int64_1",
        confirm_value=Int64(1),
        expected={"ok": 1.0},
        msg="confirm=Int64(1) should be coerced to true.",
    ),
    ConfirmCoercionTestCase(
        "confirm_decimal128_1",
        confirm_value=Decimal128("1"),
        expected={"ok": 1.0},
        msg="confirm=Decimal128('1') should be coerced to true.",
    ),
    ConfirmCoercionTestCase(
        "confirm_nan",
        confirm_value=float("nan"),
        expected={"ok": 1.0},
        msg="confirm=NaN should be treated as truthy (non-zero).",
    ),
    ConfirmCoercionTestCase(
        "confirm_infinity",
        confirm_value=float("inf"),
        expected={"ok": 1.0},
        msg="confirm=Infinity should be treated as truthy (non-zero).",
    ),
    # Numeric zero / null → treated as false (FCV_CONFIRM_REQUIRED_ERROR)
    ConfirmCoercionTestCase(
        "confirm_int_0",
        confirm_value=0,
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="confirm=0 (int32) should be coerced to false.",
    ),
    ConfirmCoercionTestCase(
        "confirm_double_0",
        confirm_value=0.0,
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="confirm=0.0 (double) should be coerced to false.",
    ),
    ConfirmCoercionTestCase(
        "confirm_negative_zero",
        confirm_value=-0.0,
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="confirm=-0.0 should be treated as zero (falsy).",
    ),
    ConfirmCoercionTestCase(
        "confirm_null",
        confirm_value=None,
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="confirm=null should be treated as not-confirmed.",
    ),
    # Non-numeric types → TYPE_MISMATCH_ERROR (14)
    ConfirmCoercionTestCase(
        "confirm_string",
        confirm_value="true",
        error_code=TYPE_MISMATCH_ERROR,
        msg="confirm='true' (string) should fail with TYPE_MISMATCH_ERROR.",
    ),
    ConfirmCoercionTestCase(
        "confirm_object",
        confirm_value={},
        error_code=TYPE_MISMATCH_ERROR,
        msg="confirm={} (object) should fail with TYPE_MISMATCH_ERROR.",
    ),
    ConfirmCoercionTestCase(
        "confirm_array",
        confirm_value=[],
        error_code=TYPE_MISMATCH_ERROR,
        msg="confirm=[] (array) should fail with TYPE_MISMATCH_ERROR.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONFIRM_COERCION_TESTS))
def test_setFeatureCompatibilityVersion_confirm_coercion(collection, test):
    """Test how MongoDB coerces non-boolean types for the confirm field."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_version, "confirm": test.confirm_value},
    )
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
