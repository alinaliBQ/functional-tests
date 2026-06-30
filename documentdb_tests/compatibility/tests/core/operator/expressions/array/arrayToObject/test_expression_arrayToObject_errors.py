"""
Error tests for $arrayToObject expression.

Tests non-array input, invalid element format, non-string keys,
and wrong arity errors.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.arrayToObject.utils.arrayToObject_common import (  # noqa: E501
    ArrayToObjectTest,
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
NOT_ARRAY_ERROR_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="string_input",
        array="hello",
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject string input",
    ),
    ArrayToObjectTest(
        id="int_input",
        array=42,
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject int input",
    ),
    ArrayToObjectTest(
        id="bool_input",
        array=True,
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject bool input",
    ),
    ArrayToObjectTest(
        id="object_input",
        array={"a": 1},
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject object input",
    ),
    ArrayToObjectTest(
        id="double_input",
        array=3.14,
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject double input",
    ),
    ArrayToObjectTest(
        id="decimal128_input",
        array=Decimal128("1"),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject decimal128 input",
    ),
    ArrayToObjectTest(
        id="int64_input",
        array=Int64(1),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject int64 input",
    ),
    ArrayToObjectTest(
        id="objectid_input",
        array=ObjectId(),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject objectid input",
    ),
    ArrayToObjectTest(
        id="datetime_input",
        array=datetime(2024, 1, 1),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject datetime input",
    ),
    ArrayToObjectTest(
        id="binary_input",
        array=Binary(b"x", 0),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject binary input",
    ),
    ArrayToObjectTest(
        id="regex_input",
        array=Regex("x"),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject regex input",
    ),
    ArrayToObjectTest(
        id="maxkey_input",
        array=MaxKey(),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject maxkey input",
    ),
    ArrayToObjectTest(
        id="minkey_input",
        array=MinKey(),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject minkey input",
    ),
    ArrayToObjectTest(
        id="timestamp_input",
        array=Timestamp(0, 0),
        error_code=ARRAY_TO_OBJECT_NOT_ARRAY_ERROR,
        msg="$arrayToObject should reject timestamp input",
    ),
]

# Property [Element Format]: $arrayToObject rejects an element that is not a k/v doc or pair.
INVALID_ELEMENT_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="element_is_string",
        array=["not_a_pair"],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject string element",
    ),
    ArrayToObjectTest(
        id="element_is_int",
        array=[42],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject int element",
    ),
    ArrayToObjectTest(
        id="element_is_null",
        array=[None],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject null element",
    ),
    ArrayToObjectTest(
        id="element_is_bool",
        array=[True],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject bool element",
    ),
    ArrayToObjectTest(
        id="element_is_double",
        array=[3.14],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject double element",
    ),
    ArrayToObjectTest(
        id="element_is_objectid",
        array=[ObjectId()],
        error_code=ARRAY_TO_OBJECT_INVALID_ELEMENT_ERROR,
        msg="$arrayToObject should reject ObjectId element",
    ),
    ArrayToObjectTest(
        id="kv_missing_v",
        array=[{"k": "a"}],
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject k/v doc missing v field",
    ),
    ArrayToObjectTest(
        id="kv_missing_k",
        array=[{"v": 1}],
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject k/v doc missing k field",
    ),
    ArrayToObjectTest(
        id="kv_extra_field",
        array=[{"k": "a", "v": 1, "extra": 2}],
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject k/v doc with extra field",
    ),
    ArrayToObjectTest(
        id="kv_empty_doc",
        array=[{}],
        error_code=ARRAY_TO_OBJECT_INVALID_KV_DOC_ERROR,
        msg="$arrayToObject should reject empty document",
    ),
    ArrayToObjectTest(
        id="kv_wrong_field_names",
        array=[{"y": "x", "x": "y"}],
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject wrong field names",
    ),
    ArrayToObjectTest(
        id="kv_uppercase_K",
        array=[{"K": "k1", "v": 2}],
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject uppercase K (case-sensitive)",
    ),
    ArrayToObjectTest(
        id="kv_uppercase_V",
        array=[{"k": "k1", "V": 2}],
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject uppercase V (case-sensitive)",
    ),
    ArrayToObjectTest(
        id="kv_key_value_names",
        array=[{"key": "k1", "value": "v1"}],
        error_code=ARRAY_TO_OBJECT_WRONG_FIELD_NAMES_ERROR,
        msg="$arrayToObject should reject 'key'/'value' instead of 'k'/'v'",
    ),
    ArrayToObjectTest(
        id="mix_valid_pair_and_invalid",
        array=[["a", 1], 123],
        error_code=ARRAY_TO_OBJECT_MIXED_PAIR_THEN_KV_ERROR,
        msg="$arrayToObject should reject mix of valid pair and invalid element",
    ),
    ArrayToObjectTest(
        id="pair_one_element",
        array=[["a"]],
        error_code=ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
        msg="$arrayToObject should reject one-element array pair",
    ),
    ArrayToObjectTest(
        id="pair_three_elements",
        array=[["a", 1, 2]],
        error_code=ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
        msg="$arrayToObject should reject three-element array pair",
    ),
    ArrayToObjectTest(
        id="pair_empty_array",
        array=[[]],
        error_code=ARRAY_TO_OBJECT_INVALID_PAIR_ERROR,
        msg="$arrayToObject should reject empty array pair",
    ),
]

# Property [Key Type Strictness]: $arrayToObject rejects a non-string key.
KEY_NOT_STRING_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="kv_int_key",
        array=[{"k": 1, "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject int key in k/v form",
    ),
    ArrayToObjectTest(
        id="kv_bool_key",
        array=[{"k": True, "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject bool key in k/v form",
    ),
    ArrayToObjectTest(
        id="kv_null_key",
        array=[{"k": None, "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject null key in k/v form",
    ),
    ArrayToObjectTest(
        id="kv_array_key",
        array=[{"k": [1], "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject array key in k/v form",
    ),
    ArrayToObjectTest(
        id="kv_object_key",
        array=[{"k": {"x": 1}, "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject object key in k/v form",
    ),
    ArrayToObjectTest(
        id="kv_double_key",
        array=[{"k": 1.5, "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject double key in k/v form",
    ),
    ArrayToObjectTest(
        id="kv_int64_key",
        array=[{"k": Int64(1), "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Int64 key in k/v form",
    ),
    ArrayToObjectTest(
        id="kv_decimal128_key",
        array=[{"k": Decimal128("1"), "v": "val"}],
        error_code=ARRAY_TO_OBJECT_KV_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Decimal128 key in k/v form",
    ),
    ArrayToObjectTest(
        id="pair_int_key",
        array=[[1, "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject int key in pair form",
    ),
    ArrayToObjectTest(
        id="pair_bool_key",
        array=[[True, "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject bool key in pair form",
    ),
    ArrayToObjectTest(
        id="pair_null_key",
        array=[[None, "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject null key in pair form",
    ),
    ArrayToObjectTest(
        id="pair_array_key",
        array=[[[1], "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject array key in pair form",
    ),
    ArrayToObjectTest(
        id="pair_object_key",
        array=[[{"x": 1}, "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject object key in pair form",
    ),
    ArrayToObjectTest(
        id="pair_double_key",
        array=[[1.5, "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject double key in pair form",
    ),
    ArrayToObjectTest(
        id="pair_int64_key",
        array=[[Int64(1), "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Int64 key in pair form",
    ),
    ArrayToObjectTest(
        id="pair_decimal128_key",
        array=[[Decimal128("1"), "val"]],
        error_code=ARRAY_TO_OBJECT_PAIR_KEY_NOT_STRING_ERROR,
        msg="$arrayToObject should reject Decimal128 key in pair form",
    ),
]

# Property [Mixed Formats]: $arrayToObject rejects arrays mixing k/v doc and pair forms.
MIXED_FORMAT_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="mixed_kv_then_pair",
        array=[{"k": "price", "v": 24}, ["item", "apple"]],
        error_code=ARRAY_TO_OBJECT_MIXED_KV_THEN_PAIR_ERROR,
        msg="$arrayToObject should reject a k/v doc followed by a pair",
    ),
    ArrayToObjectTest(
        id="mixed_pair_then_kv",
        array=[["item", "apple"], {"k": "price", "v": 24}],
        error_code=ARRAY_TO_OBJECT_MIXED_PAIR_THEN_KV_ERROR,
        msg="$arrayToObject should reject a pair followed by a k/v doc",
    ),
]

# Property [Null Byte Key]: $arrayToObject rejects a key containing a null byte.
NULL_BYTE_KEY_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="null_byte_in_key_pair",
        array=[["a\x00b", "value"]],
        error_code=ARRAY_TO_OBJECT_NULL_BYTE_PAIR_KEY_ERROR,
        msg="$arrayToObject should reject a null byte in a key (pair form)",
    ),
    ArrayToObjectTest(
        id="null_byte_in_key_kv",
        array=[{"k": "a\x00b", "v": "value"}],
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
        collection, {"$arrayToObject": "$arr"}, {"arr": test.array}
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
    expr = {"$literal": test.array} if isinstance(test.array, list) else test.array
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
