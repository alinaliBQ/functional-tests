"""
Error tests for $arrayToObject expression.

Tests non-array input, invalid element format, non-string keys,
and wrong arity errors.
"""

from datetime import datetime

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
from documentdb_tests.framework.error_codes import (
    ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
    ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
    ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
    ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
    ARRAY_TO_OBJECT_MIXED_KV_THEN_PAIR_ERROR,
    ARRAY_TO_OBJECT_MIXED_PAIR_THEN_KV_ERROR,
    ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
    ARRAY_TO_OBJECT_NULL_BYTE_KV_KEY_ERROR,
    ARRAY_TO_OBJECT_NULL_BYTE_PAIR_KEY_ERROR,
    ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
    ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Array Type Strictness]: $arrayToObject rejects a non-array input.
NOT_ARRAY_ERROR_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="string_input",
        arrays="hello",
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject string input",
    ),
    ArrayTestClass(
        id="int_input",
        arrays=42,
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject int input",
    ),
    ArrayTestClass(
        id="bool_input",
        arrays=True,
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject bool input",
    ),
    ArrayTestClass(
        id="object_input",
        arrays={"a": 1},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject object input",
    ),
    ArrayTestClass(
        id="double_input",
        arrays=3.14,
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject double input",
    ),
    ArrayTestClass(
        id="decimal128_input",
        arrays=Decimal128("1"),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject decimal128 input",
    ),
    ArrayTestClass(
        id="int64_input",
        arrays=Int64(1),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject int64 input",
    ),
    ArrayTestClass(
        id="objectid_input",
        arrays=ObjectId(),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject objectid input",
    ),
    ArrayTestClass(
        id="datetime_input",
        arrays=datetime(2024, 1, 1),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject datetime input",
    ),
    ArrayTestClass(
        id="binary_input",
        arrays=Binary(b"x", 0),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject binary input",
    ),
    ArrayTestClass(
        id="regex_input",
        arrays=Regex("x"),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject regex input",
    ),
    ArrayTestClass(
        id="maxkey_input",
        arrays=MaxKey(),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject maxkey input",
    ),
    ArrayTestClass(
        id="minkey_input",
        arrays=MinKey(),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject minkey input",
    ),
    ArrayTestClass(
        id="timestamp_input",
        arrays=Timestamp(0, 0),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject timestamp input",
    ),
]

# Property [Element Format]: $arrayToObject rejects an element that is not a k/v doc or pair.
INVALID_ELEMENT_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="element_is_string",
        arrays=["not_a_pair"],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject string element",
    ),
    ArrayTestClass(
        id="element_is_int",
        arrays=[42],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject int element",
    ),
    ArrayTestClass(
        id="element_is_null",
        arrays=[None],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject null element",
    ),
    ArrayTestClass(
        id="element_is_bool",
        arrays=[True],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject bool element",
    ),
    ArrayTestClass(
        id="element_is_double",
        arrays=[3.14],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject double element",
    ),
    ArrayTestClass(
        id="element_is_objectid",
        arrays=[ObjectId()],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject ObjectId element",
    ),
    ArrayTestClass(
        id="kv_missing_v",
        arrays=[{"k": "a"}],
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject k/v doc missing v field",
    ),
    ArrayTestClass(
        id="kv_missing_k",
        arrays=[{"v": 1}],
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject k/v doc missing k field",
    ),
    ArrayTestClass(
        id="kv_extra_field",
        arrays=[{"k": "a", "v": 1, "extra": 2}],
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject k/v doc with extra field",
    ),
    ArrayTestClass(
        id="kv_empty_doc",
        arrays=[{}],
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject empty document",
    ),
    ArrayTestClass(
        id="kv_wrong_field_names",
        arrays=[{"y": "x", "x": "y"}],
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject wrong field names",
    ),
    ArrayTestClass(
        id="kv_uppercase_K",
        arrays=[{"K": "k1", "v": 2}],
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject uppercase K (case-sensitive)",
    ),
    ArrayTestClass(
        id="kv_uppercase_V",
        arrays=[{"k": "k1", "V": 2}],
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject uppercase V (case-sensitive)",
    ),
    ArrayTestClass(
        id="kv_key_value_names",
        arrays=[{"key": "k1", "value": "v1"}],
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject 'key'/'value' instead of 'k'/'v'",
    ),
    ArrayTestClass(
        id="mix_valid_pair_and_invalid",
        arrays=[["a", 1], 123],
        error_code=ARRAY_TO_OBJECT_MIXED_PAIR_THEN_KV_ERROR,
        msg="$arrayToObject should reject mix of valid pair and invalid element",
    ),
    ArrayTestClass(
        id="pair_one_element",
        arrays=[["a"]],
        error_code=ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
        msg="$arrayToObject should reject one-element array pair",
    ),
    ArrayTestClass(
        id="pair_three_elements",
        arrays=[["a", 1, 2]],
        error_code=ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
        msg="$arrayToObject should reject three-element array pair",
    ),
    ArrayTestClass(
        id="pair_empty_array",
        arrays=[[]],
        error_code=ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
        msg="$arrayToObject should reject empty array pair",
    ),
]

