"""Tests for $min accumulator — $bucket and $bucketAuto smoke tests."""

from __future__ import annotations

import math

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MIN,
)

# ---------------------------------------------------------------------------
# Property [$bucket Smoke]: representative subset confirming $min works in $bucket context.
# ---------------------------------------------------------------------------
MIN_BUCKET_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_numeric_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": -1, "result": 10}],
        msg="$min in $bucket should return smallest int32 value",
    ),
    AccumulatorTestCase(
        "bucket_null_among_values",
        docs=[{"v": None}, {"v": 10}, {"v": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": -1, "result": 5}],
        msg="$min in $bucket should exclude null and return min of numerics",
    ),
    AccumulatorTestCase(
        "bucket_bson_cross_type",
        docs=[{"v": 100}, {"v": "hello"}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": -1, "result": 100}],
        msg="$min in $bucket should pick Number over String (Number < String)",
    ),
    AccumulatorTestCase(
        "bucket_nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 100}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": -1, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min in $bucket should pick NaN over positive number",
    ),
    AccumulatorTestCase(
        "bucket_neg_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT32_MIN}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": -1, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min in $bucket should pick -Infinity over INT32_MIN",
    ),
]

# ---------------------------------------------------------------------------
# Property [$bucketAuto Smoke]: representative subset confirming $min works
# in $bucketAuto context.
# ---------------------------------------------------------------------------
MIN_BUCKET_AUTO_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_auto_numeric_basic",
        docs=[{"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": 10}],
        msg="$min in $bucketAuto should return smallest int32 value",
    ),
    AccumulatorTestCase(
        "bucket_auto_null_among_values",
        docs=[{"v": None}, {"v": 10}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": 5}],
        msg="$min in $bucketAuto should exclude null and return min of numerics",
    ),
    AccumulatorTestCase(
        "bucket_auto_bson_cross_type",
        docs=[{"v": 100}, {"v": "hello"}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": 100}],
        msg="$min in $bucketAuto should pick Number over String",
    ),
    AccumulatorTestCase(
        "bucket_auto_nan_vs_positive",
        docs=[{"v": FLOAT_NAN}, {"v": 100}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$min in $bucketAuto should pick NaN over positive number",
    ),
    AccumulatorTestCase(
        "bucket_auto_neg_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": INT32_MIN}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$min in $bucketAuto should pick -Infinity over INT32_MIN",
    ),
]

# ---------------------------------------------------------------------------
# Combined smoke tests
# ---------------------------------------------------------------------------
MIN_BUCKET_ALL_SMOKE_TESTS = MIN_BUCKET_SMOKE_TESTS + MIN_BUCKET_AUTO_SMOKE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MIN_BUCKET_ALL_SMOKE_TESTS))
def test_accumulator_min_bucket_smoke(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator in $bucket and $bucketAuto contexts."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
