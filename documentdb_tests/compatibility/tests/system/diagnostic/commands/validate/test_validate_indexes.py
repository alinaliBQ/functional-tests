"""Tests for validate command with various index types.

Validates that validate succeeds and correctly reports on collections with
different index types including unique, sparse, TTL, text, 2dsphere, hashed,
wildcard, compound, and partial filter indexes.
"""

from __future__ import annotations

from datetime import datetime, timezone

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq


def test_validate_unique_index(collection):
    """Test validate with a unique index reports it in results."""
    collection.insert_many([{"_id": i, "x": i} for i in range(5)])
    collection.create_index("x", unique=True)
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nIndexes": 2},
        msg="validate should succeed and report unique index",
    )


def test_validate_sparse_index(collection):
    """Test validate with a sparse index shows fewer keys than nrecords."""
    collection.insert_many(
        [{"_id": i, "x": i} for i in range(5)]
        + [{"_id": i} for i in range(5, 10)]  # 5 docs without 'x' field
    )
    collection.create_index("x", sparse=True)
    result = execute_command(collection, {"validate": collection.name})
    assertProperties(
        result,
        {"ok": Eq(1.0), "valid": Eq(True), "nrecords": Eq(10), "nIndexes": Eq(2)},
        raw_res=True,
        msg="validate should succeed with sparse index",
    )


def test_validate_ttl_index(collection):
    """Test validate with a TTL index reports it in results."""
    collection.insert_one({"_id": 1, "created": datetime(2024, 1, 1, tzinfo=timezone.utc)})
    collection.create_index("created", expireAfterSeconds=3600)
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nIndexes": 2},
        msg="validate should succeed and report TTL index",
    )


def test_validate_text_index(collection):
    """Test validate with a text index succeeds."""
    collection.insert_many([{"_id": i, "content": f"document text {i}"} for i in range(5)])
    collection.create_index([("content", "text")])
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True},
        msg="validate should succeed with text index",
    )


def test_validate_2dsphere_index(collection):
    """Test validate with a 2dsphere index succeeds."""
    collection.insert_one({"_id": 1, "location": {"type": "Point", "coordinates": [0.0, 0.0]}})
    collection.create_index([("location", "2dsphere")])
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True},
        msg="validate should succeed with 2dsphere index",
    )


def test_validate_hashed_index(collection):
    """Test validate with a hashed index succeeds."""
    collection.insert_many([{"_id": i, "x": i} for i in range(5)])
    collection.create_index([("x", "hashed")])
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nIndexes": 2},
        msg="validate should succeed with hashed index",
    )


def test_validate_wildcard_index(collection):
    """Test validate with a wildcard index succeeds."""
    collection.insert_many([{"_id": i, "a": i, "b": str(i)} for i in range(5)])
    collection.create_index([("$**", 1)])
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True},
        msg="validate should succeed with wildcard index",
    )


def test_validate_compound_index(collection):
    """Test validate with a compound index reports it in results."""
    collection.insert_many([{"_id": i, "a": i, "b": -i} for i in range(5)])
    collection.create_index([("a", 1), ("b", -1)])
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nIndexes": 2},
        msg="validate should succeed and report compound index",
    )


def test_validate_partial_filter_index(collection):
    """Test validate with a partial filter index succeeds."""
    collection.insert_many([{"_id": i, "x": i} for i in range(10)])
    collection.create_index(
        "x",
        partialFilterExpression={"x": {"$gt": 4}},
    )
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nIndexes": 2},
        msg="validate should succeed with partial filter index",
    )


def test_validate_multiple_indexes(collection):
    """Test validate with multiple index types reports correct nIndexes."""
    collection.insert_many([{"_id": i, "a": i, "b": str(i)} for i in range(5)])
    collection.create_index("a", unique=True)
    collection.create_index("b")
    collection.create_index([("a", 1), ("b", 1)])
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True, "nIndexes": 4},
        msg="validate should report all 4 indexes (_id + 3 secondary)",
    )
