"""
Shared executor helpers for accumulator tests.

Provides helper functions for inserting documents and executing
accumulator pipelines.
"""

from __future__ import annotations

from typing import Any

from documentdb_tests.framework.executor import execute_command


def execute_accumulator(
    collection,
    docs: list[dict] | None,
    pipeline: list[dict[str, Any]] | None,
):
    """
    Insert docs and run an accumulator pipeline.

    Args:
        collection: MongoDB collection object
        docs: Documents to insert before running the pipeline.
            Pass None or an empty list to run against an empty collection.
        pipeline: The aggregation pipeline to execute

    Returns:
        Result from execute_command

    Example:
        >>> execute_accumulator(
        ...     collection,
        ...     [{"v": 1}, {"v": 2}],
        ...     [{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        ... )
        # Returns result with {"result": 3} in firstBatch
    """
    if docs:
        collection.insert_many(docs)

    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline or [], "cursor": {}},
    )
