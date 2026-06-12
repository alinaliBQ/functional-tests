"""Tests for setQuerySettings command settings configurations.

Validates that the setQuerySettings command accepts valid settings
combinations including indexHints, reject, queryFramework, and comment
fields, as well as allowedIndexes variations and update behavior.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.setQuerySettings_common import cleanup_query_settings

# -- helpers ------------------------------------------------------------------


def _index_hints(ctx: CommandContext, allowed=None):
    """Build a standard indexHints array for the fixture collection."""
    return [
        {
            "ns": {"db": ctx.database, "coll": ctx.collection},
            "allowedIndexes": allowed or ["_id_"],
        }
    ]


# Property [indexHints Acceptance]: setQuerySettings accepts valid indexHints configurations.
# Property [reject Acceptance]: setQuerySettings accepts reject: true alone or with indexHints.
# Property [queryFramework Acceptance]: setQuerySettings accepts classic and sbe frameworks.
# Property [comment Acceptance]: setQuerySettings accepts the comment field.
# Property [Combined Settings]: setQuerySettings accepts all settings fields together.
SET_QUERY_SETTINGS_SETTINGS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "indexHints_single_index",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a1": 1},
                "$db": ctx.database,
            },
            "settings": {"indexHints": _index_hints(ctx)},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a1": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept indexHints with single index",
    ),
    CommandTestCase(
        "indexHints_multiple_indexes",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a2": 1},
                "$db": ctx.database,
            },
            "settings": {"indexHints": _index_hints(ctx, ["_id_", {"a2": 1}])},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a2": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept multiple indexes",
    ),
    CommandTestCase(
        "indexHints_key_pattern",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a3": 1},
                "$db": ctx.database,
            },
            "settings": {"indexHints": _index_hints(ctx, [{"a3": 1}])},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a3": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept indexHints with key pattern",
    ),
    CommandTestCase(
        "reject_true",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a5": 1},
                "$db": ctx.database,
            },
            "settings": {"reject": True},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a5": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept settings with reject: true",
    ),
    CommandTestCase(
        "reject_with_indexHints",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a6": 1},
                "$db": ctx.database,
            },
            "settings": {"indexHints": _index_hints(ctx), "reject": True},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a6": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept reject with indexHints",
    ),
    CommandTestCase(
        "queryFramework_classic",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a7": 1},
                "$db": ctx.database,
            },
            "settings": {"indexHints": _index_hints(ctx), "queryFramework": "classic"},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a7": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept queryFramework: classic",
    ),
    CommandTestCase(
        "queryFramework_sbe",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a8": 1},
                "$db": ctx.database,
            },
            "settings": {"indexHints": _index_hints(ctx), "queryFramework": "sbe"},
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a8": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept queryFramework: sbe",
    ),
    CommandTestCase(
        "with_comment_string",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a9": 1},
                "$db": ctx.database,
            },
            "settings": {"indexHints": _index_hints(ctx)},
            "comment": "test comment for setQuerySettings",
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a9": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept command with comment string",
    ),
    CommandTestCase(
        "all_settings_combined",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"a12": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": _index_hints(ctx),
                "queryFramework": "classic",
                "reject": True,
            },
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"a12": 1},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept all settings combined",
    ),
]


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_SETTINGS_TESTS))
def test_setQuerySettings_settings(collection, test):
    """Test setQuerySettings accepts valid settings configurations."""
    ctx = CommandContext.from_collection(collection)
    try:
        result = execute_admin_command(collection, test.build_command(ctx))
        assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)
    finally:
        for cmd in test.build_cleanup(ctx):
            try:
                execute_admin_command(collection, cmd)
            except Exception:
                pass


# -- Update Behavior tests (multi-step, kept as individual functions) ---------


# Property [Update Behavior]: setQuerySettings can update existing settings by query or hash.
@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_update_existing_settings(collection):
    """Test setQuerySettings can update settings for an existing query shape."""
    ctx = CommandContext.from_collection(collection)
    query = {
        "find": ctx.collection,
        "filter": {"a10": 1},
        "$db": ctx.database,
    }
    try:
        # Setup: create initial settings (no assertion — setup only)
        execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {"indexHints": _index_hints(ctx)},
            },
        )

        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {"indexHints": _index_hints(ctx, ["_id_", {"a10": 1}])},
            },
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="update setQuerySettings should succeed")
    finally:
        cleanup_query_settings(collection, [query])


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_update_via_hash(collection):
    """Test setQuerySettings can update settings using the query shape hash."""
    ctx = CommandContext.from_collection(collection)
    query = {
        "find": ctx.collection,
        "filter": {"a11": 1},
        "$db": ctx.database,
    }
    try:
        # Setup: create initial settings and capture hash (no assertion — setup only)
        setup_result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query,
                "settings": {"indexHints": _index_hints(ctx)},
            },
        )

        query_hash = setup_result.get("queryShapeHash")
        result = execute_admin_command(
            collection,
            {
                "setQuerySettings": query_hash,
                "settings": {"indexHints": _index_hints(ctx, ["_id_", {"a11": 1}])},
            },
        )
        assertSuccessPartial(result, {"ok": 1.0}, msg="update via hash should succeed")
    finally:
        cleanup_query_settings(collection, [query])
