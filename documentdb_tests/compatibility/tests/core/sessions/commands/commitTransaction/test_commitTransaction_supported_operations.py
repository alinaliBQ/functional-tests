"""Tests for CRUD operations that are supported inside a transaction.

Reads (find), aggregation (including ``$count``, the supported counterpart to
the disallowed ``count`` command), and writes (update, delete) all run inside a
transaction and their effects are durable after commit. Each test runs the
operation in the transaction and commits.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_find_runs_in_transaction(collection):
    """A find issued inside a transaction returns the collection's documents."""
    collection.insert_one({"_id": 1})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection, {"find": collection.name, "filter": {}}, session=session
        )
        session.commit_transaction()
    assertSuccess(result, [{"_id": 1}])


def test_aggregate_count_runs_in_transaction(collection):
    """An aggregate with $count runs inside a transaction and returns the count."""
    collection.insert_many([{"_id": 1}, {"_id": 2}])
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection,
            {"aggregate": collection.name, "pipeline": [{"$count": "n"}], "cursor": {}},
            session=session,
        )
        session.commit_transaction()
    assertSuccess(result, [{"n": 2}])


def test_update_runs_in_transaction(collection):
    """An update issued inside a transaction is durable after commit."""
    collection.insert_one({"_id": 1, "x": "before"})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.update_one({"_id": 1}, {"$set": {"x": "after"}}, session=session)
        session.commit_transaction()
    readback = execute_command(collection, {"find": collection.name, "filter": {}})
    assertSuccess(readback, [{"_id": 1, "x": "after"}])


def test_delete_runs_in_transaction(collection):
    """A delete issued inside a transaction is durable after commit."""
    collection.insert_one({"_id": 1})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.delete_one({"_id": 1}, session=session)
        session.commit_transaction()
    readback = execute_command(collection, {"find": collection.name, "filter": {}})
    assertSuccess(readback, [])
