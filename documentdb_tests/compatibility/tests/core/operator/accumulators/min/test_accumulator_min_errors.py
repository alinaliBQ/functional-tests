"""Tests for $min accumulator — error cases ($group, $bucket, $bucketAuto)."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    MODULO_BY_ZERO_V2_ERROR,
    MODULO_ZERO_REMAINDER_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property [Expression Error Propagation]: errors in sub-expressions used as
# $min operand propagate as errors.
# ---------------------------------------------------------------------------
MIN_EXPRESSION_ERROR_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid",
        docs=[{"v": "not_a_number"}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": {"$toInt": "$v"}}}}],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$min should propagate $toInt conversion error",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero",
        docs=[{"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": {"$divide": ["$v", 0]}}}}],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$min should propagate divide-by-zero error",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero",
        docs=[{"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": {"$mod": ["$v", 0]}}}}],
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$min should propagate mod-by-zero error",
    ),
]

# ---------------------------------------------------------------------------
# Property [Arity Rejection]: $min in accumulator context is unary and rejects
# array syntax.
# ---------------------------------------------------------------------------
MIN_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": []}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": [1]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": ["$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": [1, 2, 3]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": {"$add": [1, 2], "$multiply": [3, 4]}}}}
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$min should reject multi-key expression object",
    ),
]

# ---------------------------------------------------------------------------
# Property [$bucket Smoke — Errors]: arity and expression errors in $bucket.
# ---------------------------------------------------------------------------
MIN_BUCKET_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_arity_rejection",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$min": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min in $bucket should reject array syntax",
    ),
    AccumulatorTestCase(
        "bucket_expression_error",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$min": {"$divide": ["$v", 0]}}},
                }
            }
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$min in $bucket should propagate divide-by-zero error",
    ),
]

# ---------------------------------------------------------------------------
# Property [$bucketAuto Smoke — Errors]: arity and expression errors in $bucketAuto.
# ---------------------------------------------------------------------------
MIN_BUCKET_AUTO_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_auto_arity_rejection",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min in $bucketAuto should reject array syntax",
    ),
    AccumulatorTestCase(
        "bucket_auto_expression_error",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": {"$divide": ["$v", 0]}}},
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$min in $bucketAuto should wrap divide-by-zero as BAD_VALUE_ERROR",
    ),
]

# ---------------------------------------------------------------------------
# Property [Expression Error Codes — $bucketAuto]: $bucketAuto wraps some errors
# with different codes.
# ---------------------------------------------------------------------------
MIN_EXPRESSION_ERROR_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_divide_by_zero_bucket_auto",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": {"$divide": ["$v", 0]}}},
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$min in $bucketAuto should wrap divide-by-zero as BAD_VALUE_ERROR",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero_bucket_auto",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": {"$mod": ["$v", 0]}}},
                }
            }
        ],
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="$min in $bucketAuto should wrap mod-by-zero as MODULO_ZERO_REMAINDER_ERROR",
    ),
]

# ---------------------------------------------------------------------------
# Combined error tests
# ---------------------------------------------------------------------------
MIN_ERROR_TESTS = (
    MIN_EXPRESSION_ERROR_GROUP_TESTS
    + MIN_ARITY_ERROR_TESTS
    + MIN_BUCKET_ERROR_TESTS
    + MIN_BUCKET_AUTO_ERROR_TESTS
    + MIN_EXPRESSION_ERROR_BUCKET_AUTO_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MIN_ERROR_TESTS))
def test_accumulator_min_errors(collection, test_case):
    """Test $min accumulator error cases with $group, $bucket, and $bucketAuto."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
