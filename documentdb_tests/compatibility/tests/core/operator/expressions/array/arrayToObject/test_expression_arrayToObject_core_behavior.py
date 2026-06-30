"""
Core behavior tests for $arrayToObject expression.

Tests both input forms (k/v documents and two-element arrays), empty arrays,
duplicate keys, format equivalence, field ordering, case sensitivity,
value edge cases, key edge cases, and large inputs.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.array_test_case import (  # noqa: E501
    ArrayTestClass,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [K/V Form]: $arrayToObject builds an object from {k, v} document entries.
KV_FORM_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="kv_single_pair",
        arrays=[{"k": "a", "v": 1}],
        expected={"a": 1},
        msg="$arrayToObject should convert single k/v pair",
    ),
    ArrayTestClass(
        id="kv_multiple_pairs",
        arrays=[{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "c", "v": 3}],
        expected={"a": 1, "b": 2, "c": 3},
        msg="$arrayToObject should convert multiple k/v pairs",
    ),
    ArrayTestClass(
        id="kv_string_values",
        arrays=[{"k": "name", "v": "Alice"}, {"k": "city", "v": "Mycity"}],
        expected={"name": "Alice", "city": "Mycity"},
        msg="$arrayToObject should convert k/v pairs with string values",
    ),
    ArrayTestClass(
        id="kv_mixed_value_types",
        arrays=[
            {"k": "int", "v": 1},
            {"k": "str", "v": "hello"},
            {"k": "bool", "v": True},
            {"k": "null", "v": None},
        ],
        expected={"int": 1, "str": "hello", "bool": True, "null": None},
        msg="$arrayToObject should convert k/v pairs with mixed value types",
    ),
    ArrayTestClass(
        id="kv_nested_object_value",
        arrays=[{"k": "obj", "v": {"x": 1, "y": 2}}],
        expected={"obj": {"x": 1, "y": 2}},
        msg="$arrayToObject should convert k/v pair with nested object value",
    ),
    ArrayTestClass(
        id="kv_array_value",
        arrays=[{"k": "arr", "v": [1, 2, 3]}],
        expected={"arr": [1, 2, 3]},
        msg="$arrayToObject should convert k/v pair with array value",
    ),
]

# Property [Pair Form]: $arrayToObject builds an object from two-element [key, value] arrays.
TWO_ELEM_FORM_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="pair_single",
        arrays=[["a", 1]],
        expected={"a": 1},
        msg="$arrayToObject should convert single two-element pair",
    ),
    ArrayTestClass(
        id="pair_multiple",
        arrays=[["a", 1], ["b", 2], ["c", 3]],
        expected={"a": 1, "b": 2, "c": 3},
        msg="$arrayToObject should convert multiple two-element pairs",
    ),
    ArrayTestClass(
        id="pair_string_values",
        arrays=[["name", "Alice"], ["city", "Mycity"]],
        expected={"name": "Alice", "city": "Mycity"},
        msg="$arrayToObject should convert pairs with string values",
    ),
    ArrayTestClass(
        id="pair_mixed_value_types",
        arrays=[["int", 1], ["str", "hello"], ["bool", True], ["null", None]],
        expected={"int": 1, "str": "hello", "bool": True, "null": None},
        msg="$arrayToObject should convert pairs with mixed value types",
    ),
    ArrayTestClass(
        id="pair_nested_object_value",
        arrays=[["obj", {"x": 1, "y": 2}]],
        expected={"obj": {"x": 1, "y": 2}},
        msg="$arrayToObject should convert pair with nested object value",
    ),
    ArrayTestClass(
        id="pair_array_value",
        arrays=[["arr", [1, 2, 3]]],
        expected={"arr": [1, 2, 3]},
        msg="$arrayToObject should convert pair with array value",
    ),
]

# Property [Empty And Null]: $arrayToObject returns {} for an empty array and null for null input.
EMPTY_AND_NULL_ARRAY_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="empty_array",
        arrays=[],
        expected={},
        msg="$arrayToObject should return empty object for empty array",
    ),
    ArrayTestClass(
        id="null_array",
        arrays=None,
        expected=None,
        msg="$arrayToObject should return null for null array",
    ),
]

# Property [Duplicate Keys]: when keys repeat, $arrayToObject keeps the last value.
DUPLICATE_KEY_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="kv_duplicate_keys",
        arrays=[{"k": "a", "v": 1}, {"k": "a", "v": 2}],
        expected={"a": 2},
        msg="$arrayToObject should keep the last value for duplicate keys (k/v form)",
    ),
    ArrayTestClass(
        id="pair_duplicate_keys",
        arrays=[["a", 1], ["a", 2]],
        expected={"a": 2},
        msg="$arrayToObject should keep the last value for duplicate keys (pair form)",
    ),
    ArrayTestClass(
        id="kv_triple_duplicate",
        arrays=[{"k": "x", "v": 1}, {"k": "x", "v": 2}, {"k": "x", "v": 3}],
        expected={"x": 3},
        msg="$arrayToObject should keep the last of three duplicate keys",
    ),
    ArrayTestClass(
        id="pair_dup_different_types",
        arrays=[["a", 1], ["a", "hello"]],
        expected={"a": "hello"},
        msg="$arrayToObject should keep the last value even with different value types",
    ),
    ArrayTestClass(
        id="pair_dup_interspersed",
        arrays=[["a", 1], ["b", 2], ["a", 3]],
        expected={"a": 3, "b": 2},
        msg="$arrayToObject should keep the last value with interspersed duplicate keys",
    ),
    ArrayTestClass(
        id="kv_dup_interspersed",
        arrays=[{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "a", "v": 3}],
        expected={"a": 3, "b": 2},
        msg="$arrayToObject should keep the last value with interspersed duplicates (k/v form)",
    ),
    ArrayTestClass(
        id="kv_reversed_field_order",
        arrays=[{"v": "val", "k": "key"}],
        expected={"key": "val"},
        msg="$arrayToObject should work regardless of k/v field order in document",
    ),
]

# Property [Key Characters]: $arrayToObject accepts unicode, emoji, and spaced keys.
KEY_EDGE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="unicode_key",
        arrays=[{"k": "日本語", "v": 1}],
        expected={"日本語": 1},
        msg="$arrayToObject should accept a unicode key",
    ),
    ArrayTestClass(
        id="emoji_key",
        arrays=[{"k": "🔑", "v": "value"}],
        expected={"🔑": "value"},
        msg="$arrayToObject should accept an emoji key",
    ),
    ArrayTestClass(
        id="key_with_spaces",
        arrays=[["key with spaces", 1]],
        expected={"key with spaces": 1},
        msg="$arrayToObject should accept a key with spaces",
    ),
    ArrayTestClass(
        id="numeric_string_keys",
        arrays=[["0", "a"], ["1", "b"]],
        expected={"0": "a", "1": "b"},
        msg="$arrayToObject should treat numeric string keys as strings",
    ),
    ArrayTestClass(
        id="underscore_id_key",
        arrays=[["_id", 1]],
        expected={"_id": 1},
        msg="$arrayToObject should accept _id as a key",
    ),
    ArrayTestClass(
        id="operator_like_key",
        arrays=[["$set", 1]],
        expected={"$set": 1},
        msg="$arrayToObject should accept an operator-like key",
    ),
    ArrayTestClass(
        id="very_long_key",
        arrays=[["k" * 1024, 1]],
        expected={"k" * 1024: 1},
        msg="$arrayToObject should not truncate a very long key",
    ),
]

# Property [Field Ordering]: $arrayToObject preserves input order and treats keys case-sensitively.
EDGE_CASE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="output_field_order",
        arrays=[["z", 1], ["a", 2], ["m", 3]],
        expected={"z": 1, "a": 2, "m": 3},
        msg="$arrayToObject should preserve input field order in the output",
    ),
    ArrayTestClass(
        id="case_sensitive_keys_kv",
        arrays=[{"k": "price", "v": 24}, {"k": "PRICE", "v": 100}],
        expected={"price": 24, "PRICE": 100},
        msg="$arrayToObject should treat case-differing keys as distinct",
    ),
    ArrayTestClass(
        id="case_sensitive_keys_pair",
        arrays=[["price", 24], ["PRICE", 100]],
        expected={"price": 24, "PRICE": 100},
        msg="$arrayToObject should treat case-differing keys as distinct (pair form)",
    ),
    ArrayTestClass(
        id="deeply_nested_object_value",
        arrays=[["key", {"a": {"b": {"c": {"d": 1}}}}]],
        expected={"key": {"a": {"b": {"c": {"d": 1}}}}},
        msg="$arrayToObject should handle deeply nested object",
    ),
    ArrayTestClass(
        id="deeply_nested_array_value",
        arrays=[["key", [[[[1]]]]]],
        expected={"key": [[[[1]]]]},
        msg="$arrayToObject should handle deeply nested array",
    ),
    ArrayTestClass(
        id="empty_object_value",
        arrays=[["key", {}]],
        expected={"key": {}},
        msg="$arrayToObject should handle empty object value",
    ),
    ArrayTestClass(
        id="empty_array_value",
        arrays=[["key", []]],
        expected={"key": []},
        msg="$arrayToObject should handle empty array value",
    ),
    ArrayTestClass(
        id="empty_string_value",
        arrays=[["key", ""]],
        expected={"key": ""},
        msg="$arrayToObject should handle empty string value",
    ),
    ArrayTestClass(
        id="large_string_value",
        arrays=[["key", "x" * 10240]],
        expected={"key": "x" * 10240},
        msg="$arrayToObject should handle large string value",
    ),
]

ALL_TESTS = (
    KV_FORM_TESTS
    + TWO_ELEM_FORM_TESTS
    + EMPTY_AND_NULL_ARRAY_TESTS
    + DUPLICATE_KEY_TESTS
    + KEY_EDGE_TESTS
    + EDGE_CASE_TESTS
)

TEST_SUBSET_FOR_LITERAL = [
    KV_FORM_TESTS[0],
    KV_FORM_TESTS[3],
    TWO_ELEM_FORM_TESTS[0],
    EMPTY_AND_NULL_ARRAY_TESTS[0],
    DUPLICATE_KEY_TESTS[0],
    EDGE_CASE_TESTS[0],
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayToObject_literal(collection, test):
    """Test $arrayToObject with literal values."""
    result = execute_expression(collection, {"$arrayToObject": {"$literal": test.arrays}})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_arrayToObject_insert(collection, test):
    """Test $arrayToObject with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayToObject": "$arr"}, {"arr": test.arrays}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


def test_arrayToObject_large_array_two_element(collection):
    """Test $arrayToObject with 10,000 two-element pairs."""
    large_arr = [[f"key_{i}", i] for i in range(10_000)]
    expected = {f"key_{i}": i for i in range(10_000)}
    result = execute_expression(collection, {"$arrayToObject": {"$literal": large_arr}})
    assert_expression_result(
        result,
        expected=expected,
        msg="$arrayToObject should build a 10,000-field object from two-element pairs",
    )


def test_arrayToObject_large_array_kv(collection):
    """Test $arrayToObject with 10,000 k/v documents."""
    large_arr = [{"k": f"key_{i}", "v": i} for i in range(10_000)]
    expected = {f"key_{i}": i for i in range(10_000)}
    result = execute_expression(collection, {"$arrayToObject": {"$literal": large_arr}})
    assert_expression_result(
        result,
        expected=expected,
        msg="$arrayToObject should build a 10,000-field object from k/v documents",
    )
