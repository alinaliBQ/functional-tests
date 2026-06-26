"""Tests for setFeatureCompatibilityVersion version field type and value validation.

Validates that non-string BSON types for the command field are rejected with
TYPE_MISMATCH_ERROR (14), that null is treated as a missing field
(MISSING_FIELD_ERROR 40414), and that malformed or unsupported version strings
are rejected with FCV_INVALID_VERSION_ERROR (4926900).

These tests all fail at parse time and do not change FCV state.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    FCV_INVALID_VERSION_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


@dataclass(frozen=True)
class FcvVersionTypeTestCase(BaseTestCase):
    """Test case for version field type validation."""

    version_value: Any = None


# Property [Type Rejection]: non-string BSON types for the version field are rejected.
# null is treated as a missing required field (MISSING_FIELD_ERROR 40414);
# all other non-string types produce TYPE_MISMATCH_ERROR (14).
VERSION_TYPE_TESTS: list[FcvVersionTypeTestCase] = [
    FcvVersionTypeTestCase(
        "version_int",
        version_value=1,
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject int version with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_int64",
        version_value=Int64(8),
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject Int64 version with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_double",
        version_value=1.5,
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject double version with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_decimal128",
        version_value=Decimal128("8"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="version=Decimal128 should fail with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_bool_true",
        version_value=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject bool version with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_null",
        version_value=None,
        error_code=MISSING_FIELD_ERROR,
        msg="setFeatureCompatibilityVersion should treat null version as a missing required field.",
    ),
    FcvVersionTypeTestCase(
        "version_object",
        version_value={"v": "8.0"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject object version with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_array",
        version_value=["8.0"],
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject array version with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_date",
        version_value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject date version with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_objectId",
        version_value=ObjectId(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="version=ObjectId should fail with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_binData",
        version_value=Binary(b"8.0"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="version=binData should fail with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_regex",
        version_value=Regex("8.0"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject regex version with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_timestamp",
        version_value=Timestamp(0, 0),
        error_code=TYPE_MISMATCH_ERROR,
        msg="version=Timestamp should fail with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_minKey",
        version_value=MinKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject MinKey version with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_maxKey",
        version_value=MaxKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject MaxKey version with TYPE_MISMATCH_ERROR.",
    ),
    FcvVersionTypeTestCase(
        "version_code",
        version_value=Code("function(){}"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject Code version with TYPE_MISMATCH_ERROR.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VERSION_TYPE_TESTS))
def test_setFeatureCompatibilityVersion_version_type_rejected(collection, test):
    """Test setFeatureCompatibilityVersion rejects non-string types for the version field."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": test.version_value}
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [Value Validation]: malformed and out-of-range version strings are rejected
# with FCV_INVALID_VERSION_ERROR (4926900).
VERSION_VALUE_TESTS: list[FcvVersionTypeTestCase] = [
    FcvVersionTypeTestCase(
        "version_major_only",
        version_value="8",
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject a major-only version string.",
    ),
    FcvVersionTypeTestCase(
        "version_full_semver",
        version_value="8.0.0",
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject a full semver version string.",
    ),
    FcvVersionTypeTestCase(
        "version_leading_whitespace",
        version_value=" 8.0",
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="Version string with leading whitespace should be rejected.",
    ),
    FcvVersionTypeTestCase(
        "version_trailing_whitespace",
        version_value="8.0 ",
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="Version string with trailing whitespace should be rejected.",
    ),
    FcvVersionTypeTestCase(
        "version_empty_string",
        version_value="",
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject an empty version string.",
    ),
    FcvVersionTypeTestCase(
        "version_non_numeric",
        version_value="abc",
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject a non-numeric version string.",
    ),
    FcvVersionTypeTestCase(
        "version_zero",
        version_value="0.0",
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject '0.0' (below supported floor).",
    ),
    FcvVersionTypeTestCase(
        "version_far_future",
        version_value="99.0",
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject '99.0' (above supported ceiling).",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VERSION_VALUE_TESTS))
def test_setFeatureCompatibilityVersion_version_value_rejected(collection, test):
    """Test setFeatureCompatibilityVersion rejects malformed and out-of-range version strings."""
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": test.version_value, "confirm": True}
    )
    assertFailureCode(result, test.error_code, msg=test.msg)
