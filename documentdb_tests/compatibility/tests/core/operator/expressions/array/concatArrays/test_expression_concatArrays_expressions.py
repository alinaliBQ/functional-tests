"""
Expression and field path tests for $concatArrays expression.

Tests field path lookups, composite paths, system variables,
and null/missing propagation via expressions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import CONCAT_ARRAYS_NOT_ARRAY_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Field path lookups
# ---------------------------------------------------------------------------
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_field_path",
        expression={"$concatArrays": ["$a.b", "$a.c"]},
        doc={"a": {"b": [1, 2], "c": [3, 4]}},
        expected=[1, 2, 3, 4],
        msg="Should resolve nested field paths",
    ),
    ExpressionTestCase(
        id="deeply_nested_field",
        expression={"$concatArrays": ["$a.b.c", "$a.b.d"]},
        doc={"a": {"b": {"c": [10], "d": [20]}}},
        expected=[10, 20],
        msg="Should resolve deeply nested field paths",
    ),
    ExpressionTestCase(
        id="nonexistent_field_null",
        expression={"$concatArrays": ["$a.nonexistent", "$b"]},
        doc={"a": {"missing": 1}, "b": [1]},
        expected=None,
        msg="Non-existent field should propagate null",
    ),
    ExpressionTestCase(
        id="array_index_path",
        expression={"$concatArrays": ["$a.0", [5]]},
        doc={"a": [[1, 2], [3, 4]]},
        expected=[5],
        msg="$a.0 resolves to [] in expression context",
    ),
    ExpressionTestCase(
        id="nonexistent_nested_path_empty",
        expression={"$concatArrays": ["$f.x", [3]]},
        doc={"f": [{"g": 1}, {"g": 2}]},
        expected=[3],
        msg="Non-existent nested path resolves to empty array",
    ),
    ExpressionTestCase(
        id="nested_array_of_object_path",
        expression={"$concatArrays": ["$a.b.c", [3]]},
        doc={"a": {"b": [{"c": [1]}, {"c": [2]}]}},
        expected=[[1], [2], 3],
        msg="Deep nested path resolved",
    ),
]

# ---------------------------------------------------------------------------
# Composite array paths
# ---------------------------------------------------------------------------
COMPOSITE_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="composite_array",
        expression={"$concatArrays": ["$x.y", [100]]},
        doc={"x": [{"y": 10}, {"y": 20}]},
        expected=[10, 20, 100],
        msg="Composite array path from array-of-objects",
    ),
    ExpressionTestCase(
        id="composite_path_tags",
        expression={"$concatArrays": ["$items.tags", ["d"]]},
        doc={"items": [{"tags": ["a", "b"]}, {"tags": ["c"]}]},
        expected=[["a", "b"], ["c"], "d"],
        msg="$items.tags resolves to array of arrays",
    ),
]

# ---------------------------------------------------------------------------
# $let and system variables
# ---------------------------------------------------------------------------
LET_AND_VARIABLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="let_variable",
        expression={
            "$let": {
                "vars": {"a": "$arr1", "b": "$arr2"},
                "in": {"$concatArrays": ["$$a", "$$b"]},
            }
        },
        doc={"arr1": [1, 2], "arr2": [3, 4]},
        expected=[1, 2, 3, 4],
        msg="Should work with $let variables",
    ),
    ExpressionTestCase(
        id="root_variable",
        expression={"$concatArrays": ["$$ROOT.a", "$$ROOT.b"]},
        doc={"_id": 1, "a": [1], "b": [2]},
        expected=[1, 2],
        msg="Should work with $$ROOT",
    ),
    ExpressionTestCase(
        id="current_variable",
        expression={"$concatArrays": ["$$CURRENT.a", "$$CURRENT.b"]},
        doc={"_id": 2, "a": [1], "b": [2]},
        expected=[1, 2],
        msg="$$CURRENT should be equivalent to field path",
    ),
    ExpressionTestCase(
        id="let_null_variable",
        expression={
            "$let": {
                "vars": {"x": None},
                "in": {"$concatArrays": ["$$x", [1]]},
            }
        },
        doc={"_placeholder": 1},
        expected=None,
        msg="$let null variable returns null",
    ),
]

# ---------------------------------------------------------------------------
# Null/missing via expression
# ---------------------------------------------------------------------------
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_field",
        expression={"$concatArrays": ["$nonexistent", [1]]},
        doc={"other": 1},
        expected=None,
        msg="Missing field should propagate null",
    ),
    ExpressionTestCase(
        id="missing_input_type_is_null",
        expression={"$type": {"$concatArrays": ["$nonexistent", [1]]}},
        doc={"x": 1},
        expected="null",
        msg="Missing field should produce null type",
    ),
    ExpressionTestCase(
        id="remove_variable",
        expression={"$concatArrays": ["$$REMOVE", [1]]},
        doc={"x": 1},
        expected=None,
        msg="$$REMOVE propagates null",
    ),
    ExpressionTestCase(
        id="field_ref_wrapped_non_array",
        expression={"$concatArrays": ["$a", [1]]},
        doc={"a": 1},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Field resolving to non-array should error",
    ),
    ExpressionTestCase(
        id="missing_first_field",
        expression={"$concatArrays": ["$a", "$b"]},
        doc={"b": [1]},
        expected=None,
        msg="Missing first field returns null",
    ),
    ExpressionTestCase(
        id="missing_last_field",
        expression={"$concatArrays": ["$a", "$b"]},
        doc={"a": [1]},
        expected=None,
        msg="Missing last field returns null",
    ),
    ExpressionTestCase(
        id="missing_middle_field",
        expression={"$concatArrays": ["$a", "$b", "$c"]},
        doc={"a": [1], "c": [3]},
        expected=None,
        msg="Missing middle field returns null",
    ),
    ExpressionTestCase(
        id="all_missing_fields",
        expression={"$concatArrays": ["$a", "$b"]},
        doc={"_placeholder": 1},
        expected=None,
        msg="All missing fields returns null",
    ),
    ExpressionTestCase(
        id="explicit_null_field",
        expression={"$concatArrays": ["$a", "$b"]},
        doc={"a": None, "b": [1]},
        expected=None,
        msg="Explicit null field returns null",
    ),
    ExpressionTestCase(
        id="missing_plus_null",
        expression={"$concatArrays": ["$not_a_field", "$null_val"]},
        doc={"null_val": None},
        expected=None,
        msg="Missing + null returns null",
    ),
    ExpressionTestCase(
        id="null_precedes_non_array",
        expression={"$concatArrays": ["$arr", "$null_val", "$int_val"]},
        doc={"arr": [1, 2], "null_val": None, "int_val": 42},
        expected=None,
        msg="Null precedes non-array type error",
    ),
    ExpressionTestCase(
        id="null_result_type_is_null",
        expression={"$type": {"$concatArrays": ["$a", "$nonexistent"]}},
        doc={"a": [1]},
        expected="null",
        msg="$type returns 'null' not 'missing'",
    ),
]

# ---------------------------------------------------------------------------
# Self-composition
# ---------------------------------------------------------------------------
SELF_COMPOSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_concatArrays",
        expression={"$concatArrays": [{"$concatArrays": ["$a", "$b"]}, "$c"]},
        doc={"a": [1], "b": [2], "c": [3]},
        expected=[1, 2, 3],
        msg="Nested $concatArrays should work",
    ),
    ExpressionTestCase(
        id="double_nested_concatArrays",
        expression={
            "$concatArrays": [{"$concatArrays": ["$a", "$b"]}, {"$concatArrays": ["$c", "$d"]}]
        },
        doc={"a": [1], "b": [2], "c": [3], "d": [4]},
        expected=[1, 2, 3, 4],
        msg="Both args are nested $concatArrays",
    ),
    ExpressionTestCase(
        id="triple_depth_concatArrays",
        expression={
            "$concatArrays": [{"$concatArrays": [{"$concatArrays": ["$a", "$b"]}, "$c"]}, "$d"]
        },
        doc={"a": [1], "b": [2], "c": [3], "d": [4]},
        expected=[1, 2, 3, 4],
        msg="Triple nesting depth",
    ),
]

# ---------------------------------------------------------------------------
# Same field referenced multiple times
# ---------------------------------------------------------------------------
SAME_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="same_field_twice",
        expression={"$concatArrays": ["$a", "$a"]},
        doc={"a": [1, 2, 3]},
        expected=[1, 2, 3, 1, 2, 3],
        msg="Same field twice doubles elements",
    ),
    ExpressionTestCase(
        id="same_field_three_times",
        expression={"$concatArrays": ["$a", "$a", "$a"]},
        doc={"a": [1]},
        expected=[1, 1, 1],
        msg="Same field three times triples elements",
    ),
    ExpressionTestCase(
        id="self_concat_mixed_types",
        expression={"$concatArrays": ["$a", "$a"]},
        doc={"a": [42, "string", {"key": "value"}, [1, 2], True]},
        expected=[
            42,
            "string",
            {"key": "value"},
            [1, 2],
            True,
            42,
            "string",
            {"key": "value"},
            [1, 2],
            True,
        ],
        msg="Self-concat preserves all types",
    ),
]

# ---------------------------------------------------------------------------
# Array expression and object expression inputs
# ---------------------------------------------------------------------------
EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="array_expression_input",
        expression={"$concatArrays": [["$x", "$y"], [3]]},
        doc={"x": 1, "y": 2},
        expected=[1, 2, 3],
        msg="Array expression with field refs resolved",
    ),
    ExpressionTestCase(
        id="object_expression_input",
        expression={"$concatArrays": [{"a": "$x"}]},
        doc={"x": 1},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="Object expression is not array",
    ),
    ExpressionTestCase(
        id="literal_then_field",
        expression={"$concatArrays": [[1, 2, 3], "$a"]},
        doc={"a": [1, 2]},
        expected=[1, 2, 3, 1, 2],
        msg="Literal + field order preserved",
    ),
    ExpressionTestCase(
        id="field_then_literal",
        expression={"$concatArrays": ["$a", [1, 2, 3]]},
        doc={"a": [1, 2]},
        expected=[1, 2, 1, 2, 3],
        msg="Field + literal order preserved",
    ),
    ExpressionTestCase(
        id="four_fields_with_empty_and_literal",
        expression={"$concatArrays": ["$a", "$b", "$c", "$d", [], ["array"]]},
        doc={"a": [1, 2], "b": [3, 4], "c": [5, 6], "d": []},
        expected=[1, 2, 3, 4, 5, 6, "array"],
        msg="Multiple fields + literals concatenated",
    ),
]

# ---------------------------------------------------------------------------
# Special object keys
# ---------------------------------------------------------------------------
SPECIAL_KEY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="special_object_keys",
        expression={"$concatArrays": ["$a", "$b"]},
        doc={"a": [{"a.b": 1}], "b": [{"$x": 2}]},
        expected=[{"a.b": 1}, {"$x": 2}],
        msg="Objects with special keys preserved",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + COMPOSITE_PATH_TESTS
    + LET_AND_VARIABLE_TESTS
    + NULL_MISSING_EXPR_TESTS
    + SELF_COMPOSITION_TESTS
    + SAME_FIELD_TESTS
    + EXPRESSION_INPUT_TESTS
    + SPECIAL_KEY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_concatArrays_expression(collection, test):
    """Test $concatArrays with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
