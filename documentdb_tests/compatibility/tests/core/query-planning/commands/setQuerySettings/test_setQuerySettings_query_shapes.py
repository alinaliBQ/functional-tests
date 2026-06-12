"""Tests for setQuerySettings command query shape acceptance.

Validates that the setQuerySettings command accepts valid query shapes for
find, distinct, and aggregate commands, including various shape variations,
field combinations, and $db field variations.
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

# -- helpers ------------------------------------------------------------------


def _index_hints(ctx: CommandContext, db=None, coll=None):
    """Build a standard indexHints array, optionally overriding db/coll."""
    return [
        {
            "ns": {"db": db or ctx.database, "coll": coll or ctx.collection},
            "allowedIndexes": ["_id_"],
        }
    ]


def _settings(ctx: CommandContext, db=None, coll=None):
    """Build a standard settings block with indexHints."""
    return {"indexHints": _index_hints(ctx, db=db, coll=coll)}


def _cleanup(query: dict):
    """Return a cleanup callable that removes the given query shape."""
    return lambda ctx: [{"removeQuerySettings": query}]


# -- test case helpers --------------------------------------------------------


def _find_case(tid, query_fn, msg):
    """Build an CommandTestCase for a find query shape."""
    return CommandTestCase(
        tid,
        command=lambda ctx, qf=query_fn: {
            "setQuerySettings": qf(ctx),
            "settings": _settings(ctx),
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx, qf=query_fn: [{"removeQuerySettings": qf(ctx)}],
        msg=msg,
    )


# Property [Command Shape Acceptance]: accepts find, distinct, and aggregate shapes.
# Property [Find Shape Variations]: setQuerySettings accepts find shapes with various field combos.
# Property [Distinct Shape Variations]: setQuerySettings accepts distinct shapes with query combos.
# Property [Aggregate Shape Variations]: setQuerySettings accepts aggregate pipeline shapes.
# Property [$db Field Variations]: setQuerySettings accepts non-existent and special-char db names.
SET_QUERY_SETTINGS_QUERY_SHAPE_TESTS: list[CommandTestCase] = [
    # -- Command shape acceptance --
    _find_case(
        "find_shape",
        lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": 1},
            "sort": {"x": 1},
            "$db": ctx.database,
        },
        msg="should accept valid find shape",
    ),
    CommandTestCase(
        "distinct_shape",
        command=lambda ctx: {
            "setQuerySettings": {
                "distinct": ctx.collection,
                "key": "x",
                "query": {"x": {"$gt": 0}},
                "$db": ctx.database,
            },
            "settings": _settings(ctx),
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "distinct": ctx.collection,
                    "key": "x",
                    "query": {"x": {"$gt": 0}},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept valid distinct shape",
    ),
    CommandTestCase(
        "aggregate_shape",
        command=lambda ctx: {
            "setQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"x": 1}}],
                "$db": ctx.database,
            },
            "settings": _settings(ctx),
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "aggregate": ctx.collection,
                    "pipeline": [{"$match": {"x": 1}}],
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept valid aggregate shape",
    ),
    # -- Find shape variations --
    _find_case(
        "find_filter_only",
        lambda ctx: {"find": ctx.collection, "filter": {"a": 1}, "$db": ctx.database},
        msg="should accept find with filter only",
    ),
    _find_case(
        "find_filter_sort",
        lambda ctx: {
            "find": ctx.collection,
            "filter": {"b": 1},
            "sort": {"b": 1},
            "$db": ctx.database,
        },
        msg="should accept find with filter+sort",
    ),
    _find_case(
        "find_filter_projection",
        lambda ctx: {
            "find": ctx.collection,
            "filter": {"c": 1},
            "projection": {"c": 1},
            "$db": ctx.database,
        },
        msg="should accept find with filter+projection",
    ),
    _find_case(
        "find_filter_sort_projection",
        lambda ctx: {
            "find": ctx.collection,
            "filter": {"d": 1},
            "sort": {"d": 1},
            "projection": {"d": 1},
            "$db": ctx.database,
        },
        msg="should accept find with all fields",
    ),
    _find_case(
        "find_with_collation",
        lambda ctx: {
            "find": ctx.collection,
            "filter": {"e": "abc"},
            "collation": {"locale": "en", "strength": 2},
            "$db": ctx.database,
        },
        msg="should accept find with collation",
    ),
    _find_case(
        "find_with_let",
        lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$eq": ["$f", "$$target"]}},
            "let": {"target": 1},
            "$db": ctx.database,
        },
        msg="should accept find with let",
    ),
    _find_case(
        "find_with_limit",
        lambda ctx: {
            "find": ctx.collection,
            "filter": {"g": 1},
            "limit": 10,
            "$db": ctx.database,
        },
        msg="should accept find with limit",
    ),
    # -- Distinct shape variations --
    CommandTestCase(
        "distinct_key_only",
        command=lambda ctx: {
            "setQuerySettings": {
                "distinct": ctx.collection,
                "key": "j",
                "$db": ctx.database,
            },
            "settings": _settings(ctx),
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "distinct": ctx.collection,
                    "key": "j",
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept distinct key only",
    ),
    CommandTestCase(
        "distinct_complex_query",
        command=lambda ctx: {
            "setQuerySettings": {
                "distinct": ctx.collection,
                "key": "k",
                "query": {"$and": [{"k": {"$gt": 0}}, {"k": {"$lt": 100}}]},
                "$db": ctx.database,
            },
            "settings": _settings(ctx),
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "distinct": ctx.collection,
                    "key": "k",
                    "query": {"$and": [{"k": {"$gt": 0}}, {"k": {"$lt": 100}}]},
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept distinct complex query",
    ),
    # -- Aggregate shape variations --
    CommandTestCase(
        "aggregate_match_only",
        command=lambda ctx: {
            "setQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"l": 1}}],
                "$db": ctx.database,
            },
            "settings": _settings(ctx),
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "aggregate": ctx.collection,
                    "pipeline": [{"$match": {"l": 1}}],
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept aggregate $match only",
    ),
    CommandTestCase(
        "aggregate_match_group",
        command=lambda ctx: {
            "setQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [
                    {"$match": {"m": 1}},
                    {"$group": {"_id": "$m", "count": {"$sum": 1}}},
                ],
                "$db": ctx.database,
            },
            "settings": _settings(ctx),
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "aggregate": ctx.collection,
                    "pipeline": [
                        {"$match": {"m": 1}},
                        {"$group": {"_id": "$m", "count": {"$sum": 1}}},
                    ],
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept aggregate $match+$group",
    ),
    CommandTestCase(
        "aggregate_match_sort_limit",
        command=lambda ctx: {
            "setQuerySettings": {
                "aggregate": ctx.collection,
                "pipeline": [{"$match": {"n": 1}}, {"$sort": {"n": 1}}, {"$limit": 5}],
                "$db": ctx.database,
            },
            "settings": _settings(ctx),
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "aggregate": ctx.collection,
                    "pipeline": [{"$match": {"n": 1}}, {"$sort": {"n": 1}}, {"$limit": 5}],
                    "$db": ctx.database,
                }
            }
        ],
        msg="should accept aggregate $match+$sort+$limit",
    ),
    # -- $db field variations --
    CommandTestCase(
        "db_nonexistent",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"o": 1},
                "$db": "nonexistent_db_for_query_settings_test",
            },
            "settings": _settings(ctx, db="nonexistent_db_for_query_settings_test"),
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"o": 1},
                    "$db": "nonexistent_db_for_query_settings_test",
                }
            }
        ],
        msg="should accept non-existent $db",
    ),
    CommandTestCase(
        "db_special_characters",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"p": 1},
                "$db": "test-special-db",
            },
            "settings": _settings(ctx, db="test-special-db"),
        },
        expected={"ok": 1.0},
        cleanup=lambda ctx: [
            {
                "removeQuerySettings": {
                    "find": ctx.collection,
                    "filter": {"p": 1},
                    "$db": "test-special-db",
                }
            }
        ],
        msg="should accept $db with special chars",
    ),
]


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_QUERY_SHAPE_TESTS))
def test_setQuerySettings_query_shapes(collection, test):
    """Test setQuerySettings accepts valid query shapes."""
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
