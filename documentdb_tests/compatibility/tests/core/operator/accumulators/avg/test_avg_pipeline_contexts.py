"""
Tests for $avg in various pipeline contexts.

Covers $group, $bucket, $setWindowFields, $project/$addFields,
$match+$expr, and pipeline interaction patterns.
"""

from __future__ import annotations

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# --- 14. Pipeline Contexts ---

# -- $group with computed _id --


def test_avg_group_computed_id(collection):
    """Test $avg with computed _id expression in $group."""
    collection.insert_many(
        [
            {"_id": 1, "value": 10, "score": 80},
            {"_id": 2, "value": 20, "score": 90},
            {"_id": 3, "value": 30, "score": 85},
            {"_id": 4, "value": 40, "score": 95},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": {"$gt": ["$score", 85]},
                        "avg": {"$avg": "$value"},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    # score <= 85: docs 1,3 → avg(10,30) = 20
    # score > 85: docs 2,4 → avg(20,40) = 30
    assertSuccess(
        result,
        [
            {"_id": False, "avg": 20.0},
            {"_id": True, "avg": 30.0},
        ],
        msg="$avg with computed _id should group and average correctly",
    )


# -- $bucket --


def test_avg_bucket(collection):
    """Test $avg in $bucket output specification."""
    collection.insert_many(
        [
            {"_id": 1, "score": 15, "value": 10},
            {"_id": 2, "score": 25, "value": 20},
            {"_id": 3, "score": 35, "value": 30},
            {"_id": 4, "score": 45, "value": 40},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$bucket": {
                        "groupBy": "$score",
                        "boundaries": [0, 20, 40, 60],
                        "output": {"avg_value": {"$avg": "$value"}},
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 0, "avg_value": 10.0},
            {"_id": 20, "avg_value": 25.0},
            {"_id": 40, "avg_value": 40.0},
        ],
        msg="$avg in $bucket should compute average per bucket",
    )


# -- $setWindowFields --


def test_avg_window_unbounded(collection):
    """Test $avg with unbounded window returns partition average."""
    collection.insert_many(
        [
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {
                            "avg": {
                                "$avg": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
                {"$project": {"_id": 1, "value": 1, "avg": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "value": 10, "avg": 20.0},
            {"_id": 2, "value": 20, "avg": 20.0},
            {"_id": 3, "value": 30, "avg": 20.0},
        ],
        msg="$avg with unbounded window should return full partition average",
    )


def test_avg_window_cumulative(collection):
    """Test $avg with cumulative window [unbounded, current]."""
    collection.insert_many(
        [
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {
                            "avg": {
                                "$avg": "$value",
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                },
                {"$project": {"_id": 1, "value": 1, "avg": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "value": 10, "avg": 10.0},
            {"_id": 2, "value": 20, "avg": 15.0},
            {"_id": 3, "value": 30, "avg": 20.0},
        ],
        msg="$avg with cumulative window should compute running average",
    )


def test_avg_window_sliding(collection):
    """Test $avg with sliding window [-1, 1]."""
    collection.insert_many(
        [
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
            {"_id": 4, "value": 40},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {
                            "avg": {
                                "$avg": "$value",
                                "window": {"documents": [-1, 1]},
                            }
                        },
                    }
                },
                {"$project": {"_id": 1, "value": 1, "avg": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "value": 10, "avg": 15.0},  # avg(10,20)
            {"_id": 2, "value": 20, "avg": 20.0},  # avg(10,20,30)
            {"_id": 3, "value": 30, "avg": 30.0},  # avg(20,30,40)
            {"_id": 4, "value": 40, "avg": 35.0},  # avg(30,40)
        ],
        msg="$avg with sliding window should compute local average",
    )


def test_avg_window_current_only(collection):
    """Test $avg with window [0, 0] returns current document value."""
    collection.insert_many(
        [
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {
                            "avg": {
                                "$avg": "$value",
                                "window": {"documents": [0, 0]},
                            }
                        },
                    }
                },
                {"$project": {"_id": 1, "value": 1, "avg": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "value": 10, "avg": 10.0},
            {"_id": 2, "value": 20, "avg": 20.0},
            {"_id": 3, "value": 30, "avg": 30.0},
        ],
        msg="$avg with [0,0] window should return current document value",
    )


def test_avg_window_with_nulls(collection):
    """Test $avg in $setWindowFields ignores null values in window."""
    collection.insert_many(
        [
            {"_id": 1, "value": 10},
            {"_id": 2, "value": None},
            {"_id": 3, "value": 30},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {
                            "avg": {
                                "$avg": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
                {"$project": {"_id": 1, "value": 1, "avg": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "value": 10, "avg": 20.0},
            {"_id": 2, "value": None, "avg": 20.0},
            {"_id": 3, "value": 30, "avg": 20.0},
        ],
        msg="$avg in window should ignore null values",
    )


# -- $project / $addFields context --


def test_avg_in_project_array_literal(collection):
    """Test $avg in $project with array of literal values."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {"$project": {"_id": 0, "avg": {"$avg": [10, 20, 30]}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"avg": 20.0}],
        msg="$avg in $project with literal array should average values",
    )


def test_avg_in_addfields(collection):
    """Test $avg in $addFields context."""
    collection.insert_many(
        [
            {"_id": 1, "scores": [80, 90, 100]},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"avg_score": {"$avg": "$scores"}}},
                {"$project": {"_id": 0, "avg_score": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"avg_score": 90.0}],
        msg="$avg in $addFields should traverse array field and average",
    )


def test_avg_in_match_expr(collection):
    """Test $avg used inside $expr in $match stage."""
    collection.insert_many(
        [
            {"_id": 1, "scores": [80, 90, 100]},
            {"_id": 2, "scores": [40, 50, 60]},
            {"_id": 3, "scores": [70, 80, 90]},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$expr": {"$gt": [{"$avg": "$scores"}, 75]}}},
                {"$project": {"_id": 1}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    # avg([80,90,100])=90 > 75 ✓, avg([40,50,60])=50 < 75 ✗, avg([70,80,90])=80 > 75 ✓
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 3}],
        msg="$avg in $match $expr should filter based on computed average",
    )


# --- 19. Pipeline Interaction ---


def test_avg_bucketauto(collection):
    """Test $avg in $bucketAuto output specification."""
    collection.insert_many(
        [
            {"_id": 1, "score": 10, "value": 100},
            {"_id": 2, "score": 20, "value": 200},
            {"_id": 3, "score": 30, "value": 300},
            {"_id": 4, "score": 40, "value": 400},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$bucketAuto": {
                        "groupBy": "$score",
                        "buckets": 2,
                        "output": {"avg_value": {"$avg": "$value"}},
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": {"min": 10, "max": 30}, "avg_value": 150.0},
            {"_id": {"min": 30, "max": 40}, "avg_value": 350.0},
        ],
        msg="$avg in $bucketAuto should compute average per auto-bucket",
    )


def test_avg_window_range_based(collection):
    """Test $avg with range-based window on numeric sort key."""
    collection.insert_many(
        [
            {"_id": 1, "pos": 0, "value": 10},
            {"_id": 2, "pos": 5, "value": 20},
            {"_id": 3, "pos": 10, "value": 30},
            {"_id": 4, "pos": 15, "value": 40},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"pos": 1}},
                {
                    "$setWindowFields": {
                        "sortBy": {"pos": 1},
                        "output": {
                            "avg": {
                                "$avg": "$value",
                                "window": {"range": [-5, 5]},
                            }
                        },
                    }
                },
                {"$project": {"_id": 1, "pos": 1, "value": 1, "avg": 1}},
            ],
            "cursor": {},
        },
    )
    # pos=0: range [-5,5] includes pos 0,5 → avg(10,20)=15
    # pos=5: range [0,10] includes pos 0,5,10 → avg(10,20,30)=20
    # pos=10: range [5,15] includes pos 5,10,15 → avg(20,30,40)=30
    # pos=15: range [10,20] includes pos 10,15 → avg(30,40)=35
    assertSuccess(
        result,
        [
            {"_id": 1, "pos": 0, "value": 10, "avg": 15.0},
            {"_id": 2, "pos": 5, "value": 20, "avg": 20.0},
            {"_id": 3, "pos": 10, "value": 30, "avg": 30.0},
            {"_id": 4, "pos": 15, "value": 40, "avg": 35.0},
        ],
        msg="$avg with range-based window should compute average within range",
    )


def test_avg_window_multiple_partitions(collection):
    """Test $avg in $setWindowFields with multiple partitions of different sizes."""
    collection.insert_many(
        [
            {"_id": 1, "group": "A", "value": 10},
            {"_id": 2, "group": "A", "value": 20},
            {"_id": 3, "group": "A", "value": 30},
            {"_id": 4, "group": "B", "value": 100},
            {"_id": 5, "group": "B", "value": 200},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$setWindowFields": {
                        "partitionBy": "$group",
                        "sortBy": {"_id": 1},
                        "output": {
                            "avg": {
                                "$avg": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
                {"$project": {"_id": 1, "group": 1, "avg": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "group": "A", "avg": 20.0},
            {"_id": 2, "group": "A", "avg": 20.0},
            {"_id": 3, "group": "A", "avg": 20.0},
            {"_id": 4, "group": "B", "avg": 150.0},
            {"_id": 5, "group": "B", "avg": 150.0},
        ],
        msg="$avg should compute independent averages per partition",
    )


def test_avg_group_after_unwind(collection):
    """Test $avg in $group after $unwind averages unwound values."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "values": [10, 20]},
            {"_id": 2, "category": "A", "values": [30]},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$unwind": "$values"},
                {"$group": {"_id": "$category", "avg": {"$avg": "$values"}}},
            ],
            "cursor": {},
        },
    )
    # Unwound: 10, 20, 30 → avg = 20
    assertSuccess(
        result,
        [{"_id": "A", "avg": 20.0}],
        msg="$avg after $unwind should average all unwound values",
    )


def test_avg_group_after_match(collection):
    """Test $avg in $group after $match filters documents."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 10, "active": True},
            {"_id": 2, "category": "A", "value": 20, "active": False},
            {"_id": 3, "category": "A", "value": 30, "active": True},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"active": True}},
                {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            ],
            "cursor": {},
        },
    )
    # Only active docs: avg(10, 30) = 20
    assertSuccess(
        result,
        [{"_id": "A", "avg": 20.0}],
        msg="$avg after $match should only average filtered documents",
    )


def test_avg_in_project_after_group(collection):
    """Test $avg in $project after $group uses grouped results."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "A", "value": 20},
            {"_id": 3, "category": "B", "value": 30},
            {"_id": 4, "category": "B", "value": 40},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": "$category",
                        "sum": {"$sum": "$value"},
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"_id": 1}},
                {
                    "$project": {
                        "_id": 1,
                        "manual_avg": {"$divide": ["$sum", "$count"]},
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": "A", "manual_avg": 15.0},
            {"_id": "B", "manual_avg": 35.0},
        ],
        msg="Manual average via $divide after $group should work",
    )


def test_avg_group_after_project_rename(collection):
    """Test $avg in $group after $project that renames fields."""
    collection.insert_many(
        [
            {"_id": 1, "cat": "A", "val": 10},
            {"_id": 2, "cat": "A", "val": 20},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"category": "$cat", "value": "$val"}},
                {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "avg": 15.0}],
        msg="$avg should work on renamed fields from $project",
    )
