"""
Tests for setFeatureCompatibilityVersion version value type validation.

Covers: all BSON types passed as the version value, expecting TYPE_MISMATCH_ERROR
for non-string types.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import MISSING_FIELD_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


@dataclass(frozen=True)
class VersionTypeTest(BaseTestCase):
    """Test case for version value type validation."""

    version_value: Any = None


VERSION_TYPE_TESTS: list[VersionTypeTest] = [
    VersionTypeTest(
        "int",
        version_value=8,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject int version value",
    ),
    VersionTypeTest(
        "long",
        version_value=Int64(8),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject long version value",
    ),
    VersionTypeTest(
        "double",
        version_value=8.0,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject double version value",
    ),
    VersionTypeTest(
        "decimal128",
        version_value=Decimal128("8.0"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject decimal128 version value",
    ),
    VersionTypeTest(
        "bool",
        version_value=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject bool version value",
    ),
    VersionTypeTest(
        "null",
        version_value=None,
        error_code=MISSING_FIELD_ERROR,
        msg="Should reject null version value",
    ),
    VersionTypeTest(
        "object",
        version_value={"version": "8.0"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject object version value",
    ),
    VersionTypeTest(
        "array",
        version_value=["8.0"],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array version value",
    ),
    VersionTypeTest(
        "date",
        version_value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject date version value",
    ),
    VersionTypeTest(
        "objectId",
        version_value=ObjectId(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject objectId version value",
    ),
    VersionTypeTest(
        "binData",
        version_value=Binary(b"\x00"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject binData version value",
    ),
    VersionTypeTest(
        "timestamp",
        version_value=Timestamp(0, 0),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject timestamp version value",
    ),
    VersionTypeTest(
        "regex",
        version_value=Regex(".*"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject regex version value",
    ),
    VersionTypeTest(
        "minKey",
        version_value=MinKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject minKey version value",
    ),
    VersionTypeTest(
        "maxKey",
        version_value=MaxKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject maxKey version value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VERSION_TYPE_TESTS))
def test_setFeatureCompatibilityVersion_version_type(collection, test):
    """Test setFeatureCompatibilityVersion rejects non-string version types."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": test.version_value, "confirm": True},
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)
