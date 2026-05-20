"""Smoke tests for $addToSet accumulator in $setWindowFields context."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [SetWindowFields Smoke]: $addToSet works correctly in $setWindowFields context.
ADDTOSET_SET_WINDOW_FIELDS_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "swf_unbounded",
        docs=[
            {"part": "A", "v": 10},
            {"part": "A", "v": 20},
            {"part": "A", "v": 10},
        ],
        pipeline=[
            {
                "$setWindowFields": {
                    "partitionBy": "$part",
                    "sortBy": {"v": 1},
                    "output": {
                        "result": {
                            "$addToSet": "$v",
                            "window": {"documents": ["unbounded", "unbounded"]},
                        }
                    },
                }
            },
            {"$project": {"_id": 0, "v": 1, "result": 1}},
            {"$sort": {"v": 1}},
            {"$limit": 1},
        ],
        expected=[{"v": 10, "result": [10, 20]}],
        msg="$addToSet should collect unique values across entire partition with unbounded window",
    ),
    AccumulatorTestCase(
        "swf_cumulative",
        docs=[
            {"part": "A", "v": 10},
            {"part": "A", "v": 20},
            {"part": "A", "v": 10},
        ],
        pipeline=[
            {
                "$setWindowFields": {
                    "partitionBy": "$part",
                    "sortBy": {"_id": 1},
                    "output": {
                        "result": {
                            "$addToSet": "$v",
                            "window": {"documents": ["unbounded", "current"]},
                        }
                    },
                }
            },
            {"$project": {"_id": 0, "v": 1, "result": 1}},
        ],
        expected=[
            {"v": 10, "result": [10]},
            {"v": 20, "result": [10, 20]},
            {"v": 10, "result": [10, 20]},
        ],
        msg="$addToSet should compute cumulative unique values with [unbounded, current] window",
    ),
    AccumulatorTestCase(
        "swf_partition_by",
        docs=[
            {"part": "A", "v": 1},
            {"part": "A", "v": 2},
            {"part": "B", "v": 3},
            {"part": "B", "v": 3},
        ],
        pipeline=[
            {
                "$setWindowFields": {
                    "partitionBy": "$part",
                    "sortBy": {"v": 1},
                    "output": {
                        "result": {
                            "$addToSet": "$v",
                            "window": {"documents": ["unbounded", "unbounded"]},
                        }
                    },
                }
            },
            {"$project": {"_id": 0, "part": 1, "result": 1}},
            {"$group": {"_id": "$part", "result": {"$first": "$result"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "result": [1, 2]}, {"_id": "B", "result": [3]}],
        msg="$addToSet should compute separate unique sets per partition",
    ),
    AccumulatorTestCase(
        "swf_duplicates",
        docs=[
            {"part": "A", "v": 5},
            {"part": "A", "v": 5},
            {"part": "A", "v": 10},
            {"part": "A", "v": 10},
        ],
        pipeline=[
            {
                "$setWindowFields": {
                    "partitionBy": "$part",
                    "sortBy": {"v": 1},
                    "output": {
                        "result": {
                            "$addToSet": "$v",
                            "window": {"documents": ["unbounded", "unbounded"]},
                        }
                    },
                }
            },
            {"$project": {"_id": 0, "v": 1, "result": 1}},
            {"$limit": 1},
        ],
        expected=[{"v": 5, "result": [5, 10]}],
        msg="$addToSet should deduplicate values within window",
    ),
    AccumulatorTestCase(
        "swf_null_values",
        docs=[
            {"part": "A", "v": None},
            {"part": "A", "v": 5},
            {"part": "A", "v": None},
        ],
        pipeline=[
            {
                "$setWindowFields": {
                    "partitionBy": "$part",
                    "sortBy": {"_id": 1},
                    "output": {
                        "result": {
                            "$addToSet": "$v",
                            "window": {"documents": ["unbounded", "unbounded"]},
                        }
                    },
                }
            },
            {"$project": {"_id": 0, "v": 1, "result": 1}},
            {"$limit": 1},
        ],
        expected=[{"v": None, "result": [None, 5]}],
        msg="$addToSet should collect null as a value in $setWindowFields window",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_SET_WINDOW_FIELDS_SMOKE_TESTS))
def test_addToSet_setWindowFields_smoke(collection, test_case: AccumulatorTestCase):
    """Test $addToSet accumulator in $setWindowFields context."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_order_in=["result"])
