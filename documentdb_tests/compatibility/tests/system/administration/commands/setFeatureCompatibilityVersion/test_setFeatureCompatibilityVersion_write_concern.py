"""Tests for setFeatureCompatibilityVersion writeConcern field validation.

Validates BSON-type acceptance and rejection for the writeConcern field:
- Object (including empty {}) is accepted.
- null is treated as omitted (accepted).
- String, int, long, double, decimal128, bool, and array are rejected with
  TYPE_MISMATCH_ERROR (14).

Also validates writeConcern.wtimeout coercion: MongoDB accepts whole-number
double, Int64, and Decimal128 values; fractional doubles; negative values; and
zero for wtimeout without rejecting them.

All tests target the current deployment FCV so no FCV state change occurs.
"""

from dataclasses import dataclass
from typing import Any, Optional

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import (
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
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


@dataclass(frozen=True)
class WriteConcernTestCase(BaseTestCase):
    """Test case for writeConcern field validation."""

    write_concern: Any = None
    error_code: Optional[int] = None


# Property [writeConcern Type Validation]: object and null are accepted; string,
# int, double, bool, and array are rejected with TYPE_MISMATCH_ERROR (14).
WRITE_CONCERN_TYPE_TESTS: list[WriteConcernTestCase] = [
    WriteConcernTestCase(
        "write_concern_object",
        write_concern={"w": 1},
        expected={"ok": 1.0},
        msg="writeConcern should accept an object value.",
    ),
    WriteConcernTestCase(
        "write_concern_empty_object",
        write_concern={},
        expected={"ok": 1.0},
        msg="writeConcern should accept an empty object (defaults applied).",
    ),
    WriteConcernTestCase(
        "write_concern_null",
        write_concern=None,
        expected={"ok": 1.0},
        msg="writeConcern=null should be treated as omitted (accepted).",
    ),
    WriteConcernTestCase(
        "write_concern_string",
        write_concern="majority",
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern should reject a string value with TYPE_MISMATCH_ERROR.",
    ),
    WriteConcernTestCase(
        "write_concern_int",
        write_concern=1,
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern should reject an int value with TYPE_MISMATCH_ERROR.",
    ),
    WriteConcernTestCase(
        "write_concern_double",
        write_concern=1.0,
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern should reject a double value with TYPE_MISMATCH_ERROR.",
    ),
    WriteConcernTestCase(
        "write_concern_bool",
        write_concern=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern should reject a bool value with TYPE_MISMATCH_ERROR.",
    ),
    WriteConcernTestCase(
        "write_concern_array",
        write_concern=[],
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern should reject an array value with TYPE_MISMATCH_ERROR.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_TYPE_TESTS))
def test_setFeatureCompatibilityVersion_write_concern_type(collection, test):
    """Test writeConcern field type acceptance and rejection."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_version,
            "confirm": True,
            "writeConcern": test.write_concern,
        },
    )
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [writeConcern.wtimeout coercion]: MongoDB accepts whole-number double,
# Int64, Decimal128, fractional double, negative, and zero values for wtimeout
# without rejecting them.


@dataclass(frozen=True)
class WtimeoutCoercionTestCase(BaseTestCase):
    """Test case for writeConcern.wtimeout coercion."""

    wtimeout_value: Any = None


WTIMEOUT_COERCION_TESTS: list[WtimeoutCoercionTestCase] = [
    WtimeoutCoercionTestCase(
        "wtimeout_int",
        wtimeout_value=60000,
        expected={"ok": 1.0},
        msg="writeConcern.wtimeout should accept an int value.",
    ),
    WtimeoutCoercionTestCase(
        "wtimeout_whole_double",
        wtimeout_value=5000.0,
        expected={"ok": 1.0},
        msg="writeConcern.wtimeout should accept a whole-number double.",
    ),
    WtimeoutCoercionTestCase(
        "wtimeout_int64",
        wtimeout_value=Int64(60000),
        expected={"ok": 1.0},
        msg="writeConcern.wtimeout should accept an Int64 value.",
    ),
    WtimeoutCoercionTestCase(
        "wtimeout_decimal128",
        wtimeout_value=Decimal128("60000"),
        expected={"ok": 1.0},
        msg="writeConcern.wtimeout should accept a Decimal128 whole-number value.",
    ),
    WtimeoutCoercionTestCase(
        "wtimeout_fractional_double",
        wtimeout_value=1.5,
        expected={"ok": 1.0},
        msg="writeConcern.wtimeout should accept a fractional double.",
    ),
    WtimeoutCoercionTestCase(
        "wtimeout_negative",
        wtimeout_value=-1,
        expected={"ok": 1.0},
        msg="writeConcern.wtimeout should accept a negative value.",
    ),
    WtimeoutCoercionTestCase(
        "wtimeout_zero",
        wtimeout_value=0,
        expected={"ok": 1.0},
        msg="writeConcern.wtimeout should accept zero.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WTIMEOUT_COERCION_TESTS))
def test_setFeatureCompatibilityVersion_write_concern_wtimeout_coercion(collection, test):
    """Test writeConcern.wtimeout accepts various numeric types without rejection."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_version,
            "confirm": True,
            "writeConcern": {"wtimeout": test.wtimeout_value},
        },
    )
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [writeConcern unknown sub-field]: an unrecognized field inside writeConcern
# is rejected with UNRECOGNIZED_COMMAND_FIELD_ERROR (40415).
def test_setFeatureCompatibilityVersion_write_concern_unknown_subfield(collection):
    """Test writeConcern rejects an unrecognized sub-field."""
    current_version = _get_current_version(collection)
    result = execute_admin_command(
        collection,
        {
            "setFeatureCompatibilityVersion": current_version,
            "confirm": True,
            "writeConcern": {"unknownSubField": 1},
        },
    )
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="writeConcern should reject an unrecognized sub-field.",
    )
