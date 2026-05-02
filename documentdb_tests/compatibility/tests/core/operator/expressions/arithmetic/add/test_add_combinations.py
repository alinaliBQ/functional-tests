"""Tests for $add in combination with other operators and multi-stage pipelines."""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AddComboTest(BaseTestCase):
    """Test case for $add operator combinations."""

    expression: Any = None


# --- $add inside other operators ---

OPERATOR_COMBO_TESTS: list[AddComboTest] = [
    AddComboTest(
        "inside_cond",
        expression={"$cond": [True, {"$add": [1, 2]}, 0]},
        expected=3,
        msg="Should work inside $cond",
    ),
    AddComboTest(
        "input_to_abs",
        expression={"$abs": {"$add": [-5, 2]}},
        expected=3,
        msg="Should work as input to $abs",
    ),
    AddComboTest(
        "input_to_gt",
        expression={"$gt": [{"$add": [5, 6]}, 10]},
        expected=True,
        msg="Should work as input to comparison",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OPERATOR_COMBO_TESTS))
def test_add_operator_combinations(collection, test):
    """Test $add combined with other operators."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- $add inside $ifNull with missing fields ---


def test_add_inside_ifnull(collection):
    """Test $add inside $ifNull returns fallback when fields are missing."""
    collection.insert_one({})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "r": {"$ifNull": [{"$add": ["$a", "$b"]}, 0]}}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result, [{"r": 0}], msg="Should return ifNull fallback when add operands are missing"
    )


# --- $add inside $sum accumulator ---


def test_add_inside_sum_accumulator(collection):
    """Test $add used inside $sum accumulator in $group."""
    collection.insert_many([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": None, "total": {"$sum": {"$add": ["$a", "$b"]}}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": None, "total": 10}], msg="Should sum computed $add values")


# --- $add result in $project followed by $match ---


def test_add_project_then_match(collection):
    """Test $add result in $project followed by $match filtering."""
    collection.insert_many([{"a": 3, "b": 4}, {"a": 1, "b": 2}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "sum": {"$add": ["$a", "$b"]}}},
                {"$match": {"sum": {"$gt": 5}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"sum": 7}], msg="Should filter on computed $add field")


# --- $add result in $addFields followed by $sort ---


def test_add_addfields_then_sort(collection):
    """Test $add result in $addFields followed by $sort."""
    collection.insert_many([{"a": 3, "b": 4}, {"a": 1, "b": 2}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"sum": {"$add": ["$a", "$b"]}}},
                {"$sort": {"sum": 1}},
                {"$project": {"_id": 0, "sum": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"sum": 3}, {"sum": 7}], msg="Should sort on computed $add field")
