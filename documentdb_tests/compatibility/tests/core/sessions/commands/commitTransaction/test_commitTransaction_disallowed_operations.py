"""Tests for operations that are not supported inside a transaction.

Which operation types may run inside a transaction is its own concern (kept out
of the behavioral files). Several commands are rejected with
OperationNotSupportedInTransaction when issued inside an active transaction, as
are writes to a capped collection or to a system database. Each test issues the
operation in the transaction and asserts the rejection; the session is closed by
its ``with`` block.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


# Commands rejected inside a transaction with OperationNotSupportedInTransaction.
DISALLOWED_COMMANDS: list[CommandTestCase] = [
    CommandTestCase(
        "count",
        command=lambda ctx: {"count": ctx.collection},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="count command is not supported inside a transaction",
    ),
    CommandTestCase(
        "listCollections",
        command={"listCollections": 1},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="listCollections is not supported inside a transaction",
    ),
    CommandTestCase(
        "listIndexes",
        command=lambda ctx: {"listIndexes": ctx.collection},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="listIndexes is not supported inside a transaction",
    ),
    CommandTestCase(
        "explain",
        command=lambda ctx: {"explain": {"find": ctx.collection}},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="explain is not supported inside a transaction",
    ),
    CommandTestCase(
        "createUser",
        command={"createUser": "commit_txn_user", "pwd": "commit_txn_pwd", "roles": []},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="createUser is not supported inside a transaction",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DISALLOWED_COMMANDS))
def test_command_disallowed_in_transaction(collection, test):
    """Commands not supported inside a transaction are rejected."""
    collection.insert_one({"_id": 1})
    ctx = CommandContext.from_collection(collection)
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(collection, test.build_command(ctx), session=session)
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_write_to_capped_collection_disallowed_in_transaction(collection):
    """Writing to a capped collection inside a transaction is not supported."""
    capped = collection.database.create_collection(
        f"{collection.name}_capped", capped=True, size=4096
    )
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection,
            {"insert": capped.name, "documents": [{"_id": 1}]},
            session=session,
        )
    assertFailureCode(result, OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR)


@pytest.mark.parametrize("system_db_name", ["config", "local"])
def test_write_to_system_database_disallowed_in_transaction(collection, system_db_name):
    """Writing to a system database inside a transaction is not supported."""
    client = collection.database.client
    system_collection = client[system_db_name][f"{collection.name}_probe"]
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            system_collection,
            {"insert": system_collection.name, "documents": [{"_id": 1}]},
            session=session,
        )
    assertFailureCode(result, OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR)