# Property [Key Type Strictness]: $arrayToObject rejects a non-string key.
KEY_NOT_STRING_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="kv_int_key",
        arrays=[{"k": 1, "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject int key in k/v form",
    ),
    ArrayTestClass(
        id="kv_bool_key",
        arrays=[{"k": True, "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject bool key in k/v form",
    ),
    ArrayTestClass(
        id="kv_null_key",
        arrays=[{"k": None, "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject null key in k/v form",
    ),
    ArrayTestClass(
        id="kv_array_key",
        arrays=[{"k": [1], "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject array key in k/v form",
    ),
    ArrayTestClass(
        id="kv_object_key",
        arrays=[{"k": {"x": 1}, "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject object key in k/v form",
    ),
    ArrayTestClass(
        id="kv_double_key",
        arrays=[{"k": 1.5, "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject double key in k/v form",
    ),
    ArrayTestClass(
        id="kv_int64_key",
        arrays=[{"k": Int64(1), "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Int64 key in k/v form",
    ),
    ArrayTestClass(
        id="kv_decimal128_key",
        arrays=[{"k": Decimal128("1"), "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Decimal128 key in k/v form",
    ),
    ArrayTestClass(
        id="pair_int_key",
        arrays=[[1, "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject int key in pair form",
    ),
    ArrayTestClass(
        id="pair_bool_key",
        arrays=[[True, "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject bool key in pair form",
    ),
    ArrayTestClass(
        id="pair_null_key",
        arrays=[[None, "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject null key in pair form",
    ),
    ArrayTestClass(
        id="pair_array_key",
        arrays=[[[1], "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject array key in pair form",
    ),
    ArrayTestClass(
        id="pair_object_key",
        arrays=[[{"x": 1}, "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject object key in pair form",
    ),
    ArrayTestClass(
        id="pair_double_key",
        arrays=[[1.5, "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject double key in pair form",
    ),
    ArrayTestClass(
        id="pair_int64_key",
        arrays=[[Int64(1), "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Int64 key in pair form",
    ),
    ArrayTestClass(
        id="pair_decimal128_key",
        arrays=[[Decimal128("1"), "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Decimal128 key in pair form",
    ),
]

# Property [Mixed Formats]: $arrayToObject rejects arrays mixing k/v doc and pair forms.
MIXED_FORMAT_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="mixed_kv_then_pair",
        arrays=[{"k": "price", "v": 24}, ["item", "apple"]],
        error_code=ARRAY_TO_OBJECT_MIXED_KV_THEN_PAIR_ERROR,
        msg="$arrayToObject should reject a k/v doc followed by a pair",
    ),
    ArrayTestClass(
        id="mixed_pair_then_kv",
        arrays=[["item", "apple"], {"k": "price", "v": 24}],
        error_code=ARRAY_TO_OBJECT_MIXED_PAIR_THEN_KV_ERROR,
        msg="$arrayToObject should reject a pair followed by a k/v doc",
    ),
]

# Property [Null Byte Key]: $arrayToObject rejects a key containing a null byte.
NULL_BYTE_KEY_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="null_byte_in_key_pair",
        arrays=[["a\x00b", "value"]],
        error_code=ARRAY_TO_OBJECT_NULL_BYTE_PAIR_KEY_ERROR,
        msg="$arrayToObject should reject a null byte in a key (pair form)",
    ),
    ArrayTestClass(
        id="null_byte_in_key_kv",
        arrays=[{"k": "a\x00b", "v": "value"}],
        error_code=ARRAY_TO_OBJECT_NULL_BYTE_KV_KEY_ERROR,
        msg="$arrayToObject should reject a null byte in a key (k/v form)",
    ),
]

ALL_TESTS = (
    NOT_ARRAY_ERROR_TESTS
    + INVALID_ELEMENT_TESTS
    + KEY_NOT_STRING_TESTS
    + MIXED_FORMAT_TESTS
    + NULL_BYTE_KEY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_arrayToObject_insert(collection, test):
    """Test $arrayToObject error cases with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayToObject": "$arr"}, {"arr": test.arrays}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


TEST_SUBSET_FOR_LITERAL = [
    NOT_ARRAY_ERROR_TESTS[0],
    NOT_ARRAY_ERROR_TESTS[3],
    INVALID_ELEMENT_TESTS[0],
    INVALID_ELEMENT_TESTS[6],
    KEY_NOT_STRING_TESTS[0],
    KEY_NOT_STRING_TESTS[8],
    MIXED_FORMAT_TESTS[0],
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayToObject_literal(collection, test):
    """Test $arrayToObject error cases with literal values."""
    # Use $literal for array inputs to prevent MongoDB from interpreting them as arguments
    expr = {"$literal": test.arrays} if isinstance(test.arrays, list) else test.arrays
    result = execute_expression(collection, {"$arrayToObject": expr})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Arity]: $arrayToObject requires exactly one argument.
ARITY_ERROR_TESTS = [
    pytest.param({"$arrayToObject": [[], []]}, id="two_args"),
]


@pytest.mark.parametrize("expr", ARITY_ERROR_TESTS)
def test_arrayToObject_arity_error(collection, expr):
    """Test $arrayToObject errors with wrong number of arguments."""
    result = execute_expression(collection, expr)
    assert_expression_result(result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR)
