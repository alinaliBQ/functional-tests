"""Shared utilities for setQuerySettings tests."""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection


def cleanup_query_settings(collection: Collection, queries: list[dict]) -> None:
    """Remove all query settings created during a test."""
    admin = collection.database.client.admin
    for q in queries:
        try:
            admin.command({"removeQuerySettings": q})
        except Exception:
            pass


def get_query_settings(collection: Collection) -> list[dict[str, Any]]:
    """Retrieve all current query settings via $querySettings stage."""
    admin = collection.database.client.admin
    result = admin.command({"aggregate": 1, "pipeline": [{"$querySettings": {}}], "cursor": {}})
    batch: list[dict[str, Any]] = result.get("cursor", {}).get("firstBatch", [])
    return batch
