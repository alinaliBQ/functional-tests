"""Tests for commitTransaction command success cases.

Validates that commitTransaction succeeds within a real transaction context,
including insert, update, delete, and multi-operation transactions. Also
verifies the response structure on success.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_test_case import (
    SessionTestCase,
)
from documentdb_tests.framework.assertions import (
    assertNotError,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


# ---------------------------------------------------------------------------
# Property [Commit Persistence]: committed operations are durable.
# ---------------------------------------------------------------------------

COMMIT_PERSISTENCE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "commit_insert",
        ops=[lambda c, s: c.insert_one({"_id": 1, "x": "inserted"}, session=s)],
        expected=[{"_id": 1, "x": "inserted"}],
        msg="commitTransaction should persist the inserted document",
    ),
    SessionTestCase(
        "commit_update",
        docs=[{"_id": 1, "x": "before"}],
        ops=[lambda c, s: c.update_one({"_id": 1}, {"$set": {"x": "after"}}, session=s)],
        expected=[{"_id": 1, "x": "after"}],
        msg="commitTransaction should persist the updated value",
    ),
    SessionTestCase(
        "commit_delete",
        docs=[{"_id": 1, "x": "to_delete"}],
        ops=[lambda c, s: c.delete_one({"_id": 1}, session=s)],
        expected=[],
        msg="commitTransaction should persist the deletion",
    ),
    SessionTestCase(
        "commit_multi_operation",
        docs=[{"_id": 1, "x": "original"}],
        ops=[
            lambda c, s: c.insert_one({"_id": 2, "x": "new"}, session=s),
            lambda c, s: c.update_one({"_id": 1}, {"$set": {"x": "modified"}}, session=s),
        ],
        expected=[{"_id": 1, "x": "modified"}, {"_id": 2, "x": "new"}],
        msg="commitTransaction should persist all operations from a multi-op transaction",
    ),
    # Property [Commit with writeConcern]: explicit writeConcern is accepted.
    SessionTestCase(
        "commit_with_writeconcern",
        docs=[{"_id": 1, "x": "before"}],
        ops=[lambda c, s: c.update_one({"_id": 1}, {"$set": {"x": "after"}}, session=s)],
        commit_command={"commitTransaction": 1, "writeConcern": {"w": 1}},
        expected=[{"_id": 1, "x": "after"}],
        msg="commitTransaction with writeConcern should persist changes",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMIT_PERSISTENCE_TESTS))
def test_commitTransaction_persistence(collection, test):
    """Test commitTransaction persists operations."""
    if test.docs:
        collection.insert_many(test.docs)
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        for op in test.ops:
            op(collection, session)
        if test.commit_command is not None:
            execute_admin_command(collection, test.commit_command, session=session)
        else:
            session.commit_transaction()
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(result, test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [Empty Transaction]: committing a transaction with no ops succeeds.
# ---------------------------------------------------------------------------

EMPTY_TRANSACTION_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "commit_empty_transaction",
        ops=[],
        msg="commitTransaction on empty transaction should not error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EMPTY_TRANSACTION_TESTS))
def test_commitTransaction_empty(collection, test):
    """Test commitTransaction succeeds on an empty transaction."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        session.commit_transaction()
    result = execute_command(collection, {"find": collection.name, "filter": {}})
    assertNotError(result, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [Response Structure]: commit response contains ok:1 on success.
# ---------------------------------------------------------------------------

RESPONSE_STRUCTURE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "commit_response_ok",
        ops=[lambda c, s: c.insert_one({"_id": 1}, session=s)],
        commit_command={"commitTransaction": 1},
        expected_response={"ok": 1.0},
        msg="commitTransaction response should have ok:1 on success",
    ),
    # Property [Commit with comment]: comment parameter is accepted.
    SessionTestCase(
        "commit_with_comment",
        ops=[lambda c, s: c.insert_one({"_id": 1}, session=s)],
        commit_command={"commitTransaction": 1, "comment": "test commit"},
        expected_response={"ok": 1.0},
        msg="commitTransaction with comment should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_STRUCTURE_TESTS))
def test_commitTransaction_response(collection, test):
    """Test commitTransaction returns expected response fields."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        for op in test.ops:
            op(collection, session)
        result = execute_admin_command(collection, test.commit_command, session=session)
    assertSuccessPartial(result, test.expected_response, msg=test.msg)
