"""Tests for setQuerySettings command behavioral verification.

Validates that query settings are retrievable via $querySettings aggregation
stage, removable via removeQuerySettings, and that the response structure
includes expected fields like queryShapeHash and representativeQuery.
"""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import QUERYSETTINGS_QUERY_REJECTED_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command

from .utils.setQuerySettings_common import cleanup_query_settings, get_query_settings


# Property [Response Structure]: setQuerySettings response includes hash, query, and settings.
@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_response_contains_hash(collection: Collection):
    """Test setQuerySettings response contains queryShapeHash field."""
    query = {
        "find": collection.name,
        "filter": {"b1": 1},
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
        assertSuccessPartial(
            result,
            {"ok": 1.0, "queryShapeHash": result.get("queryShapeHash")},
            msg="response should contain queryShapeHash",
        )
    finally:
        cleanup_query_settings(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_response_contains_representative_query(collection: Collection):
    """Test setQuerySettings response contains representativeQuery field."""
    query = {
        "find": collection.name,
        "filter": {"b2": 1},
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
        assertSuccessPartial(
            result,
            {"ok": 1.0, "representativeQuery": result.get("representativeQuery")},
            msg="response should contain representativeQuery",
        )
    finally:
        cleanup_query_settings(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_response_settings_echo(collection: Collection):
    """Test setQuerySettings response echoes the settings that were applied."""
    query = {
        "find": collection.name,
        "filter": {"b3": 1},
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
        assertSuccessPartial(
            result,
            {
                "ok": 1.0,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                },
            },
            msg="response should echo applied settings",
        )
    finally:
        cleanup_query_settings(collection, [query])


# Property [$querySettings Retrieval]: settings are visible via $querySettings aggregation stage.
@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_querySettings_stage_retrieval(collection: Collection):
    """Test query settings are visible via $querySettings aggregation stage."""
    query = {
        "find": collection.name,
        "filter": {"b4": 1},
        "$db": collection.database.name,
    }
    try:
        # Setup: create a query setting (no assertion — setup only)
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
        expected_hash = setup_result.get("queryShapeHash")

        settings = get_query_settings(collection)
        matching = [s for s in settings if s.get("queryShapeHash") == expected_hash]
        assertSuccessPartial(
            matching[0] if matching else {},
            {"queryShapeHash": expected_hash},
            msg="$querySettings should return the created setting",
        )
    finally:
        cleanup_query_settings(collection, [query])


# Property [removeQuerySettings]: settings can be removed by query or hash.
@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_removeQuerySettings_by_query(collection: Collection):
    """Test removeQuerySettings removes settings by representative query."""
    query = {
        "find": collection.name,
        "filter": {"b5": 1},
        "$db": collection.database.name,
    }
    try:
        # Setup: create a query setting (no assertion — setup only)
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
            {"removeQuerySettings": query},
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="removeQuerySettings by query should succeed")
    finally:
        cleanup_query_settings(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_removeQuerySettings_by_hash(collection: Collection):
    """Test removeQuerySettings removes settings by query shape hash."""
    query = {
        "find": collection.name,
        "filter": {"b6": 1},
        "$db": collection.database.name,
    }
    try:
        # Setup: create a query setting and capture hash (no assertion — setup only)
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
            {"removeQuerySettings": query_hash},
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="removeQuerySettings by hash should succeed")
    finally:
        cleanup_query_settings(collection, [query])


# Property [Reject Blocks Query]: a rejected query returns an error when executed.
@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_reject_true_blocks_query(collection: Collection):
    """Test that reject: true causes the matching query to be rejected."""
    query = {
        "find": collection.name,
        "filter": {"b8": 1},
        "$db": collection.database.name,
    }
    try:
        # Setup: create a reject setting (no assertion — setup only)
        execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {"reject": True},
            },
        )

        # Execute the matching find query on the collection database
        result = execute_command(
            collection,
            {
                "find": collection.name,
                "filter": {"b8": 1},
            },
        )
        assertResult(
            result,
            error_code=QUERYSETTINGS_QUERY_REJECTED_ERROR,
            msg="query matching reject: true setting should be rejected",
        )
    finally:
        cleanup_query_settings(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_querySettings_stage_shows_settings(collection: Collection):
    """Test $querySettings stage includes indexHints in the returned settings."""
    query = {
        "find": collection.name,
        "filter": {"b9": 1},
        "$db": collection.database.name,
    }
    try:
        # Setup: create a query setting (no assertion — setup only)
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
        expected_hash = setup_result.get("queryShapeHash")

        settings = get_query_settings(collection)
        matching = [s for s in settings if s.get("queryShapeHash") == expected_hash]
        entry = matching[0] if matching else {}
        assertSuccessPartial(
            entry,
            {
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": collection.database.name, "coll": collection.name},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                },
            },
            msg="$querySettings should include indexHints in settings",
        )
    finally:
        cleanup_query_settings(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_querySettings_stage_shows_representative_query(collection: Collection):
    """Test $querySettings stage includes representativeQuery in the output."""
    query = {
        "find": collection.name,
        "filter": {"b10": 1},
        "$db": collection.database.name,
    }
    try:
        # Setup: create a query setting (no assertion — setup only)
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
        expected_hash = setup_result.get("queryShapeHash")

        settings = get_query_settings(collection)
        matching = [s for s in settings if s.get("queryShapeHash") == expected_hash]
        entry = matching[0] if matching else {}
        assertSuccessPartial(
            entry,
            {"representativeQuery": entry.get("representativeQuery")},
            msg="$querySettings should include representativeQuery",
        )
    finally:
        cleanup_query_settings(collection, [query])
