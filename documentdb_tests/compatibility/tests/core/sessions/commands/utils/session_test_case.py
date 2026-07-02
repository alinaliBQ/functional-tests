"""Shared test case model for session command tests.

Provides ``SessionTestCase``, the data model used by session command success
tests (e.g. commitTransaction). The transaction lifecycle itself is written
inline in each test function so the full flow — seed, start transaction, run
operations, commit, read back — is visible at the call site rather than hidden
behind a runner.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pymongo.client_session import ClientSession
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)


@dataclass(frozen=True)
class SessionTestCase(CommandTestCase):
    """Test case for session command success tests (e.g. commitTransaction).

    Extends ``CommandTestCase`` with the fields needed to model a transaction
    workflow.

    Attributes:
        ops: Operations to run inside the transaction before committing. Each
            is a callable ``(collection, session)`` that issues a single
            pymongo write within the session, e.g.
            ``lambda c, s: c.insert_one({"_id": 1}, session=s)``. Writing the
            operation inline keeps the exact call visible at the test-case site.
        commit_command: Optional raw command dict for committing (e.g. to
            include writeConcern or comment). When None, the test commits via
            ``session.commit_transaction()``.
        expected_response: Expected fields from the commit command response,
            for tests that assert on the commit response rather than on a
            post-commit readback.
    """

    ops: list[Callable[[Collection, ClientSession], Any]] = field(default_factory=list)
    commit_command: dict[str, Any] | None = None
    expected_response: dict[str, Any] | None = None
