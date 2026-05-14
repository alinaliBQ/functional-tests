"""Shared executor helpers for accumulator tests."""

from __future__ import annotations

from typing import Any

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.executor import execute_command


def execute_accumulator(
    collection,
    test_case: AccumulatorTestCase,
    stage: str,
    accumulator_name: str,
):
    """Insert docs and run the accumulator through the specified stage."""
    if test_case.docs:
        collection.insert_many(test_case.docs)

    pipeline: list[dict[str, Any]]
    if stage == "group":
        pipeline = [{"$group": {"_id": None, "result": {accumulator_name: test_case.accumulator}}}]
    elif stage == "bucket":
        pipeline = [
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {accumulator_name: test_case.accumulator}},
                }
            }
        ]
    else:
        pipeline = [
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {accumulator_name: test_case.accumulator}},
                }
            }
        ]

    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )


def execute_accumulator_with_type(
    collection,
    test_case: AccumulatorTestCase,
    stage: str,
    accumulator_name: str,
):
    """Insert docs and run the accumulator with a $type projection through the specified stage."""
    if test_case.docs:
        collection.insert_many(test_case.docs)

    pipeline: list[dict[str, Any]]
    if stage == "group":
        pipeline = [
            {"$group": {"_id": None, "result": {accumulator_name: test_case.accumulator}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ]
    elif stage == "bucket":
        pipeline = [
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {accumulator_name: test_case.accumulator}},
                }
            },
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ]
    else:
        pipeline = [
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {accumulator_name: test_case.accumulator}},
                }
            },
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ]

    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
