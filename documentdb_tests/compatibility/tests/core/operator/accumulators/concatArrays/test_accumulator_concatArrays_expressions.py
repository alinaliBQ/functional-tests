"""Tests for $concatArrays accumulator: expression arguments and constant expressions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Arguments]: $concatArrays accepts various expression
# forms that resolve to arrays.
CONCATARRAYS_EXPRESSION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_simple_field_path",
        docs=[
            {"_id": 1, "items": [1, 2]},
            {"_id": 2, "items": [3]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$items"}}},
        ],
        expected=[{"_id": None, "result": [1, 2, 3]}],
        msg="$concatArrays should accept a simple field path expression",
    ),
    AccumulatorTestCase(
        "expr_nested_field_path",
        docs=[
            {"_id": 1, "a": {"items": [10, 20]}},
            {"_id": 2, "a": {"items": [30]}},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$a.items"}}},
        ],
        expected=[{"_id": None, "result": [10, 20, 30]}],
        msg="$concatArrays should accept a nested field path expression",
    ),
    AccumulatorTestCase(
        "expr_literal_constant_array",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": {"$literal": [1, 2]}}}},
        ],
        expected=[{"_id": None, "result": [1, 2, 1, 2, 1, 2]}],
        msg="$concatArrays should repeat a literal array constant for each document",
    ),
    AccumulatorTestCase(
        "expr_computed_cond",
        docs=[
            {"_id": 1, "qty": 5, "v": [1, 2]},
            {"_id": 2, "qty": 0, "v": [3, 4]},
            {"_id": 3, "qty": 3, "v": [5]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$concatArrays": {"$cond": [{"$gt": ["$qty", 0]}, "$v", []]}},
                }
            },
        ],
        expected=[{"_id": None, "result": [1, 2, 5]}],
        msg="$concatArrays should accept computed $cond expression returning arrays",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_EXPRESSION_TESTS))
def test_accumulator_concatArrays_expressions(collection, test_case: AccumulatorTestCase):
    """Test $concatArrays expression argument cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
