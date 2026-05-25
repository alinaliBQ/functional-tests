"""Tests for $concatArrays accumulator: arity errors, syntax validation, and error propagation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Arity Rejection]: $concatArrays in accumulator context is unary
# and rejects array syntax.
CONCATARRAYS_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"_id": 1, "v": [1]}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": []}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$concatArrays should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element_array",
        docs=[{"_id": 1, "v": [1]}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": ["$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$concatArrays should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array",
        docs=[{"_id": 1, "a": [1], "b": [2]}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": ["$a", "$b"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$concatArrays should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_literal_array",
        docs=[{"_id": 1, "v": [1]}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": [1]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$concatArrays should reject single-element literal array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object",
        docs=[{"_id": 1, "v": [1]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$concatArrays": {"$add": [1, 2], "$multiply": [3, 4]}},
                }
            }
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$concatArrays should reject multi-key expression object",
    ),
]

# Property [Expression Error Propagation]: errors from sub-expressions
# propagate through $concatArrays accumulator.
CONCATARRAYS_EXPRESSION_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_error_to_int_invalid_string",
        docs=[{"_id": 1, "v": "abc"}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": {"$toInt": "$v"}}}}],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$concatArrays should propagate $toInt conversion error from expression",
    ),
    AccumulatorTestCase(
        "expr_error_divide_by_zero",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$concatArrays": {"$divide": ["$v", 0]}},
                }
            }
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$concatArrays should propagate $divide by zero error",
    ),
]

CONCATARRAYS_ALL_ERROR_TESTS = CONCATARRAYS_ARITY_ERROR_TESTS + CONCATARRAYS_EXPRESSION_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_ALL_ERROR_TESTS))
def test_concatArrays_errors(collection, test_case):
    """Test $concatArrays arity and expression error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
