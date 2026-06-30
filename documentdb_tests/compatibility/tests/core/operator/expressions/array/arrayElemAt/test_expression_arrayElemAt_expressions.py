"""
Expression and field path tests for $arrayElemAt expression.

Tests nested expressions, field path lookups, composite paths,
and path through array of objects.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.error_codes import ARRAY_ELEM_AT_INDEX_TYPE_ERROR


# Nested expressions
@pytest.mark.parametrize(
    "expression,expected",
    [
        # 2D array access: arr[1][0]
        ({"$arrayElemAt": [{"$arrayElemAt": [[[10, 20], [30, 40]], 1]}, 0]}, 30),
        # 3D array access: arr[1][0][1]
        (
            {
                "$arrayElemAt": [
                    {
                        "$arrayElemAt": [
                            {"$arrayElemAt": [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]], 1]},
                            0,
                        ]
                    },
                    1,
                ]
            },
            6,
        ),
        # 4D array access: arr[1][1][0][1]
        (
            {
                "$arrayElemAt": [
                    {
                        "$arrayElemAt": [
                            {
                                "$arrayElemAt": [
                                    {
                                        "$arrayElemAt": [
                                            [
                                                [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
                                                [[[9, 10], [11, 12]], [[13, 14], [15, 16]]],
                                            ],
                                            1,
                                        ]
                                    },
                                    1,
                                ]
                            },
                            0,
                        ]
                    },
                    1,
                ]
            },
            14,
        ),
    ],
    ids=["nested_2d_access", "nested_3d_access", "nested_4d_access"],
)
def test_arrayElemAt_nested_expression(collection, expression, expected):
    """Test $arrayElemAt composed with other expressions."""
    result = execute_expression(collection, expression)
    assert_expression_result(result, expected=expected)


# Field path lookups
@pytest.mark.parametrize(
    "document,array_ref,idx,expected",
    [
        ({"a": {"b": [10, 20, 30]}}, "$a.b", 1, 20),
        ({"a": {"missing": 1}}, "$a.nonexistent", 0, None),
        ({"a": {"b": {"c": [5, 6, 7]}}}, "$a.b.c", -1, 7),
    ],
    ids=["nested_field_path", "nonexistent_field_null", "deeply_nested_field"],
)
def test_arrayElemAt_field_lookup(collection, document, array_ref, idx, expected):
    """Test $arrayElemAt with field path lookups from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": [array_ref, idx]}, document
    )
    assert_expression_result(result, expected=expected)


# Field path: path through array of objects
def test_arrayElemAt_path_through_array_of_objects(collection):
    """Test $arrayElemAt where field path traverses array of objects."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$a.b", 0]}, {"a": [{"b": 10}, {"b": 20}]}
    )
    assert_expression_result(result, expected=10)


# Field path: composite path for index
def test_arrayElemAt_composite_path_for_index(collection):
    """Test $arrayElemAt with nested field path as index."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": [[10, 20, 30], "$a.b"]}, {"a": {"b": 1}}
    )
    assert_expression_result(result, expected=20)


def test_arrayElemAt_composite_array_as_array(collection):
    """Test $arrayElemAt with composite array from $x.y as the array argument."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$x.y", 1]}, {"x": [{"y": 10}, {"y": 20}, {"y": 30}]}
    )
    assert_expression_result(result, expected=20)


def test_arrayElemAt_composite_array_as_index(collection):
    """Test $arrayElemAt rejects composite array from $x.y as the index argument."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": [[10, 20, 30], "$x.y"]}, {"x": [{"y": 0}, {"y": 1}]}
    )
    assert_expression_result(result, error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR)


# Composite path with Decimal128 indices and OOB
@pytest.mark.parametrize(
    "idx,expected",
    [
        (Decimal128("0"), 1),
        (Decimal128("-1"), 3),
    ],
    ids=["composite_decimal128_pos", "composite_decimal128_neg"],
)
def test_arrayElemAt_composite_path_decimal128(collection, idx, expected):
    """Test $arrayElemAt with composite path $a.b and Decimal128 index."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$a.b", idx]}, {"a": [{"b": 1}, {"b": 2}, {"b": 3}]}
    )
    assert_expression_result(result, expected=expected)


@pytest.mark.parametrize(
    "idx",
    [Decimal128("4"), Decimal128("-4")],
    ids=["composite_decimal128_oob_pos", "composite_decimal128_oob_neg"],
)
def test_arrayElemAt_composite_path_decimal128_oob(collection, idx):
    """Test $arrayElemAt with composite path $a.b and Decimal128 OOB index."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": ["$a.b", idx]}, {"a": [{"b": 1}, {"b": 2}, {"b": 3}]}
    )
    assertSuccess(result, [{}])
