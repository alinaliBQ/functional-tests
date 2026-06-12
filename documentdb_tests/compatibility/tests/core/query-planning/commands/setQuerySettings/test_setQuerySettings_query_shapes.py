"""Tests for setQuerySettings command query shape acceptance.

Validates that the setQuerySettings command accepts valid query shapes for
find, distinct, and aggregate commands, including various shape variations,
field combinations, and $db field variations.
"""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.framework.assertions import assertSuccessPartial
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
def test_setQuerySettings_find_shape(collection: Collection):
    """Test setQuerySettings accepts a valid find query shape."""
    query = {
        "find": collection.name,
        "filter": {"x": 1},
        "sort": {"x": 1},
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
            {"ok": 1.0},
            msg="should accept valid find shape",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_distinct_shape(collection: Collection):
    """Test setQuerySettings accepts a valid distinct query shape."""
    query = {
        "distinct": collection.name,
        "key": "x",
        "query": {"x": {"$gt": 0}},
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
            {"ok": 1.0},
            msg="should accept valid distinct shape",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_aggregate_shape(collection: Collection):
    """Test setQuerySettings accepts a valid aggregate query shape."""
    query = {
        "aggregate": collection.name,
        "pipeline": [{"$match": {"x": 1}}],
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
            {"ok": 1.0},
            msg="should accept valid aggregate shape",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_find_filter_only(collection: Collection):
    """Test setQuerySettings accepts find shape with only filter, no sort or projection."""
    query = {
        "find": collection.name,
        "filter": {"a": 1},
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
            {"ok": 1.0},
            msg="should accept find with filter only",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_find_filter_sort(collection: Collection):
    """Test setQuerySettings accepts find shape with filter and sort."""
    query = {
        "find": collection.name,
        "filter": {"b": 1},
        "sort": {"b": 1},
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
            {"ok": 1.0},
            msg="should accept find with filter+sort",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_find_filter_projection(collection: Collection):
    """Test setQuerySettings accepts find shape with filter and projection."""
    query = {
        "find": collection.name,
        "filter": {"c": 1},
        "projection": {"c": 1},
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
            {"ok": 1.0},
            msg="should accept find with filter+projection",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_find_filter_sort_projection(collection: Collection):
    """Test setQuerySettings accepts find shape with filter, sort, and projection."""
    query = {
        "find": collection.name,
        "filter": {"d": 1},
        "sort": {"d": 1},
        "projection": {"d": 1},
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
            {"ok": 1.0},
            msg="should accept find with all fields",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_find_with_collation(collection: Collection):
    """Test setQuerySettings accepts find shape with collation."""
    query = {
        "find": collection.name,
        "filter": {"e": "abc"},
        "collation": {"locale": "en", "strength": 2},
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
            {"ok": 1.0},
            msg="should accept find with collation",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_find_with_let(collection: Collection):
    """Test setQuerySettings accepts find shape with let variables."""
    query = {
        "find": collection.name,
        "filter": {"$expr": {"$eq": ["$f", "$$target"]}},
        "let": {"target": 1},
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
            {"ok": 1.0},
            msg="should accept find with let",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_find_with_limit(collection: Collection):
    """Test setQuerySettings accepts find shape containing limit."""
    query = {
        "find": collection.name,
        "filter": {"g": 1},
        "limit": 10,
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
            {"ok": 1.0},
            msg="should accept find with limit",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_distinct_key_only(collection: Collection):
    """Test setQuerySettings accepts distinct shape with key only, no query filter."""
    query = {
        "distinct": collection.name,
        "key": "j",
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
            {"ok": 1.0},
            msg="should accept distinct key only",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_distinct_complex_query(collection: Collection):
    """Test setQuerySettings accepts distinct shape with complex query filter."""
    query = {
        "distinct": collection.name,
        "key": "k",
        "query": {"$and": [{"k": {"$gt": 0}}, {"k": {"$lt": 100}}]},
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
            {"ok": 1.0},
            msg="should accept distinct complex query",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_aggregate_match_only(collection: Collection):
    """Test setQuerySettings accepts aggregate shape with single $match stage."""
    query = {
        "aggregate": collection.name,
        "pipeline": [{"$match": {"l": 1}}],
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
            {"ok": 1.0},
            msg="should accept aggregate $match only",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_aggregate_match_group(collection: Collection):
    """Test setQuerySettings accepts aggregate shape with $match and $group pipeline."""
    query = {
        "aggregate": collection.name,
        "pipeline": [{"$match": {"m": 1}}, {"$group": {"_id": "$m", "count": {"$sum": 1}}}],
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
            {"ok": 1.0},
            msg="should accept aggregate $match+$group",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_aggregate_match_sort_limit(collection: Collection):
    """Test setQuerySettings accepts aggregate shape with $match, $sort, and $limit."""
    query = {
        "aggregate": collection.name,
        "pipeline": [{"$match": {"n": 1}}, {"$sort": {"n": 1}}, {"$limit": 5}],
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
            {"ok": 1.0},
            msg="should accept aggregate $match+$sort+$limit",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_db_nonexistent(collection: Collection):
    """Test setQuerySettings accepts $db pointing to a non-existent database."""
    query = {
        "find": collection.name,
        "filter": {"o": 1},
        "$db": "nonexistent_db_for_query_settings_test",
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {
                                "db": "nonexistent_db_for_query_settings_test",
                                "coll": collection.name,
                            },
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                },
            },
        )
        assertSuccessPartial(
            result,
            {"ok": 1.0},
            msg="should accept non-existent $db",
        )
    finally:
        _cleanup(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_db_special_characters(collection: Collection):
    """Test setQuerySettings accepts $db with special characters like hyphens."""
    query = {
        "find": collection.name,
        "filter": {"p": 1},
        "$db": "test-special-db",
    }
    try:
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {
                    "indexHints": [
                        {
                            "ns": {"db": "test-special-db", "coll": collection.name},
                            "allowedIndexes": ["_id_"],
                        }
                    ],
                },
            },
        )
        assertSuccessPartial(
            result,
            {"ok": 1.0},
            msg="should accept $db with special chars",
        )
    finally:
        _cleanup(collection, [query])
