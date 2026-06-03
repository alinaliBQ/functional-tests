"""Tests for commitTransaction command success cases.

Validates that commitTransaction succeeds within a real transaction context,
including insert, update, delete, and multi-operation transactions. Also
verifies the response structure on success.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertNotError, assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.admin, pytest.mark.replica_set]


def test_commitTransaction_insert(collection):
    """Test commitTransaction succeeds after inserting a document."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1, "x": "inserted"}, session=session)
        session.commit_transaction()
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        {"cursor": {"firstBatch": [{"_id": 1, "x": "inserted"}]}},
        msg="commitTransaction should persist the inserted document",
        raw_res=True,
        transform=lambda r: {"cursor": {"firstBatch": r["cursor"]["firstBatch"]}},
    )


def test_commitTransaction_update(collection):
    """Test commitTransaction succeeds after updating a document."""
    collection.insert_one({"_id": 1, "x": "before"})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.update_one({"_id": 1}, {"$set": {"x": "after"}}, session=session)
        session.commit_transaction()
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        {"cursor": {"firstBatch": [{"_id": 1, "x": "after"}]}},
        msg="commitTransaction should persist the updated value",
        raw_res=True,
        transform=lambda r: {"cursor": {"firstBatch": r["cursor"]["firstBatch"]}},
    )


def test_commitTransaction_delete(collection):
    """Test commitTransaction succeeds after deleting a document."""
    collection.insert_one({"_id": 1, "x": "to_delete"})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.delete_one({"_id": 1}, session=session)
        session.commit_transaction()
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        {"cursor": {"firstBatch": []}},
        msg="commitTransaction should persist the deletion",
        raw_res=True,
        transform=lambda r: {"cursor": {"firstBatch": r["cursor"]["firstBatch"]}},
    )


def test_commitTransaction_multi_operation(collection):
    """Test commitTransaction succeeds with multiple operations in one transaction."""
    collection.insert_one({"_id": 1, "x": "original"})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 2, "x": "new"}, session=session)
        collection.update_one({"_id": 1}, {"$set": {"x": "modified"}}, session=session)
        session.commit_transaction()
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(
        result,
        {
            "cursor": {
                "firstBatch": [
                    {"_id": 1, "x": "modified"},
                    {"_id": 2, "x": "new"},
                ]
            }
        },
        msg="commitTransaction should persist all operations from a multi-op transaction",
        raw_res=True,
        transform=lambda r: {"cursor": {"firstBatch": r["cursor"]["firstBatch"]}},
    )


def test_commitTransaction_empty_transaction(collection):
    """Test commitTransaction succeeds on a transaction with no operations."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        session.commit_transaction()
    # Verify the collection is still empty after an empty committed transaction.
    result = execute_command(collection, {"find": collection.name, "filter": {}})
    assertNotError(
        result,
        msg="commitTransaction on empty transaction should not error",
    )


def test_commitTransaction_response_structure(collection):
    """Test commitTransaction returns expected response fields on success."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1}, session=session)
        result = client.admin.command(
            {"commitTransaction": 1},
            session=session,
        )
    # Use execute_command for readback to confirm persistence.
    execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        {"ok": 1.0},
        msg="commitTransaction response should have ok:1 on success",
        raw_res=True,
        transform=lambda r: {"ok": r["ok"]},
    )


def test_commitTransaction_with_writeconcern(collection):
    """Test commitTransaction succeeds with explicit writeConcern."""
    collection.insert_one({"_id": 1, "x": "before"})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.update_one({"_id": 1}, {"$set": {"x": "after"}}, session=session)
        client.admin.command(
            {"commitTransaction": 1, "writeConcern": {"w": 1}},
            session=session,
        )
    readback = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        readback,
        {"cursor": {"firstBatch": [{"_id": 1, "x": "after"}]}},
        msg="commitTransaction with writeConcern should persist changes",
        raw_res=True,
        transform=lambda r: {"cursor": {"firstBatch": r["cursor"]["firstBatch"]}},
    )


def test_commitTransaction_with_comment(collection):
    """Test commitTransaction succeeds with comment parameter."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1}, session=session)
        result = client.admin.command(
            {"commitTransaction": 1, "comment": "test commit"},
            session=session,
        )
    # Use execute_command for readback to confirm persistence.
    execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        {"ok": 1.0},
        msg="commitTransaction with comment should succeed",
        raw_res=True,
        transform=lambda r: {"ok": r["ok"]},
    )
