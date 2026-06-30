"""
Error tests for $concatArrays expression.

Tests non-array input (all BSON types, special numeric values, boundary values,
string edge cases). $concatArrays propagates null but errors on non-array,
non-null input.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.concatArrays.utils.concatArrays_common import (  # noqa: E501
    ConcatArraysTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import CONCAT_ARRAYS_NOT_ARRAY_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# ---------------------------------------------------------------------------
# Error: non-array input — standard BSON types
# ---------------------------------------------------------------------------
NOT_ARRAY_ERROR_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="string_input",
        arrays=["hello", [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject string input",
    ),
    ConcatArraysTest(
        id="int_input",
        arrays=[42, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject int input",
    ),
    ConcatArraysTest(
        id="negative_int_input",
        arrays=[-42, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject negative int input",
    ),
    ConcatArraysTest(
        id="bool_input",
        arrays=[True, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject bool input",
    ),
    ConcatArraysTest(
        id="object_input",
        arrays=[{"a": 1}, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject object input",
    ),
    ConcatArraysTest(
        id="double_input",
        arrays=[3.14, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject double input",
    ),
    ConcatArraysTest(
        id="negative_double_input",
        arrays=[-3.14, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject negative double input",
    ),
    ConcatArraysTest(
        id="decimal128_input",
        arrays=[Decimal128("1"), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject decimal128 input",
    ),
    ConcatArraysTest(
        id="int64_input",
        arrays=[Int64(1), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject int64 input",
    ),
    ConcatArraysTest(
        id="objectid_input",
        arrays=[ObjectId(), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject objectid input",
    ),
    ConcatArraysTest(
        id="datetime_input",
        arrays=[datetime(2024, 1, 1), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject datetime input",
    ),
    ConcatArraysTest(
        id="binary_input",
        arrays=[Binary(b"x", 0), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject binary input",
    ),
    ConcatArraysTest(
        id="regex_input",
        arrays=[Regex("x"), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject regex input",
    ),
    ConcatArraysTest(
        id="maxkey_input",
        arrays=[MaxKey(), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject maxkey input",
    ),
    ConcatArraysTest(
        id="minkey_input",
        arrays=[MinKey(), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject minkey input",
    ),
    ConcatArraysTest(
        id="timestamp_input",
        arrays=[Timestamp(0, 0), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject timestamp input",
    ),
    ConcatArraysTest(
        id="non_array_second_arg",
        arrays=[[1], 42],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject non-array in second position",
    ),
    ConcatArraysTest(
        id="non_array_middle_arg",
        arrays=[[1], "bad", [2]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject non-array in middle position",
    ),
]

# ---------------------------------------------------------------------------
# Error: special float/Decimal128 values
# ---------------------------------------------------------------------------
SPECIAL_NUMERIC_ERROR_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="nan_input",
        arrays=[FLOAT_NAN, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject NaN input",
    ),
    ConcatArraysTest(
        id="inf_input",
        arrays=[FLOAT_INFINITY, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject Infinity input",
    ),
    ConcatArraysTest(
        id="neg_inf_input",
        arrays=[FLOAT_NEGATIVE_INFINITY, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject -Infinity input",
    ),
    ConcatArraysTest(
        id="neg_zero_input",
        arrays=[DOUBLE_NEGATIVE_ZERO, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject negative zero input",
    ),
    ConcatArraysTest(
        id="decimal128_nan_input",
        arrays=[DECIMAL128_NAN, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 NaN input",
    ),
    ConcatArraysTest(
        id="decimal128_neg_nan_input",
        arrays=[Decimal128("-NaN"), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -NaN input",
    ),
    ConcatArraysTest(
        id="decimal128_inf_input",
        arrays=[DECIMAL128_INFINITY, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 Infinity input",
    ),
    ConcatArraysTest(
        id="decimal128_neg_inf_input",
        arrays=[DECIMAL128_NEGATIVE_INFINITY, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -Infinity input",
    ),
    ConcatArraysTest(
        id="decimal128_neg_zero_input",
        arrays=[DECIMAL128_NEGATIVE_ZERO, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -0 input",
    ),
]

# ---------------------------------------------------------------------------
# Error: numeric boundary values
# ---------------------------------------------------------------------------
BOUNDARY_ERROR_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="int32_max_input",
        arrays=[INT32_MAX, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MAX input",
    ),
    ConcatArraysTest(
        id="int32_min_input",
        arrays=[INT32_MIN, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MIN input",
    ),
    ConcatArraysTest(
        id="int64_max_input",
        arrays=[INT64_MAX, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject INT64_MAX input",
    ),
    ConcatArraysTest(
        id="int64_min_input",
        arrays=[INT64_MIN, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject INT64_MIN input",
    ),
    ConcatArraysTest(
        id="decimal128_max_input",
        arrays=[DECIMAL128_MAX, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject DECIMAL128_MAX input",
    ),
    ConcatArraysTest(
        id="decimal128_min_input",
        arrays=[DECIMAL128_MIN, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject DECIMAL128_MIN input",
    ),
]

# ---------------------------------------------------------------------------
# Error: string edge cases
# ---------------------------------------------------------------------------
STRING_EDGE_ERROR_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="comma_separated_string_input",
        arrays=["1, 2, 3", [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject comma-separated string",
    ),
    ConcatArraysTest(
        id="json_like_string_input",
        arrays=["[1, 2, 3]", [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject JSON-like string",
    ),
    ConcatArraysTest(
        id="empty_object_input",
        arrays=[{}, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Should reject empty object as arg",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_TESTS = (
    NOT_ARRAY_ERROR_TESTS
    + SPECIAL_NUMERIC_ERROR_TESTS
    + BOUNDARY_ERROR_TESTS
    + STRING_EDGE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_concatArrays_not_array_insert(collection, test):
    """Test $concatArrays error with non-array input from inserted documents."""
    doc = {f"arr{i}": a for i, a in enumerate(test.arrays)}
    refs = [f"$arr{i}" for i in range(len(test.arrays))]
    result = execute_expression_with_insert(collection, {"$concatArrays": refs}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


TEST_SUBSET_FOR_LITERAL = [
    NOT_ARRAY_ERROR_TESTS[0],  # string_input
    NOT_ARRAY_ERROR_TESTS[-3],  # timestamp_input
    SPECIAL_NUMERIC_ERROR_TESTS[0],  # nan_input
    BOUNDARY_ERROR_TESTS[0],  # int32_max_input
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_concatArrays_not_array_literal(collection, test):
    """Test $concatArrays error with non-array literal input."""
    args = [{"$literal": a} if isinstance(a, list) else a for a in test.arrays]
    result = execute_expression(collection, {"$concatArrays": args})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
