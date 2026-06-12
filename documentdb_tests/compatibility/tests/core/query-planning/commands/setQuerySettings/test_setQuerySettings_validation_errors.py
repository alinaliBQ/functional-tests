"""Tests for setQuerySettings command structural and validation errors.

Validates that the setQuerySettings command rejects malformed query shapes,
invalid hash strings, missing or empty settings, unrecognized fields, invalid
queryFramework values, and system collection restrictions.
"""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_NAMESPACE_ERROR,
    MISSING_FIELD_ERROR,
    QUERYSETTINGS_EMPTY_SETTINGS_ERROR,
    QUERYSETTINGS_INTERNAL_DB_ERROR,
    QUERYSETTINGS_NS_COLL_MISSING_ERROR,
    QUERYSETTINGS_NS_DB_MISSING_ERROR,
    QUERYSETTINGS_REJECT_ONLY_ERROR,
    QUERYSETTINGS_UNKNOWN_COMMAND_SHAPE_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
    UNSUPPORTED_FORMAT_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_query_shape_missing_db(collection: Collection):
    """Test setQuerySettings rejects a query shape document missing $db field."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=MISSING_FIELD_ERROR,
        msg="setQuerySettings should reject query shape missing $db field",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_query_shape_empty_db(collection: Collection):
    """Test setQuerySettings rejects a query shape with empty string $db."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": "",
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="setQuerySettings should reject query shape with empty $db",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_query_shape_unknown_command(collection: Collection):
    """Test setQuerySettings rejects a query shape with an unknown command type."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "unknownCommand": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=QUERYSETTINGS_UNKNOWN_COMMAND_SHAPE_ERROR,
        msg="setQuerySettings should reject unknown command type in query shape",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_empty_hash_string(collection: Collection):
    """Test setQuerySettings rejects an empty hash string."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": "",
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=UNSUPPORTED_FORMAT_ERROR,
        msg="setQuerySettings should reject empty hash string",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_indexHints_missing_ns(collection: Collection):
    """Test setQuerySettings rejects indexHints entry missing ns field."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=MISSING_FIELD_ERROR,
        msg="setQuerySettings should reject indexHints missing ns field",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_indexHints_ns_missing_db(collection: Collection):
    """Test setQuerySettings rejects indexHints.ns missing db field."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=QUERYSETTINGS_NS_DB_MISSING_ERROR,
        msg="setQuerySettings should reject indexHints.ns missing db field",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_indexHints_ns_missing_coll(collection: Collection):
    """Test setQuerySettings rejects indexHints.ns missing coll field."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=QUERYSETTINGS_NS_COLL_MISSING_ERROR,
        msg="setQuerySettings should reject indexHints.ns missing coll field",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_invalid_query_framework_value(collection: Collection):
    """Test setQuerySettings rejects an invalid queryFramework string value."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "queryFramework": "invalidFramework",
            },
        },
    )
    assertResult(
        result,
        error_code=BAD_VALUE_ERROR,
        msg="setQuerySettings should reject invalid queryFramework string",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_reject_false_only(collection: Collection):
    """Test setQuerySettings rejects settings with only reject: false and no other settings."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {"reject": False},
        },
    )
    assertResult(
        result,
        error_code=QUERYSETTINGS_REJECT_ONLY_ERROR,
        msg="setQuerySettings should reject settings with only reject: false",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_missing_settings(collection: Collection):
    """Test setQuerySettings rejects command missing the settings field entirely."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
        },
    )
    assertResult(
        result,
        error_code=MISSING_FIELD_ERROR,
        msg="setQuerySettings should reject missing settings field",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_empty_settings(collection: Collection):
    """Test setQuerySettings rejects empty settings document."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {},
        },
    )
    assertResult(
        result,
        error_code=QUERYSETTINGS_EMPTY_SETTINGS_ERROR,
        msg="setQuerySettings should reject empty settings document",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_unrecognized_top_level_field(collection: Collection):
    """Test setQuerySettings rejects unrecognized top-level fields."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
            "unknownField": 1,
        },
    )
    assertResult(
        result,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="setQuerySettings should reject unrecognized top-level field",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_system_collection(collection: Collection):
    """Test setQuerySettings rejects query shapes targeting internal databases."""
    result = execute_admin_command(
        collection,
        {
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
    )
    assertResult(
        result,
        error_code=QUERYSETTINGS_INTERNAL_DB_ERROR,
        msg="setQuerySettings should reject query shapes on internal databases",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_local_database(collection: Collection):
    """Test setQuerySettings rejects query shapes targeting local database."""
    result = execute_admin_command(
        collection,
        {
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
    )
    assertResult(
        result,
        error_code=QUERYSETTINGS_INTERNAL_DB_ERROR,
        msg="setQuerySettings should reject query shapes on local database",
    )
