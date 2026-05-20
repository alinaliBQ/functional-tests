"""Tests for $max accumulator error cases: arity rejection."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Arity]: $max in accumulator context is a unary operator and
# rejects array syntax in $group, $bucket, and $bucketAuto.
MAX_ARITY_ERROR_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array_group",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": []}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject empty array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_single_element_array_group",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": [1]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single-element literal array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array_group",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": ["$v"]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single field ref in array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_group",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": [1, 2, 3]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject multi-element array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object_group",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": {"$add": [1, 2], "$multiply": [3, 4]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$max should reject multi-key expression object ($group)",
    ),
]

MAX_ARITY_ERROR_BUCKET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": []}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject empty array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_single_element_array_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": [1]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single-element literal array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": ["$v"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single field ref in array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": [1, 2, 3]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject multi-element array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": {"$add": [1, 2], "$multiply": [3, 4]}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$max should reject multi-key expression object ($bucket)",
    ),
]

MAX_ARITY_ERROR_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": []}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject empty array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_single_element_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": [1]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single-element literal array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": ["$v"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single field ref in array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": [1, 2, 3]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject multi-element array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": {"$add": [1, 2], "$multiply": [3, 4]}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$max should reject multi-key expression object ($bucketAuto)",
    ),
]

MAX_ARITY_ERROR_TESTS = (
    MAX_ARITY_ERROR_GROUP_TESTS + MAX_ARITY_ERROR_BUCKET_TESTS + MAX_ARITY_ERROR_BUCKET_AUTO_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_ARITY_ERROR_TESTS))
def test_accumulator_max_errors(collection, test_case):
    """Test $max accumulator error cases: arity rejection."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
