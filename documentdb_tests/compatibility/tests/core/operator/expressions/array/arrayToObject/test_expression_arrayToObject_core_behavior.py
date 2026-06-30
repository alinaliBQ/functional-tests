"""
Core behavior tests for $arrayToObject expression.

Tests both input forms (k/v documents and two-element arrays), empty arrays,
duplicate keys, format equivalence, field ordering, case sensitivity,
value edge cases, key edge cases, and large inputs.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.array.arrayToObject.utils.arrayToObject_common import (  # noqa: E501
    ArrayToObjectTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Success: k/v document form — [{k: <key>, v: <value>}, ...]
# ---------------------------------------------------------------------------
KV_FORM_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="kv_single_pair",
        array=[{"k": "a", "v": 1}],
        expected={"a": 1},
        msg="Should convert single k/v pair",
    ),
    ArrayToObjectTest(
        id="kv_multiple_pairs",
        array=[{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "c", "v": 3}],
        expected={"a": 1, "b": 2, "c": 3},
        msg="Should convert multiple k/v pairs",
    ),
    ArrayToObjectTest(
        id="kv_string_values",
        array=[{"k": "name", "v": "Alice"}, {"k": "city", "v": "Mycity"}],
        expected={"name": "Alice", "city": "Mycity"},
        msg="Should convert k/v pairs with string values",
    ),
    ArrayToObjectTest(
        id="kv_mixed_value_types",
        array=[
            {"k": "int", "v": 1},
            {"k": "str", "v": "hello"},
            {"k": "bool", "v": True},
            {"k": "null", "v": None},
        ],
        expected={"int": 1, "str": "hello", "bool": True, "null": None},
        msg="Should convert k/v pairs with mixed value types",
    ),
    ArrayToObjectTest(
        id="kv_nested_object_value",
        array=[{"k": "obj", "v": {"x": 1, "y": 2}}],
        expected={"obj": {"x": 1, "y": 2}},
        msg="Should convert k/v pair with nested object value",
    ),
    ArrayToObjectTest(
        id="kv_array_value",
        array=[{"k": "arr", "v": [1, 2, 3]}],
        expected={"arr": [1, 2, 3]},
        msg="Should convert k/v pair with array value",
    ),
]

# ---------------------------------------------------------------------------
# Success: two-element array form — [[<key>, <value>], ...]
# ---------------------------------------------------------------------------
TWO_ELEM_FORM_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="pair_single",
        array=[["a", 1]],
        expected={"a": 1},
        msg="Should convert single two-element pair",
    ),
    ArrayToObjectTest(
        id="pair_multiple",
        array=[["a", 1], ["b", 2], ["c", 3]],
        expected={"a": 1, "b": 2, "c": 3},
        msg="Should convert multiple two-element pairs",
    ),
    ArrayToObjectTest(
        id="pair_string_values",
        array=[["name", "Alice"], ["city", "Mycity"]],
        expected={"name": "Alice", "city": "Mycity"},
        msg="Should convert pairs with string values",
    ),
    ArrayToObjectTest(
        id="pair_mixed_value_types",
        array=[["int", 1], ["str", "hello"], ["bool", True], ["null", None]],
        expected={"int": 1, "str": "hello", "bool": True, "null": None},
        msg="Should convert pairs with mixed value types",
    ),
    ArrayToObjectTest(
        id="pair_nested_object_value",
        array=[["obj", {"x": 1, "y": 2}]],
        expected={"obj": {"x": 1, "y": 2}},
        msg="Should convert pair with nested object value",
    ),
    ArrayToObjectTest(
        id="pair_array_value",
        array=[["arr", [1, 2, 3]]],
        expected={"arr": [1, 2, 3]},
        msg="Should convert pair with array value",
    ),
]

# ---------------------------------------------------------------------------
# Success: empty or null
# ---------------------------------------------------------------------------
EMPTY_AND_NULL_ARRAY_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="empty_array",
        array=[],
        expected={},
        msg="Should return empty object for empty array",
    ),
    ArrayToObjectTest(
        id="null_array",
        array=None,
        expected=None,
        msg="Should return null for null array",
    ),
]

# ---------------------------------------------------------------------------
# Success: duplicate keys — last value wins
# ---------------------------------------------------------------------------
DUPLICATE_KEY_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="kv_duplicate_keys",
        array=[{"k": "a", "v": 1}, {"k": "a", "v": 2}],
        expected={"a": 2},
        msg="Last value should win for duplicate keys (k/v form)",
    ),
    ArrayToObjectTest(
        id="pair_duplicate_keys",
        array=[["a", 1], ["a", 2]],
        expected={"a": 2},
        msg="Last value should win for duplicate keys (pair form)",
    ),
    ArrayToObjectTest(
        id="kv_triple_duplicate",
        array=[{"k": "x", "v": 1}, {"k": "x", "v": 2}, {"k": "x", "v": 3}],
        expected={"x": 3},
        msg="Last of three duplicate keys should win",
    ),
    ArrayToObjectTest(
        id="pair_dup_different_types",
        array=[["a", 1], ["a", "hello"]],
        expected={"a": "hello"},
        msg="Last value should win even with different value types",
    ),
    ArrayToObjectTest(
        id="pair_dup_interspersed",
        array=[["a", 1], ["b", 2], ["a", 3]],
        expected={"a": 3, "b": 2},
        msg="Last value should win with interspersed duplicate keys",
    ),
    ArrayToObjectTest(
        id="kv_dup_interspersed",
        array=[{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "a", "v": 3}],
        expected={"a": 3, "b": 2},
        msg="Last value should win with interspersed duplicates (k/v form)",
    ),
    ArrayToObjectTest(
        id="kv_reversed_field_order",
        array=[{"v": "val", "k": "key"}],
        expected={"key": "val"},
        msg="Should work regardless of k/v field order in document",
    ),
]

# ---------------------------------------------------------------------------
# Success: key edge cases (unicode, emoji, spaces)
# ---------------------------------------------------------------------------
KEY_EDGE_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="unicode_key",
        array=[{"k": "日本語", "v": 1}],
        expected={"日本語": 1},
        msg="Unicode key should be valid",
    ),
    ArrayToObjectTest(
        id="emoji_key",
        array=[{"k": "🔑", "v": "value"}],
        expected={"🔑": "value"},
        msg="Emoji key should be valid",
    ),
    ArrayToObjectTest(
        id="key_with_spaces",
        array=[["key with spaces", 1]],
        expected={"key with spaces": 1},
        msg="Key with spaces should be valid",
    ),
    ArrayToObjectTest(
        id="numeric_string_keys",
        array=[["0", "a"], ["1", "b"]],
        expected={"0": "a", "1": "b"},
        msg="Numeric string keys should be treated as strings",
    ),
    ArrayToObjectTest(
        id="underscore_id_key",
        array=[["_id", 1]],
        expected={"_id": 1},
        msg="_id key should be valid",
    ),
    ArrayToObjectTest(
        id="operator_like_key",
        array=[["$set", 1]],
        expected={"$set": 1},
        msg="Operator-like key should be valid",
    ),
    ArrayToObjectTest(
        id="very_long_key",
        array=[["k" * 1024, 1]],
        expected={"k" * 1024: 1},
        msg="Very long key should not be truncated",
    ),
]

# ---------------------------------------------------------------------------
# Success: field ordering, case sensitivity, value/key edge cases
# ---------------------------------------------------------------------------
EDGE_CASE_TESTS: list[ArrayToObjectTest] = [
    ArrayToObjectTest(
        id="output_field_order",
        array=[["z", 1], ["a", 2], ["m", 3]],
        expected={"z": 1, "a": 2, "m": 3},
        msg="Output field order should match input order",
    ),
    ArrayToObjectTest(
        id="case_sensitive_keys_kv",
        array=[{"k": "price", "v": 24}, {"k": "PRICE", "v": 100}],
        expected={"price": 24, "PRICE": 100},
        msg="Case-differing keys should be distinct",
    ),
    ArrayToObjectTest(
        id="case_sensitive_keys_pair",
        array=[["price", 24], ["PRICE", 100]],
        expected={"price": 24, "PRICE": 100},
        msg="Case-differing keys should be distinct (pair form)",
    ),
    ArrayToObjectTest(
        id="deeply_nested_object_value",
        array=[["key", {"a": {"b": {"c": {"d": 1}}}}]],
        expected={"key": {"a": {"b": {"c": {"d": 1}}}}},
        msg="Should handle deeply nested object",
    ),
    ArrayToObjectTest(
        id="deeply_nested_array_value",
        array=[["key", [[[[1]]]]]],
        expected={"key": [[[[1]]]]},
        msg="Should handle deeply nested array",
    ),
    ArrayToObjectTest(
        id="empty_object_value",
        array=[["key", {}]],
        expected={"key": {}},
        msg="Should handle empty object value",
    ),
    ArrayToObjectTest(
        id="empty_array_value",
        array=[["key", []]],
        expected={"key": []},
        msg="Should handle empty array value",
    ),
    ArrayToObjectTest(
        id="empty_string_value",
        array=[["key", ""]],
        expected={"key": ""},
        msg="Should handle empty string value",
    ),
    ArrayToObjectTest(
        id="large_string_value",
        array=[["key", "x" * 10240]],
        expected={"key": "x" * 10240},
        msg="Should handle large string value",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_TESTS = (
    KV_FORM_TESTS
    + TWO_ELEM_FORM_TESTS
    + EMPTY_AND_NULL_ARRAY_TESTS
    + DUPLICATE_KEY_TESTS
    + KEY_EDGE_TESTS
    + EDGE_CASE_TESTS
)

TEST_SUBSET_FOR_LITERAL = [
    KV_FORM_TESTS[0],  # kv_single_pair
    KV_FORM_TESTS[3],  # kv_mixed_value_types
    TWO_ELEM_FORM_TESTS[0],  # pair_single
    EMPTY_AND_NULL_ARRAY_TESTS[0],  # empty_array
    DUPLICATE_KEY_TESTS[0],  # kv_duplicate_keys
    EDGE_CASE_TESTS[0],  # output_field_order
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_arrayToObject_literal(collection, test):
    """Test $arrayToObject with literal values."""
    result = execute_expression(collection, {"$arrayToObject": {"$literal": test.array}})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_arrayToObject_insert(collection, test):
    """Test $arrayToObject with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayToObject": "$arr"}, {"arr": test.array}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# ---------------------------------------------------------------------------
