"""Tests for setFeatureCompatibilityVersion error conditions.

Covers admin-database-only enforcement and unknown/extra field rejection.

Admin enforcement: the command must be issued on the admin database.
Running it on a user database fails with UNAUTHORIZED_ERROR (13).

Unknown field rejection: unrecognized top-level fields fail with
UNRECOGNIZED_COMMAND_FIELD_ERROR (40415). A misspelled 'confirm' field
is treated as an unknown field (40415) rather than an invalid confirm value,
and the real confirm is still considered missing.

None of these tests change FCV state.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    UNAUTHORIZED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Admin-Only]: setFeatureCompatibilityVersion is rejected on non-admin databases.
def test_setFeatureCompatibilityVersion_non_admin_db_rejected(collection):
    """Test setFeatureCompatibilityVersion fails when issued against a non-admin database."""
    result = execute_command(
        collection,
        {"setFeatureCompatibilityVersion": "8.0", "confirm": True},
    )
    assertFailureCode(
        result,
        UNAUTHORIZED_ERROR,
        msg="setFeatureCompatibilityVersion must be run on the admin database.",
    )


def test_setFeatureCompatibilityVersion_nonexistent_db_rejected(collection):
    """Test setFeatureCompatibilityVersion fails on a non-existent user database."""
    other_db = collection.database.client[f"{collection.name}_nonexistent_db"]
    other_col = other_db[collection.name]
    result = execute_command(
        other_col,
        {"setFeatureCompatibilityVersion": "8.0", "confirm": True},
    )
    assertFailureCode(
        result,
        UNAUTHORIZED_ERROR,
        msg="setFeatureCompatibilityVersion must be run on the admin database.",
    )


# Property [Unknown Fields]: unrecognized top-level fields are rejected with
# UNRECOGNIZED_COMMAND_FIELD_ERROR (40415).
def test_setFeatureCompatibilityVersion_unknown_field_rejected(collection):
    """Test setFeatureCompatibilityVersion rejects an unrecognized top-level field."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": "8.0", "confirm": True, "unknownField": 1},
    )
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="setFeatureCompatibilityVersion should reject an unrecognized top-level field.",
    )


def test_setFeatureCompatibilityVersion_misspelled_confirm_rejected(collection):
    """Test a misspelled confirm field is treated as an unknown field."""
    result = execute_admin_command(
        collection,
        # 'confrim' is not 'confirm' — treated as unrecognized, not as a confirm value
        {"setFeatureCompatibilityVersion": "8.0", "confrim": True},
    )
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="A misspelled confirm field should be treated as an unrecognized field.",
    )
