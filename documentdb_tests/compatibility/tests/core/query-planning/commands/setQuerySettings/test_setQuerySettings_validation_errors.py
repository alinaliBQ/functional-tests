"""Tests for setQuerySettings command structural and validation errors.

Validates that the setQuerySettings command rejects malformed query shapes,
invalid hash strings, missing or empty settings, unrecognized fields, invalid
queryFramework values, and system collection restrictions.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_NAMESPACE_ERROR,
    MISSING_FIELD_ERROR,
    QUERYSETTINGS_EMPTY_SETTINGS_ERROR,
    QUERYSETTINGS_IDHACK_QUERY_ERROR,
    QUERYSETTINGS_INTERNAL_DB_ERROR,
    QUERYSETTINGS_NS_COLL_MISSING_ERROR,
    QUERYSETTINGS_NS_DB_MISSING_ERROR,
    QUERYSETTINGS_REJECT_ONLY_ERROR,
    QUERYSETTINGS_UNKNOWN_COMMAND_SHAPE_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
    UNSUPPORTED_FORMAT_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# -- helpers ------------------------------------------------------------------


def _default_settings(ctx: CommandContext) -> dict:
    """Build the standard indexHints settings block."""
    return {
        "indexHints": [
            {
                "ns": {"db": ctx.database, "coll": ctx.collection},
                "allowedIndexes": ["_id_"],
            }
        ],
    }


def _default_query(ctx: CommandContext) -> dict:
    """Build a minimal valid query shape."""
    return {
        "find": ctx.collection,
        "filter": {"x": 1},
        "$db": ctx.database,
    }


# Property [Query Shape Validation]: rejects malformed or unknown query shape documents.
# Property [Hash String Validation]: rejects invalid hash string formats.
# Property [indexHints Structure Validation]: rejects indexHints missing required sub-fields.
# Property [Settings Value Validation]: rejects invalid field values in settings document.
# Property [Settings Presence]: rejects missing or empty settings document.
# Property [Unrecognized Fields]: rejects unknown top-level command fields.
# Property [Database Restrictions]: rejects query shapes targeting internal databases.
# Property [indexHints Value Validation]: rejects empty allowedIndexes and IDHACK queries.
SET_QUERY_SETTINGS_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_shape_missing_db",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
            },
            "settings": _default_settings(ctx),
        },
        error_code=MISSING_FIELD_ERROR,
        msg="setQuerySettings should reject query shape missing $db field",
    ),
    CommandTestCase(
        "query_shape_empty_db",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": "",
            },
            "settings": _default_settings(ctx),
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="setQuerySettings should reject query shape with empty $db",
    ),
    CommandTestCase(
        "query_shape_unknown_command",
        command=lambda ctx: {
            "setQuerySettings": {
                "unknownCommand": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            },
            "settings": _default_settings(ctx),
        },
        error_code=QUERYSETTINGS_UNKNOWN_COMMAND_SHAPE_ERROR,
        msg="setQuerySettings should reject unknown command type in query shape",
    ),
    CommandTestCase(
        "empty_hash_string",
        command=lambda ctx: {
            "setQuerySettings": "",
            "settings": _default_settings(ctx),
        },
        error_code=UNSUPPORTED_FORMAT_ERROR,
        msg="setQuerySettings should reject empty hash string",
    ),
    CommandTestCase(
        "indexHints_missing_ns",
        command=lambda ctx: {
            "setQuerySettings": _default_query(ctx),
            "settings": {
                "indexHints": [
                    {
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
        error_code=MISSING_FIELD_ERROR,
        msg="setQuerySettings should reject indexHints missing ns field",
    ),
    CommandTestCase(
        "indexHints_ns_missing_db",
        command=lambda ctx: {
            "setQuerySettings": _default_query(ctx),
            "settings": {
                "indexHints": [
                    {
                        "ns": {"coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
        error_code=QUERYSETTINGS_NS_DB_MISSING_ERROR,
        msg="setQuerySettings should reject indexHints.ns missing db field",
    ),
    CommandTestCase(
        "indexHints_ns_missing_coll",
        command=lambda ctx: {
            "setQuerySettings": _default_query(ctx),
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
        error_code=QUERYSETTINGS_NS_COLL_MISSING_ERROR,
        msg="setQuerySettings should reject indexHints.ns missing coll field",
    ),
    CommandTestCase(
        "invalid_query_framework_value",
        command=lambda ctx: {
            "setQuerySettings": _default_query(ctx),
            "settings": {**_default_settings(ctx), "queryFramework": "invalidFramework"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="setQuerySettings should reject invalid queryFramework string",
    ),
    CommandTestCase(
        "reject_false_only",
        command=lambda ctx: {
            "setQuerySettings": _default_query(ctx),
            "settings": {"reject": False},
        },
        error_code=QUERYSETTINGS_REJECT_ONLY_ERROR,
        msg="setQuerySettings should reject settings with only reject: false",
    ),
    CommandTestCase(
        "missing_settings",
        command=lambda ctx: {
            "setQuerySettings": _default_query(ctx),
        },
        error_code=MISSING_FIELD_ERROR,
        msg="setQuerySettings should reject missing settings field",
    ),
    CommandTestCase(
        "empty_settings",
        command=lambda ctx: {
            "setQuerySettings": _default_query(ctx),
            "settings": {},
        },
        error_code=QUERYSETTINGS_EMPTY_SETTINGS_ERROR,
        msg="setQuerySettings should reject empty settings document",
    ),
    CommandTestCase(
        "unrecognized_top_level_field",
        command=lambda ctx: {
            "setQuerySettings": _default_query(ctx),
            "settings": _default_settings(ctx),
            "unknownField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="setQuerySettings should reject unrecognized top-level field",
    ),
    CommandTestCase(
        "system_collection",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": "system.users",
                "filter": {},
                "$db": "admin",
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": "admin", "coll": "system.users"},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
        error_code=QUERYSETTINGS_INTERNAL_DB_ERROR,
        msg="setQuerySettings should reject query shapes on internal databases",
    ),
    CommandTestCase(
        "local_database",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": "oplog.rs",
                "filter": {},
                "$db": "local",
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": "local", "coll": "oplog.rs"},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
        error_code=QUERYSETTINGS_INTERNAL_DB_ERROR,
        msg="setQuerySettings should reject query shapes on local database",
    ),
    CommandTestCase(
        "indexHints_empty_allowed_rejected",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a4": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": [],
                    }
                ],
            },
        },
        error_code=QUERYSETTINGS_REJECT_ONLY_ERROR,
        msg="setQuerySettings should reject indexHints with empty allowedIndexes",
    ),
    CommandTestCase(
        "idhack_query_rejected",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"_id": 1},
                "$db": ctx.database,
            },
            "settings": _default_settings(ctx),
        },
        error_code=QUERYSETTINGS_IDHACK_QUERY_ERROR,
        msg="setQuerySettings should reject IDHACK-eligible queries",
    ),
]


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_VALIDATION_ERROR_TESTS))
def test_setQuerySettings_validation_errors(collection, test):
    """Test setQuerySettings structural and validation error rejection."""
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        error_code=test.error_code,
        msg=test.msg,
    )
