"""
Tests for $avg accumulator in $group context.

Covers numeric equivalence in grouping, single/empty groups,
precision edge cases, multiple groups, and comparison with $sum.
"""

from __future__ import annotations

from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# --- Helpers ---


def _group_avg(collection, docs, group_id="$category", field="$value"):
    """Insert docs and run $group with $avg."""
    collection.insert_many(docs)
    return execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": group_id, "avg": {"$avg": field}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )


# --- 13. Numeric Equivalence in Grouping ---


def test_avg_group_numeric_equivalence_grouping(collection):
    """Test $avg groups numerically equivalent values of different types into same group."""
    collection.insert_many(
        [
            {"_id": 1, "key": 1, "value": 10},
            {"_id": 2, "key": Int64(1), "value": 20},
            {"_id": 3, "key": 1.0, "value": 30},
            {"_id": 4, "key": Decimal128("1"), "value": 40},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$key", "avg": {"$avg": "$value"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "avg": 25.0}],
        msg="Numerically equivalent group keys should produce a single group",
    )


def test_avg_group_zero_equivalence(collection):
    """Test $avg groups all zero representations into same group."""
    collection.insert_many(
        [
            {"_id": 1, "key": 0, "value": 10},
            {"_id": 2, "key": Int64(0), "value": 20},
            {"_id": 3, "key": 0.0, "value": 30},
            {"_id": 4, "key": Decimal128("0"), "value": 40},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$key", "avg": {"$avg": "$value"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 0, "avg": 25.0}],
        msg="All zero representations should group together",
    )


# --- 16. Single Document Group / Empty Group ---


def test_avg_group_single_document(collection):
    """Test $avg with single document in group returns that value."""
    result = _group_avg(
        collection,
        [{"_id": 1, "category": "A", "value": 42}],
    )
    assertSuccess(
        result,
        [{"_id": "A", "avg": 42.0}],
        msg="$avg of single document should return that value as double",
    )


def test_avg_group_single_document_non_numeric(collection):
    """Test $avg with single non-numeric document returns null."""
    result = _group_avg(
        collection,
        [{"_id": 1, "category": "A", "value": "hello"}],
    )
    assertSuccess(
        result,
        [{"_id": "A", "avg": None}],
        msg="$avg of single non-numeric document should return null",
    )


def test_avg_group_single_document_null(collection):
    """Test $avg with single null document returns null."""
    result = _group_avg(
        collection,
        [{"_id": 1, "category": "A", "value": None}],
    )
    assertSuccess(
        result,
        [{"_id": "A", "avg": None}],
        msg="$avg of single null document should return null",
    )


def test_avg_group_single_document_missing_field(collection):
    """Test $avg with single document missing the field returns null."""
    result = _group_avg(
        collection,
        [{"_id": 1, "category": "A"}],
    )
    assertSuccess(
        result,
        [{"_id": "A", "avg": None}],
        msg="$avg of single document with missing field should return null",
    )


def test_avg_group_empty_collection(collection):
    """Test $avg on empty collection produces no output documents."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [],
        msg="$avg on empty collection should produce no output",
    )


def test_avg_group_all_filtered_out(collection):
    """Test $avg where $match filters all documents produces no output."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "A", "value": 20},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"category": "Z"}},
                {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [],
        msg="$avg after filtering all documents should produce no output",
    )


def test_avg_group_null_id(collection):
    """Test $avg with _id: null groups entire collection."""
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
                {"$group": {"_id": None, "avg": {"$avg": "$value"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": None, "avg": 20.0}],
        msg="$avg with _id: null should average entire collection",
    )


# --- 18. Precision Edge Cases ---


def test_avg_group_odd_sum_two_int32(collection):
    """Test $avg of two int32 values whose sum is odd produces fractional result."""
    result = _group_avg(
        collection,
        [
            {"_id": 1, "category": "A", "value": 1},
            {"_id": 2, "category": "A", "value": 2},
        ],
    )
    assertSuccess(
        result,
        [{"_id": "A", "avg": 1.5}],
        msg="$avg of 1 and 2 should return 1.5",
    )


def test_avg_group_repeating_decimal(collection):
    """Test $avg producing repeating decimal (1+1+2)/3."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 1},
            {"_id": 2, "category": "A", "value": 1},
            {"_id": 3, "category": "A", "value": 2},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "avg": 1.3333333333333333}],
        msg="$avg of 1,1,2 should return 4/3",
    )


def test_avg_group_sequence_1_to_100(collection):
    """Test $avg of sequence 1..100 returns 50.5."""
    docs = [{"_id": i, "category": "A", "value": i} for i in range(1, 101)]
    result = _group_avg(collection, docs)
    assertSuccess(
        result,
        [{"_id": "A", "avg": 50.5}],
        msg="$avg of 1..100 should return 50.5",
    )


def test_avg_group_large_count_identical(collection):
    """Test $avg of 1000 identical values returns that value."""
    docs = [{"_id": i, "category": "A", "value": 7} for i in range(1000)]
    result = _group_avg(collection, docs)
    assertSuccess(
        result,
        [{"_id": "A", "avg": 7.0}],
        msg="$avg of 1000 identical values should return that value",
    )


# --- 20. Multiple Groups with Different Characteristics ---


def test_avg_group_different_counts(collection):
    """Test $avg where groups have different document counts."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "B", "value": 20},
            {"_id": 3, "category": "B", "value": 40},
            {"_id": 4, "category": "C", "value": 5},
            {"_id": 5, "category": "C", "value": 10},
            {"_id": 6, "category": "C", "value": 15},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": "A", "avg": 10.0},
            {"_id": "B", "avg": 30.0},
            {"_id": "C", "avg": 10.0},
        ],
        msg="$avg should compute correct average per group with different counts",
    )


def test_avg_group_one_all_nulls_one_all_numeric(collection):
    """Test $avg where one group has all nulls and another has numerics."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": None},
            {"_id": 2, "category": "A", "value": None},
            {"_id": 3, "category": "B", "value": 10},
            {"_id": 4, "category": "B", "value": 20},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": "A", "avg": None},
            {"_id": "B", "avg": 15.0},
        ],
        msg="Group with all nulls returns null, group with numerics returns average",
    )


def test_avg_group_mixed_types_per_group(collection):
    """Test $avg where groups have different numeric type distributions."""
    collection.insert_many(
        [
            {"_id": 1, "category": "int", "value": 10},
            {"_id": 2, "category": "int", "value": 20},
            {"_id": 3, "category": "dec", "value": Decimal128("10")},
            {"_id": 4, "category": "dec", "value": Decimal128("20")},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": "dec", "avg": Decimal128("15")},
            {"_id": "int", "avg": 15.0},
        ],
        msg="Int group returns double, Decimal128 group returns Decimal128",
    )


# --- 21. Comparison with Related Operators ---


def test_avg_equals_sum_divided_by_count(collection):
    """Test $avg equals $sum / count for int32 values."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "A", "value": 20},
            {"_id": 3, "category": "A", "value": 30},
            {"_id": 4, "category": "A", "value": 40},
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
                        "avg": {"$avg": "$value"},
                        "sum": {"$sum": "$value"},
                        "count": {"$sum": 1},
                    }
                },
            ],
            "cursor": {},
        },
    )
    # avg should be 25.0, sum should be 100, count should be 4
    assertSuccess(
        result,
        [{"_id": "A", "avg": 25.0, "sum": 100, "count": 4}],
        msg="$avg should equal $sum / count",
    )


def test_avg_vs_sum_non_numeric_handling(collection):
    """Test $avg returns null but $sum returns 0 when all values are non-numeric."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": "hello"},
            {"_id": 2, "category": "A", "value": "world"},
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
                        "avg": {"$avg": "$value"},
                        "sum": {"$sum": "$value"},
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "avg": None, "sum": 0}],
        msg="$avg returns null for non-numeric but $sum returns 0",
    )
