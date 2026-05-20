"""Smoke tests for $addToSet accumulator in $bucketAuto context."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [BucketAuto Smoke]: $addToSet works correctly in $bucketAuto context.
ADDTOSET_BUCKET_AUTO_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucketAuto_basic",
        docs=[{"v": 10}, {"v": 20}, {"v": 30}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$addToSet": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": [10, 20, 30]}],
        msg="$addToSet should collect unique values in $bucketAuto context",
    ),
    AccumulatorTestCase(
        "bucketAuto_duplicates",
        docs=[{"v": 10}, {"v": 20}, {"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$addToSet": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": [10, 20, 30]}],
        msg="$addToSet should deduplicate values in $bucketAuto context",
    ),
    AccumulatorTestCase(
        "bucketAuto_null_among_values",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$addToSet": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": [None, 5, 3]}],
        msg="$addToSet should collect null alongside values in $bucketAuto context",
    ),
]

# Property [BucketAuto Arity Rejection]: $addToSet rejects array syntax in $bucketAuto context.
ADDTOSET_BUCKET_AUTO_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucketAuto_arity_empty_array",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$addToSet": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$addToSet should reject empty array in $bucketAuto context",
    ),
    AccumulatorTestCase(
        "bucketAuto_expression_error",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$addToSet": {"$divide": ["$v", 0]}}},
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$addToSet should propagate divide-by-zero error in $bucketAuto context",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_BUCKET_AUTO_SMOKE_TESTS))
def test_addToSet_bucketAuto_smoke(collection, test_case: AccumulatorTestCase):
    """Test $addToSet accumulator in $bucketAuto context."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_order_in=["result"])


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_BUCKET_AUTO_ERROR_TESTS))
def test_addToSet_bucketAuto_smoke_errors(collection, test_case: AccumulatorTestCase):
    """Test $addToSet error cases in $bucketAuto context."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
