"""
Out-of-bounds index tests for $arrayElemAt expression.

Tests that $arrayElemAt returns no result (missing) when the index
exceeds array bounds in either direction.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.array_test_case import (  # noqa: E501
    ArrayTestClass,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_MAX, INT32_MIN

# Property [Out Of Bounds]: $arrayElemAt returns no value when the index is out of bounds.
OUT_OF_BOUNDS_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="positive_oob",
        arrays=[1, 2, 3],
        idx=15,
        expected=[{}],
        msg="$arrayElemAt should return no result for positive OOB",
    ),
    ArrayTestClass(
        id="positive_oob_by_one",
        arrays=[1, 2, 3],
        idx=3,
        expected=[{}],
        msg="$arrayElemAt should return no result for OOB by one",
    ),
    ArrayTestClass(
        id="negative_oob",
        arrays=[1, 2, 3],
        idx=-4,
        expected=[{}],
        msg="$arrayElemAt should return no result for negative OOB",
    ),
    ArrayTestClass(
        id="negative_oob_large",
        arrays=[1, 2, 3],
        idx=-100,
        expected=[{}],
        msg="$arrayElemAt should return no result for large negative OOB",
    ),
    ArrayTestClass(
        id="empty_array_idx_0",
        arrays=[],
        idx=0,
        expected=[{}],
        msg="$arrayElemAt should return no result for empty array idx 0",
    ),
    ArrayTestClass(
        id="empty_array_neg1",
        arrays=[],
        idx=-1,
        expected=[{}],
        msg="$arrayElemAt should return no result for empty array idx -1",
    ),
    ArrayTestClass(
        id="int32_max_oob",
        arrays=[1, 2, 3],
        idx=INT32_MAX,
        expected=[{}],
        msg="$arrayElemAt should return no result for INT32_MAX index",
    ),
    ArrayTestClass(
        id="int32_min_oob",
        arrays=[1, 2, 3],
        idx=INT32_MIN,
        expected=[{}],
        msg="$arrayElemAt should return no result for INT32_MIN index",
    ),
    ArrayTestClass(
        id="single_element_oob_pos",
        arrays=[42],
        idx=1,
        expected=[{}],
        msg="$arrayElemAt should return no result for single element OOB positive",
    ),
    ArrayTestClass(
        id="single_element_oob_neg",
        arrays=[42],
        idx=-2,
        expected=[{}],
        msg="$arrayElemAt should return no result for single element OOB negative",
    ),
    ArrayTestClass(
        id="decimal128_oob_pos",
        arrays=[1, 2, 3],
        idx=Decimal128("15"),
        expected=[{}],
        msg="$arrayElemAt should return no result for Decimal128 positive OOB",
    ),
    ArrayTestClass(
        id="decimal128_oob_neg",
        arrays=[1, 2, 3],
        idx=Decimal128("-100"),
        expected=[{}],
        msg="$arrayElemAt should return no result for Decimal128 negative OOB",
    ),
]

TEST_SUBSET_FOR_LITERAL = [
    OUT_OF_BOUNDS_TESTS[0],
    OUT_OF_BOUNDS_TESTS[4],
    OUT_OF_BOUNDS_TESTS[-1],
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayElemAt_out_of_bounds_literal(collection, test):
    """Test $arrayElemAt returns no result when index exceeds array bounds."""
    result = execute_expression(collection, {"$arrayElemAt": [test.arrays, test.idx]})
    assertSuccess(result, test.expected)


@pytest.mark.parametrize("test", pytest_params(OUT_OF_BOUNDS_TESTS))
def test_arrayElemAt_out_of_bounds_insert(collection, test):
    """Test $arrayElemAt out-of-bounds with inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$arr", "$idx"]}, {"arr": test.arrays, "idx": test.idx}
    )
    assertSuccess(result, test.expected)