# Large inputs — standalone because assertSuccess+transform is used to
# spot-check a few fields instead of comparing the full 10K-field object.
# ---------------------------------------------------------------------------
def test_arrayToObject_large_array_two_element(collection):
    """Test $arrayToObject with 10,000 two-element pairs."""
    large_arr = [[f"key_{i}", i] for i in range(10000)]
    result = execute_expression(collection, {"$arrayToObject": {"$literal": large_arr}})
    assertSuccess(
        result,
        expected=[{"has_10k": True, "first": 0, "last": 9999}],
        transform=lambda batch: [
            {
                "has_10k": len(batch[0]["result"]) == 10000,
                "first": batch[0]["result"]["key_0"],
                "last": batch[0]["result"]["key_9999"],
            }
        ],
        msg="Should produce 10,000 fields with correct values",
    )


def test_arrayToObject_large_array_kv(collection):
    """Test $arrayToObject with 10,000 k/v documents."""
    large_arr = [{"k": f"key_{i}", "v": i} for i in range(10000)]
    result = execute_expression(collection, {"$arrayToObject": {"$literal": large_arr}})
    assertSuccess(
        result,
        expected=[{"has_10k": True, "first": 0, "last": 9999}],
        transform=lambda batch: [
            {
                "has_10k": len(batch[0]["result"]) == 10000,
                "first": batch[0]["result"]["key_0"],
                "last": batch[0]["result"]["key_9999"],
            }
        ],
        msg="Should produce 10,000 fields with correct values in k/v format",
    )
