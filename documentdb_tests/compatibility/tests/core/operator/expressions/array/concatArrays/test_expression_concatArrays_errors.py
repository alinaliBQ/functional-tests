"""
Error tests for $concatArrays expression.

Tests non-array input (all BSON types, special numeric values, boundary values,
string edge cases). $concatArrays propagates null but errors on non-array,
non-null input.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.array_test_case import (  # noqa: E501
    ArrayTestClass,
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

# Property [Array Type Strictness]: $concatArrays rejects a non-array argument.
NOT_ARRAY_ERROR_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="string_input",
        arrays=["hello", [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject string input",
    ),
    ArrayTestClass(
        id="int_input",
        arrays=[42, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject int input",
    ),
    ArrayTestClass(
        id="negative_int_input",
        arrays=[-42, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject negative int input",
    ),
    ArrayTestClass(
        id="bool_input",
        arrays=[True, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject bool input",
    ),
    ArrayTestClass(
        id="object_input",
        arrays=[{"a": 1}, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject object input",
    ),
    ArrayTestClass(
        id="double_input",
        arrays=[3.14, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject double input",
    ),
    ArrayTestClass(
        id="negative_double_input",
        arrays=[-3.14, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject negative double input",
    ),
    ArrayTestClass(
        id="decimal128_input",
        arrays=[Decimal128("1"), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject decimal128 input",
    ),
    ArrayTestClass(
        id="int64_input",
        arrays=[Int64(1), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject int64 input",
    ),
    ArrayTestClass(
        id="objectid_input",
        arrays=[ObjectId(), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject objectid input",
    ),
    ArrayTestClass(
        id="datetime_input",
        arrays=[datetime(2024, 1, 1, tzinfo=timezone.utc), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject datetime input",
    ),
    ArrayTestClass(
        id="binary_input",
        arrays=[Binary(b"x", 0), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject binary input",
    ),
    ArrayTestClass(
        id="regex_input",
        arrays=[Regex("x"), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject regex input",
    ),
    ArrayTestClass(
        id="maxkey_input",
        arrays=[MaxKey(), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject maxkey input",
    ),
    ArrayTestClass(
        id="minkey_input",
        arrays=[MinKey(), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject minkey input",
    ),
    ArrayTestClass(
        id="timestamp_input",
        arrays=[Timestamp(0, 0), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject timestamp input",
    ),
    ArrayTestClass(
        id="non_array_second_arg",
        arrays=[[1], 42],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject non-array in second position",
    ),
    ArrayTestClass(
        id="non_array_middle_arg",
        arrays=[[1], "bad", [2]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject non-array in middle position",
    ),
]

# Property [Non-Array Numerics]: $concatArrays rejects special float/Decimal128 arguments.
SPECIAL_NUMERIC_ERROR_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="nan_input",
        arrays=[FLOAT_NAN, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject NaN input",
    ),
    ArrayTestClass(
        id="inf_input",
        arrays=[FLOAT_INFINITY, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Infinity input",
    ),
    ArrayTestClass(
        id="neg_inf_input",
        arrays=[FLOAT_NEGATIVE_INFINITY, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject -Infinity input",
    ),
    ArrayTestClass(
        id="neg_zero_input",
        arrays=[DOUBLE_NEGATIVE_ZERO, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject negative zero input",
    ),
    ArrayTestClass(
        id="decimal128_nan_input",
        arrays=[DECIMAL128_NAN, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Decimal128 NaN input",
    ),
    ArrayTestClass(
        id="decimal128_neg_nan_input",
        arrays=[Decimal128("-NaN"), [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Decimal128 -NaN input",
    ),
    ArrayTestClass(
        id="decimal128_inf_input",
        arrays=[DECIMAL128_INFINITY, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Decimal128 Infinity input",
    ),
    ArrayTestClass(
        id="decimal128_neg_inf_input",
        arrays=[DECIMAL128_NEGATIVE_INFINITY, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Decimal128 -Infinity input",
    ),
    ArrayTestClass(
        id="decimal128_neg_zero_input",
        arrays=[DECIMAL128_NEGATIVE_ZERO, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Decimal128 -0 input",
    ),
]

# Property [Non-Array Boundaries]: $concatArrays rejects numeric boundary values as arguments.
BOUNDARY_ERROR_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="int32_max_input",
        arrays=[INT32_MAX, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject INT32_MAX input",
    ),
    ArrayTestClass(
        id="int32_min_input",
        arrays=[INT32_MIN, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject INT32_MIN input",
    ),
    ArrayTestClass(
        id="int64_max_input",
        arrays=[INT64_MAX, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject INT64_MAX input",
    ),
    ArrayTestClass(
        id="int64_min_input",
        arrays=[INT64_MIN, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject INT64_MIN input",
    ),
    ArrayTestClass(
        id="decimal128_max_input",
        arrays=[DECIMAL128_MAX, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject DECIMAL128_MAX input",
    ),
    ArrayTestClass(
        id="decimal128_min_input",
        arrays=[DECIMAL128_MIN, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject DECIMAL128_MIN input",
    ),
]

# Property [Non-Array Strings]: $concatArrays rejects string arguments regardless of content.
STRING_EDGE_ERROR_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="comma_separated_string_input",
        arrays=["1, 2, 3", [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject comma-separated string",
    ),
    ArrayTestClass(
        id="json_like_string_input",
        arrays=["[1, 2, 3]", [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject JSON-like string",
    ),
    ArrayTestClass(
        id="empty_object_input",
        arrays=[{}, [1]],
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject empty object as arg",
    ),
]

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
    NOT_ARRAY_ERROR_TESTS[0],
    NOT_ARRAY_ERROR_TESTS[-3],
    SPECIAL_NUMERIC_ERROR_TESTS[0],
    BOUNDARY_ERROR_TESTS[0],
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_concatArrays_not_array_literal(collection, test):
    """Test $concatArrays error with non-array literal input."""
    args = [{"$literal": a} if isinstance(a, list) else a for a in test.arrays]
    result = execute_expression(collection, {"$concatArrays": args})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Array Type Strictness]: $concatArrays rejects a field path that resolves to a
# non-array value.
def test_concatArrays_field_resolves_to_non_array(collection):
    """Test $concatArrays errors when a field path resolves to a non-array value."""
    result = execute_expression_with_insert(collection, {"$concatArrays": ["$a", [1]]}, {"a": 1})
    assert_expression_result(result, error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR)


# Property [Array Type Strictness]: $concatArrays rejects an object expression argument.
def test_concatArrays_object_expression_input(collection):
    """Test $concatArrays rejects an object expression that is not an array."""
    result = execute_expression_with_insert(collection, {"$concatArrays": [{"a": "$x"}]}, {"x": 1})
    assert_expression_result(result, error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR)
