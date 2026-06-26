"""
Tests for setFeatureCompatibilityVersion version value validation.

Covers: valid version strings, invalid/malformed versions, edge cases.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

# MongoDB 8.2 returns this code for invalid FCV version strings
INVALID_FCV_VERSION_ERROR = 4926900

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_fcv(collection) -> str:
    """Read back the current FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        pytest.skip("Cannot read FCV via getParameter")
    return result["featureCompatibilityVersion"]["version"]


@dataclass(frozen=True)
class VersionValueTest(BaseTestCase):
    """Test case for version value validation."""

    version_value: Any = None


INVALID_VERSION_TESTS: list[VersionValueTest] = [
    VersionValueTest(
        "empty_string",
        version_value="",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject empty string version",
    ),
    VersionValueTest(
        "major_only",
        version_value="8",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject major-only version string",
    ),
    VersionValueTest(
        "full_semver",
        version_value="8.0.0",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject full semver version string",
    ),
    VersionValueTest(
        "leading_whitespace",
        version_value=" 7.0",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject version with leading whitespace",
    ),
    VersionValueTest(
        "trailing_whitespace",
        version_value="7.0 ",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject version with trailing whitespace",
    ),
    VersionValueTest(
        "below_supported_floor",
        version_value="3.0",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject version below supported floor",
    ),
    VersionValueTest(
        "above_max_supported",
        version_value="99.0",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject version above max supported",
    ),
    VersionValueTest(
        "future_version",
        version_value="10.0",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject future version",
    ),
    VersionValueTest(
        "zero_version",
        version_value="0.0",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject zero version",
    ),
    VersionValueTest(
        "non_numeric_chars",
        version_value="abc",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject non-numeric version string",
    ),
    VersionValueTest(
        "unicode_digits",
        version_value="\uff18.\uff10",
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject unicode digit version string",
    ),
    VersionValueTest(
        "very_long_string",
        version_value="8." + "0" * 1000,
        error_code=INVALID_FCV_VERSION_ERROR,
        msg="Should reject very long version string without crash",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_VERSION_TESTS))
def test_setFeatureCompatibilityVersion_invalid_version_value(collection, test):
    """Test setFeatureCompatibilityVersion rejects invalid version strings."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": test.version_value, "confirm": True},
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)


def test_setFeatureCompatibilityVersion_valid_current_version_accepted(collection):
    """Test that the current deployment version string is accepted."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": current_fcv, "confirm": True}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Current version string should be accepted")
