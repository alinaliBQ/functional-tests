"""
Expression and field path tests for $arrayToObject expression.

Tests field path lookups, composite paths, key edge cases,
system variables, and null/missing handling.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Field path lookups
# ---------------------------------------------------------------------------
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_field_path",
        expression={"$arrayToObject": "$a.b"},
        doc={"a": {"b": [{"k": "x", "v": 1}]}},
        expected={"x": 1},
        msg="Should resolve nested field path",
    ),
    ExpressionTestCase(
        id="nonexistent_field_null",
        expression={"$arrayToObject": "$a.nonexistent"},
        doc={"a": {"missing": 1}},
        expected=None,
        msg="Non-existent field should return null",
    ),
    ExpressionTestCase(
        id="deeply_nested_field",
        expression={"$arrayToObject": "$a.b.c"},
        doc={"a": {"b": {"c": [{"k": "x", "v": 1}]}}},
        expected={"x": 1},
        msg="Should resolve deeply nested field path",
    ),
]

# ---------------------------------------------------------------------------
# Composite array path
# ---------------------------------------------------------------------------
COMPOSITE_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="composite_array_path",
        expression={"$arrayToObject": "$a.b"},
        doc={"a": [{"b": {"k": "x", "v": 1}}, {"b": {"k": "y", "v": 2}}]},
        expected={"x": 1, "y": 2},
        msg="Composite array path should resolve to valid k/v array",
    ),
]

# ---------------------------------------------------------------------------
# Key edge cases
# ---------------------------------------------------------------------------
KEY_EDGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="empty_string_key",
        expression={"$arrayToObject": "$arr"},
        doc={"arr": [{"k": "", "v": 1}]},
        expected={"": 1},
        msg="Should handle empty string key",
    ),
    ExpressionTestCase(
        id="key_with_dots",
        expression={"$arrayToObject": "$arr"},
        doc={"arr": [{"k": "a.b.c", "v": 1}]},
        expected={"a.b.c": 1},
        msg="Should handle key with dots",
    ),
    ExpressionTestCase(
        id="key_with_dollar",
        expression={"$arrayToObject": "$arr"},
        doc={"arr": [{"k": "$field", "v": 1}]},
        expected={"$field": 1},
        msg="Should handle key with dollar sign",
    ),
]

# ---------------------------------------------------------------------------
# $let and system variables
# ---------------------------------------------------------------------------
SYSTEM_VAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="let_variable",
        expression={"$let": {"vars": {"arr": "$arr"}, "in": {"$arrayToObject": "$$arr"}}},
        doc={"arr": [["a", 1]]},
        expected={"a": 1},
        msg="Should work with $let variable",
    ),
    ExpressionTestCase(
        id="root_variable",
        expression={"$arrayToObject": "$$ROOT.pairs"},
        doc={"_id": 1, "pairs": [["a", 1]]},
        expected={"a": 1},
        msg="Should work with $$ROOT",
    ),
    ExpressionTestCase(
        id="current_variable",
        expression={"$arrayToObject": "$$CURRENT.pairs"},
        doc={"_id": 2, "pairs": [["a", 1]]},
        expected={"a": 1},
        msg="$$CURRENT should be equivalent to field path",
    ),
]

# ---------------------------------------------------------------------------
# Null/missing via expression
# ---------------------------------------------------------------------------
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_field",
        expression={"$arrayToObject": "$nonexistent"},
        doc={"other": 1},
        expected=None,
        msg="Missing field should return null",
    ),
    ExpressionTestCase(
        id="missing_input_type_is_null",
        expression={"$type": {"$arrayToObject": "$nonexistent"}},
        doc={"x": 1},
        expected="null",
        msg="Missing field should produce null type",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + COMPOSITE_PATH_TESTS
    + KEY_EDGE_TESTS
    + SYSTEM_VAR_TESTS
    + NULL_MISSING_EXPR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_arrayToObject_expression(collection, test):
    """Test $arrayToObject with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
