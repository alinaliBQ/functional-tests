"""Tests for setQuerySettings command settings configurations.

Validates that the setQuerySettings command accepts valid settings
combinations including indexHints, reject, queryFramework, and comment
fields, as well as allowedIndexes variations and update behavior.
"""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    QUERYSETTINGS_IDHACK_QUERY_ERROR,
    QUERYSETTINGS_REJECT_ONLY_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command


def _cleanup(collection: Collection, queries: list[dict]) -> None:
    """Remove all query settings created during the test."""
    admin = collection.database.client.admin
    for q in queries:
        try:
            admin.command({"removeQuerySettings": q})
        except Exception:
            pass


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_indexHints_single_index(collection: Collection):
    """Test setQuerySettings accepts indexHints with a single named index."""
    query = {
        "find": collection.name,
        "filter": {"a1": 1},
        "$db": collection.database.name,
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
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
        assertSuccessPartial(result, {"ok": 1.0}, msg="should accept indexHints with single index")
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_indexHints_multiple_indexes(collection: Collection):
    """Test setQuerySettings accepts indexHints with multiple allowedIndexes entries."""
    query = {
        "find": collection.name,
        "filter": {"a2": 1},
        "$db": collection.database.name,
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": ["_id_", {"a2": 1}],
                        }
                    ],
                },
            },
        )
        assertSuccessPartial(
            result,
            {"ok": 1.0},
            msg="should accept multiple indexes",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_indexHints_key_pattern(collection: Collection):
    """Test setQuerySettings accepts indexHints with index key pattern instead of name."""
    query = {
        "find": collection.name,
        "filter": {"a3": 1},
        "$db": collection.database.name,
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": [{"a3": 1}],
                        }
                    ],
                },
            },
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="should accept indexHints with key pattern")
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_indexHints_empty_allowed_rejected(collection: Collection):
    """Test setQuerySettings rejects indexHints with empty allowedIndexes as empty settings."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"a4": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": [],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=QUERYSETTINGS_REJECT_ONLY_ERROR,
        msg="should reject indexHints with empty allowedIndexes",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_reject_true(collection: Collection):
    """Test setQuerySettings accepts settings with reject: true."""
    query = {
        "find": collection.name,
        "filter": {"a5": 1},
        "$db": collection.database.name,
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {"reject": True},
            },
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="should accept settings with reject: true")
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_reject_with_indexHints(collection: Collection):
    """Test setQuerySettings accepts settings with both reject and indexHints."""
    query = {
        "find": collection.name,
        "filter": {"a6": 1},
        "$db": collection.database.name,
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                    "reject": True,
                },
            },
        )
        assertSuccessPartial(
            result,
            {"ok": 1.0},
            msg="should accept reject with indexHints",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_queryFramework_classic(collection: Collection):
    """Test setQuerySettings accepts queryFramework: classic."""
    query = {
        "find": collection.name,
        "filter": {"a7": 1},
        "$db": collection.database.name,
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                    "queryFramework": "classic",
                },
            },
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="should accept queryFramework: classic")
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_queryFramework_sbe(collection: Collection):
    """Test setQuerySettings accepts queryFramework: sbe."""
    query = {
        "find": collection.name,
        "filter": {"a8": 1},
        "$db": collection.database.name,
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                    "queryFramework": "sbe",
                },
            },
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="should accept queryFramework: sbe")
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_with_comment_string(collection: Collection):
    """Test setQuerySettings accepts a comment field with string value."""
    query = {
        "find": collection.name,
        "filter": {"a9": 1},
        "$db": collection.database.name,
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                },
                "comment": "test comment for setQuerySettings",
            },
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="should accept command with comment string")
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_update_existing_settings(collection: Collection):
    """Test setQuerySettings can update settings for an existing query shape."""
    query = {
        "find": collection.name,
        "filter": {"a10": 1},
        "$db": collection.database.name,
    }
    try:
        # Setup: create initial settings (no assertion — setup only)
        execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
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

        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": ["_id_", {"a10": 1}],
                        }
                    ],
                },
            },
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="update setQuerySettings should succeed")
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_update_via_hash(collection: Collection):
    """Test setQuerySettings can update settings using the query shape hash."""
    query = {
        "find": collection.name,
        "filter": {"a11": 1},
        "$db": collection.database.name,
    }
    try:
        # Setup: create initial settings and capture hash (no assertion — setup only)
        setup_result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
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

        query_hash = setup_result.get("queryShapeHash")
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query_hash,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": ["_id_", {"a11": 1}],
                        }
                    ],
                },
            },
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="update via hash should succeed")
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_idhack_query_rejected(collection: Collection):
    """Test setQuerySettings rejects queries eligible for IDHACK optimization."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"_id": 1},
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
        error_code=QUERYSETTINGS_IDHACK_QUERY_ERROR,
        msg="setQuerySettings should reject IDHACK-eligible queries",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_all_settings_combined(collection: Collection):
    """Test setQuerySettings accepts all settings fields combined."""
    query = {
        "find": collection.name,
        "filter": {"a12": 1},
        "$db": collection.database.name,
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                    "queryFramework": "classic",
                    "reject": True,
                },
            },
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="should accept all settings combined")
    finally:
        _cleanup(collection, [query])
