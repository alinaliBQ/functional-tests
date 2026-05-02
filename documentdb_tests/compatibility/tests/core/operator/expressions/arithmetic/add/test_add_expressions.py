"""Tests for $add expression types, field paths, nesting, variables, and system variables."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AddExprTest(BaseTestCase):
    """Test case for $add expression types."""

    expression: Any = None
    doc: Optional[dict] = None


# --- Literal and nested expression input ---

LITERAL_TESTS: list[AddExprTest] = [
    AddExprTest(
        "literal_values", expression={"$add": [1, 2]}, expected=3, msg="Should add literal values"
    ),
    AddExprTest(
        "nested_expression",
        expression={"$add": [{"$abs": -5}, 3]},
        expected=8,
        msg="Should accept nested expression input",
    ),
    AddExprTest(
        "nested_add",
        expression={"$add": [{"$add": [1, 2]}, {"$add": [3, 4]}]},
        expected=10,
        msg="Should handle nested $add",
    ),
    AddExprTest(
        "deep_nested_add",
        expression={"$add": [1, {"$add": [2, {"$add": [3, 4]}]}]},
        expected=10,
        msg="Should handle deeply nested $add",
    ),
    AddExprTest(
        "nested_mixed_types",
        expression={"$add": [{"$add": [1, Int64(2)]}, Decimal128("3")]},
        expected=Decimal128("6"),
        msg="Should handle nested $add with type promotion",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_add_literal_and_nesting(collection, test):
    """Test $add with literal values and nested expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Field path input ---

FIELD_PATH_TESTS: list[AddExprTest] = [
    AddExprTest(
        "simple_fields",
        expression={"$add": ["$a", "$b"]},
        doc={"a": 5, "b": 3},
        expected=8,
        msg="Should add field path values",
    ),
    AddExprTest(
        "field_int_long",
        expression={"$add": ["$a", "$b"]},
        doc={"a": 1, "b": Int64(2)},
        expected=Int64(3),
        msg="Should promote int + long from field paths",
    ),
    AddExprTest(
        "field_date_int",
        expression={"$add": ["$d", "$n"]},
        doc={"d": datetime(2024, 1, 1), "n": 1000},
        expected=datetime(2024, 1, 1, 0, 0, 1),
        msg="Should add date + int from field paths",
    ),
    AddExprTest(
        "field_null",
        expression={"$add": ["$a", "$b"]},
        doc={"a": None, "b": 5},
        expected=None,
        msg="Should return null when field resolves to null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_PATH_TESTS))
def test_add_field_paths(collection, test):
    """Test $add with field path references."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Field path error cases ---

FIELD_PATH_ERROR_TESTS: list[AddExprTest] = [
    AddExprTest(
        "field_string_error",
        expression={"$add": ["$a", "$b"]},
        doc={"a": "hello", "b": 5},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject field resolving to string",
    ),
    AddExprTest(
        "composite_array_error",
        expression={"$add": ["$a.b"]},
        doc={"a": [{"b": 1}, {"b": 2}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject composite array path resolving to array",
    ),
    AddExprTest(
        "array_index_error",
        expression={"$add": ["$a.0.b", 1]},
        doc={"a": [{"b": 5}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array index path in expression context",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_PATH_ERROR_TESTS))
def test_add_field_path_errors(collection, test):
    """Test $add rejects invalid field path types."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


# --- Expression type errors (array/object as input) ---

EXPR_TYPE_ERROR_TESTS: list[AddExprTest] = [
    AddExprTest(
        "array_expression",
        expression={"$add": [["$a", "$b"]]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array expression input",
    ),
    AddExprTest(
        "object_expression",
        expression={"$add": [{"a": "$x"}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject object expression input",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EXPR_TYPE_ERROR_TESTS))
def test_add_expression_type_errors(collection, test):
    """Test $add rejects array and object expression inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


# --- Missing field behavior ---

MISSING_FIELD_TESTS: list[AddExprTest] = [
    AddExprTest(
        "missing_first",
        expression={"$add": ["$nonexistent", 1]},
        doc={},
        expected=None,
        msg="Should return null for missing field in first position",
    ),
    AddExprTest(
        "missing_second",
        expression={"$add": [1, "$nonexistent"]},
        doc={},
        expected=None,
        msg="Should return null for missing field in second position",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MISSING_FIELD_TESTS))
def test_add_missing_fields(collection, test):
    """Test $add missing field behavior."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- System variables ---

SYSTEM_VAR_TESTS: list[AddExprTest] = [
    AddExprTest(
        "root_field",
        expression={"$add": ["$$ROOT.a", 1]},
        doc={"a": 5},
        expected=6,
        msg="Should access field via $$ROOT",
    ),
    AddExprTest(
        "current_field",
        expression={"$add": ["$$CURRENT.a", 1]},
        doc={"a": 5},
        expected=6,
        msg="Should access field via $$CURRENT",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SYSTEM_VAR_TESTS))
def test_add_system_variables(collection, test):
    """Test $add with system variables."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- $let variables ---

LET_TESTS: list[AddExprTest] = [
    AddExprTest(
        "let_single",
        expression={"$let": {"vars": {"x": 5}, "in": {"$add": ["$$x", 1]}}},
        expected=6,
        msg="Should use $let variable in $add",
    ),
    AddExprTest(
        "let_multi",
        expression={"$let": {"vars": {"x": 5, "y": 3}, "in": {"$add": ["$$x", "$$y"]}}},
        expected=8,
        msg="Should use multiple $let variables in $add",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LET_TESTS))
def test_add_let_variables(collection, test):
    """Test $add with $let variables."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
