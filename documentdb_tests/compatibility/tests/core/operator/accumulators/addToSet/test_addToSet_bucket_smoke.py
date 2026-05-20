"""Smoke tests for $addToSet accumulator in $bucket context."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    DIVIDE_BY_ZERO_V2_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Bucket Smoke]: $addToSet works correctly in $bucket context.
ADDTOSET_BUCKET_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_basic",
        docs=[{"v": 10}, {"v": 20}, {"v": 30}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$addToSet": "$v"}},
                }
            }
        ],
        expected=[{"_id": -1, "result": [10, 20, 30]}],
        msg="$addToSet should collect unique values in $bucket context",
    ),
    AccumulatorTestCase(
        "bucket_duplicates",
        docs=[{"v": 10}, {"v": 20}, {"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$addToSet": "$v"}},
                }
            }
        ],
        expected=[{"_id": -1, "result": [10, 20, 30]}],
        msg="$addToSet should deduplicate values in $bucket context",
    ),
    AccumulatorTestCase(
        "bucket_null_among_values",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$addToSet": "$v"}},
                }
            }
        ],
        expected=[{"_id": -1, "result": [None, 5, 3]}],
        msg="$addToSet should collect null alongside values in $bucket context",
    ),
]

# Property [Bucket Arity Rejection]: $addToSet rejects array syntax in $bucket context.
ADDTOSET_BUCKET_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_arity_empty_array",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$addToSet": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$addToSet should reject empty array in $bucket context",
    ),
    AccumulatorTestCase(
        "bucket_expression_error",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$addToSet": {"$divide": ["$v", 0]}}},
                }
            }
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$addToSet should propagate divide-by-zero error in $bucket context",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_BUCKET_SMOKE_TESTS))
def test_addToSet_bucket_smoke(collection, test_case: AccumulatorTestCase):
    """Test $addToSet accumulator in $bucket context."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_order_in=["result"])


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_BUCKET_ERROR_TESTS))
def test_addToSet_bucket_smoke_errors(collection, test_case: AccumulatorTestCase):
    """Test $addToSet error cases in $bucket context."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
