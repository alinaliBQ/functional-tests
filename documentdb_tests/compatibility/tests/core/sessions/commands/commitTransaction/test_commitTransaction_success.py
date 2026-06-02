"""Tests for commitTransaction success cases.

Validates that commitTransaction returns ok:1 when run inside an active
transaction, and verifies committed data is persisted.
These tests require a replica set (transactions are not supported on standalone).
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.replica_set]


# Property [Successful Commit]: commitTransaction inside an active transaction returns ok:1.
def test_commitTransaction_success(collection):
    """Test commitTransaction succeeds inside an active transaction."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": "txn_success_test", "x": 1}, session=session)
        result = execute_admin_command(
            collection,
            {"commitTransaction": 1, "autocommit": False},
            session=session,
        )
    assertSuccessPartial(result, {"ok": 1.0}, msg="commitTransaction should return ok:1")


# Property [Commit Persists Data]: committed data is visible after the transaction.
def test_commitTransaction_data_persisted(collection):
    """Test commitTransaction persists inserted data after commit."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": "txn_persist_test", "x": 42}, session=session)
        execute_admin_command(
            collection,
            {"commitTransaction": 1, "autocommit": False},
            session=session,
        )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": "txn_persist_test"}},
    )
    assertSuccessPartial(
        result["cursor"]["firstBatch"][0],
        {"_id": "txn_persist_test", "x": 42},
        msg="committed document should be visible after transaction",
    )
