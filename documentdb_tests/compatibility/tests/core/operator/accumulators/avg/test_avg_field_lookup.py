"""
Tests for $avg accumulator expression types and field lookup in $group context.

Covers expression types (literal, field path, computed expressions, system variables)
and field path resolution (simple, nested, missing, array traversal).
"""

from __future__ import annotations

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# --- Helpers ---


def _group_avg(collection, docs, avg_expr="$value"):
    """Insert docs and run $group with $avg on given expression."""
    collection.insert_many(docs)
    return execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "avg": {"$avg": avg_expr}}},
            ],
            "cursor": {},
        },
    )


# --- 11. Expression Types (per-operator) ---


def test_avg_group_field_path(collection):
    """Test $avg with simple field path expression in $group."""
    result = _group_avg(
        collection,
        [
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
        ],
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="$avg with field path should average field values",
    )


def test_avg_group_computed_expression(collection):
    """Test $avg with computed expression in $group."""
    collection.insert_many(
        [
            {"_id": 1, "a": 2, "b": 3},
            {"_id": 2, "a": 4, "b": 6},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "avg": {"$avg": {"$multiply": ["$a", "$b"]}}}},
            ],
            "cursor": {},
        },
    )
    # (2*3 + 4*6) / 2 = (6 + 24) / 2 = 15
    assertSuccess(
        result,
        [{"_id": None, "avg": 15.0}],
        msg="$avg with computed expression should average computed values",
    )


def test_avg_group_literal_numeric(collection):
    """Test $avg with literal numeric value in $group returns that constant."""
    collection.insert_many(
        [
            {"_id": 1},
            {"_id": 2},
            {"_id": 3},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "avg": {"$avg": 5}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": 5.0}],
        msg="$avg with literal numeric should return that constant",
    )


def test_avg_group_literal_null(collection):
    """Test $avg with null literal in $group returns null."""
    collection.insert_many([{"_id": 1}, {"_id": 2}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "avg": {"$avg": None}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": None}],
        msg="$avg with null literal should return null",
    )


def test_avg_group_cond_expression(collection):
    """Test $avg with $cond expression in $group."""
    collection.insert_many(
        [
            {"_id": 1, "value": 10, "include": True},
            {"_id": 2, "value": 20, "include": False},
            {"_id": 3, "value": 30, "include": True},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "avg": {
                            "$avg": {
                                "$cond": [
                                    "$include",
                                    "$value",
                                    None,
                                ]
                            }
                        },
                    }
                },
            ],
            "cursor": {},
        },
    )
    # Only values 10 and 30 contribute (null is ignored), avg = 20
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="$avg with $cond should average only non-null conditional results",
    )


def test_avg_group_ifnull_expression(collection):
    """Test $avg with $ifNull expression replacing missing values."""
    collection.insert_many(
        [
            {"_id": 1, "value": 10},
            {"_id": 2},
            {"_id": 3, "value": 30},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "avg": {"$avg": {"$ifNull": ["$value", 0]}},
                    }
                },
            ],
            "cursor": {},
        },
    )
    # (10 + 0 + 30) / 3 = 13.333...
    assertSuccess(
        result,
        [{"_id": None, "avg": 13.333333333333334}],
        msg="$avg with $ifNull should replace missing with 0",
    )


# --- 12. Field Lookup ---


def test_avg_group_nested_field_path(collection):
    """Test $avg with nested field path in $group."""
    result = _group_avg(
        collection,
        [
            {"_id": 1, "nested": {"value": 10}},
            {"_id": 2, "nested": {"value": 20}},
            {"_id": 3, "nested": {"value": 30}},
        ],
        avg_expr="$nested.value",
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="$avg with nested field path should resolve and average",
    )


def test_avg_group_missing_field(collection):
    """Test $avg with non-existent field path returns null."""
    result = _group_avg(
        collection,
        [
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
        ],
        avg_expr="$nonexistent",
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": None}],
        msg="$avg with non-existent field should return null",
    )


def test_avg_group_some_missing_field(collection):
    """Test $avg where some documents have the field and others don't."""
    result = _group_avg(
        collection,
        [
            {"_id": 1, "value": 10},
            {"_id": 2},
            {"_id": 3, "value": 30},
        ],
    )
    # Missing values are ignored: (10 + 30) / 2 = 20
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="$avg should ignore documents with missing field",
    )


def test_avg_group_field_resolves_to_array(collection):
    """Test $avg where field resolves to an array in $group — treated as non-numeric."""
    result = _group_avg(
        collection,
        [
            {"_id": 1, "value": [1, 2, 3]},
            {"_id": 2, "value": [4, 5, 6]},
        ],
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": None}],
        msg="$avg in $group should treat array values as non-numeric",
    )


def test_avg_group_mixed_array_and_numeric(collection):
    """Test $avg where some docs have arrays and others have numerics."""
    result = _group_avg(
        collection,
        [
            {"_id": 1, "value": [1, 2, 3]},
            {"_id": 2, "value": 10},
            {"_id": 3, "value": 20},
        ],
    )
    # Array is ignored: (10 + 20) / 2 = 15
    assertSuccess(
        result,
        [{"_id": None, "avg": 15.0}],
        msg="$avg in $group should ignore array values and average numerics",
    )


def test_avg_group_deeply_nested_path(collection):
    """Test $avg with deeply nested field path."""
    result = _group_avg(
        collection,
        [
            {"_id": 1, "a": {"b": {"c": {"d": 10}}}},
            {"_id": 2, "a": {"b": {"c": {"d": 20}}}},
        ],
        avg_expr="$a.b.c.d",
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": 15.0}],
        msg="$avg with deeply nested path should resolve correctly",
    )


def test_avg_group_intermediate_null(collection):
    """Test $avg where intermediate field in path is null."""
    result = _group_avg(
        collection,
        [
            {"_id": 1, "a": {"b": 10}},
            {"_id": 2, "a": None},
            {"_id": 3, "a": {"b": 30}},
        ],
        avg_expr="$a.b",
    )
    # Doc 2 has null intermediate, treated as missing: (10 + 30) / 2 = 20
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="$avg should treat null intermediate as missing",
    )


def test_avg_group_multiple_accumulators(collection):
    """Test multiple $avg accumulators in same $group stage."""
    collection.insert_many(
        [
            {"_id": 1, "a": 10, "b": 100},
            {"_id": 2, "a": 20, "b": 200},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "avg_a": {"$avg": "$a"},
                        "avg_b": {"$avg": "$b"},
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": None, "avg_a": 15.0, "avg_b": 150.0}],
        msg="Multiple $avg accumulators should work independently",
    )
