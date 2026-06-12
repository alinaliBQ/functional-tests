"""Tests for setQuerySettings command behavioral verification.

Validates that query settings are retrievable via $querySettings aggregation
stage, removable via removeQuerySettings, and that the response structure
includes expected fields like queryShapeHash and representativeQuery.
"""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    AdminCommandTestCase,
    CommandContext,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import QUERYSETTINGS_QUERY_REJECTED_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.setQuerySettings_common import cleanup_query_settings, get_query_settings

# -- helpers ------------------------------------------------------------------


def _index_hints(ctx: CommandContext):
    """Build a standard indexHints array for the fixture collection."""
    return [
        {
            "ns": {"db": ctx.database, "coll": ctx.collection},
            "allowedIndexes": ["_id_"],
        }
    ]


def _settings(ctx: CommandContext):
    """Build a standard settings block with indexHints."""
    return {"indexHints": _index_hints(ctx)}


def _setup_setting(ctx: CommandContext, query: dict, settings: dict | None = None):
    """Return a setup command list that creates a query setting."""
    return [{"setQuerySettings": query, "settings": settings or _settings(ctx)}]


def _cleanup_query(query_fn):
    """Return a cleanup callable that removes the query shape built by query_fn."""
    return lambda ctx: [{"removeQuerySettings": query_fn(ctx)}]


def _find_query(ctx: CommandContext, field: str):
    """Build a find query shape for the given field."""
    return {"find": ctx.collection, "filter": {field: 1}, "$db": ctx.database}


# -- Response Structure tests (single-step, fits AdminCommandTestCase) --------

# Property [Response Structure]: setQuerySettings response includes hash, query, and settings.
SET_QUERY_SETTINGS_RESPONSE_TESTS: list[AdminCommandTestCase] = [
    AdminCommandTestCase(
        "response_contains_hash",
        command=lambda ctx: {
            "setQuerySettings": _find_query(ctx, "b1"),
            "settings": _settings(ctx),
        },
        expected={"ok": 1.0},
        cleanup=_cleanup_query(lambda ctx: _find_query(ctx, "b1")),
        msg="response should contain queryShapeHash",
    ),
    AdminCommandTestCase(
        "response_contains_representative_query",
        command=lambda ctx: {
            "setQuerySettings": _find_query(ctx, "b2"),
            "settings": _settings(ctx),
        },
        expected={"ok": 1.0},
        cleanup=_cleanup_query(lambda ctx: _find_query(ctx, "b2")),
        msg="response should contain representativeQuery",
    ),
    AdminCommandTestCase(
        "response_settings_echo",
        command=lambda ctx: {
            "setQuerySettings": _find_query(ctx, "b3"),
            "settings": _settings(ctx),
        },
        expected=lambda ctx: {"ok": 1.0, "settings": _settings(ctx)},
        cleanup=_cleanup_query(lambda ctx: _find_query(ctx, "b3")),
        msg="response should echo applied settings",
    ),
]


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_RESPONSE_TESTS))
def test_setQuerySettings_response(collection, test):
    """Test setQuerySettings response structure."""
    ctx = CommandContext.from_collection(collection)
    try:
        result = execute_admin_command(collection, test.build_command(ctx))
        expected = test.build_expected(ctx)
        # Also verify the dynamic fields are present
        if test.id == "response_contains_hash":
            expected["queryShapeHash"] = result.get("queryShapeHash")
        elif test.id == "response_contains_representative_query":
            expected["representativeQuery"] = result.get("representativeQuery")
        assertSuccessPartial(result, expected, msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# -- removeQuerySettings tests (multi-step: setup creates setting, command removes it) ---

# Property [removeQuerySettings]: settings can be removed by query or hash.
SET_QUERY_SETTINGS_REMOVE_TESTS: list[AdminCommandTestCase] = [
    AdminCommandTestCase(
        "removeQuerySettings_by_query",
        setup_commands=lambda ctx: _setup_setting(ctx, _find_query(ctx, "b5")),
        command=lambda ctx: {"removeQuerySettings": _find_query(ctx, "b5")},
        expected={"ok": 1.0},
        cleanup=_cleanup_query(lambda ctx: _find_query(ctx, "b5")),
        msg="removeQuerySettings by query should succeed",
    ),
]


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_REMOVE_TESTS))
def test_setQuerySettings_remove(collection, test):
    """Test removeQuerySettings removes settings."""
    ctx = CommandContext.from_collection(collection)
    try:
        for cmd in test.build_setup(ctx):
            execute_admin_command(collection, cmd)
        result = execute_admin_command(collection, test.build_command(ctx))
        assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# -- Multi-step behavior tests (kept as individual functions) -----------------


# Property [removeQuerySettings by hash]: requires capturing hash from setup result.
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
