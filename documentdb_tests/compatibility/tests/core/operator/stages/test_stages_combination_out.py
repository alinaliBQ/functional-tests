"""Tests for $out composing with other pipeline stages."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_OUT_TARGET = "__OUT_TARGET__"
_FOREIGN = "__FOREIGN__"

# Property [Match → Out]: $match narrows the document stream before $out
# writes the filtered results to the target collection.
MATCH_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_equality",
        docs=[
            {"_id": 1, "status": "active", "val": 10},
            {"_id": 2, "status": "inactive", "val": 20},
            {"_id": 3, "status": "active", "val": 30},
        ],
        pipeline=[
            {"$match": {"status": "active"}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 1, "status": "active", "val": 10},
            {"_id": 3, "status": "active", "val": 30},
        ],
        msg="$out should write only the documents that pass the $match filter",
    ),
    StageTestCase(
        "match_comparison",
        docs=[
            {"_id": 1, "val": 5},
            {"_id": 2, "val": 15},
            {"_id": 3, "val": 25},
        ],
        pipeline=[
            {"$match": {"val": {"$gte": 15}}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 2, "val": 15},
            {"_id": 3, "val": 25},
        ],
        msg="$out should write documents matching a comparison $match filter",
    ),
    StageTestCase(
        "match_no_results",
        docs=[
            {"_id": 1, "val": 10},
            {"_id": 2, "val": 20},
        ],
        pipeline=[
            {"$match": {"val": {"$gt": 100}}},
            {"$out": _OUT_TARGET},
        ],
        expected=[],
        msg="$out should create an empty collection when $match filters all documents",
    ),
]

# Property [Project → Out]: $project reshapes documents before $out writes
# the projected results to the target collection.
PROJECT_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "project_inclusion",
        docs=[
            {"_id": 1, "a": 1, "b": 2, "c": 3},
            {"_id": 2, "a": 4, "b": 5, "c": 6},
        ],
        pipeline=[
            {"$project": {"a": 1, "b": 1}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 4, "b": 5},
        ],
        msg="$out should write only the fields kept by an inclusion $project",
    ),
    StageTestCase(
        "project_computed",
        docs=[
            {"_id": 1, "x": 10},
            {"_id": 2, "x": 20},
        ],
        pipeline=[
            {"$project": {"doubled": {"$multiply": ["$x", 2]}}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 1, "doubled": 20},
            {"_id": 2, "doubled": 40},
        ],
        msg="$out should write computed fields from a $project stage",
    ),
]

# Property [Group → Out]: $group aggregates documents before $out writes
# the grouped results to the target collection.
GROUP_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "group_sum",
        docs=[
            {"_id": 1, "cat": "a", "val": 10},
            {"_id": 2, "cat": "a", "val": 20},
            {"_id": 3, "cat": "b", "val": 30},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "total": {"$sum": "$val"}}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": "a", "total": 30},
            {"_id": "b", "total": 30},
        ],
        msg="$out should write $group $sum results to the target collection",
    ),
    StageTestCase(
        "group_count",
        docs=[
            {"_id": 1, "cat": "x"},
            {"_id": 2, "cat": "x"},
            {"_id": 3, "cat": "y"},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "n": {"$sum": 1}}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": "x", "n": 2},
            {"_id": "y", "n": 1},
        ],
        msg="$out should write $group count results to the target collection",
    ),
]

# Property [Sort → Limit → Out]: $sort followed by $limit selects the
# top-N documents which $out writes to the target collection.
SORT_LIMIT_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sort_limit_top_n",
        docs=[
            {"_id": 1, "val": 50},
            {"_id": 2, "val": 10},
            {"_id": 3, "val": 40},
            {"_id": 4, "val": 30},
            {"_id": 5, "val": 20},
        ],
        pipeline=[
            {"$sort": {"val": -1}},
            {"$limit": 3},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 1, "val": 50},
            {"_id": 3, "val": 40},
            {"_id": 4, "val": 30},
        ],
        msg="$out should write the top-N sorted documents after $sort and $limit",
    ),
]

# Property [Skip → Limit → Out]: $skip and $limit paginate the document
# stream before $out writes the page to the target collection.
SKIP_LIMIT_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "skip_limit_page",
        docs=[
            {"_id": 1, "val": 10},
            {"_id": 2, "val": 20},
            {"_id": 3, "val": 30},
            {"_id": 4, "val": 40},
            {"_id": 5, "val": 50},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$skip": 1},
            {"$limit": 2},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 2, "val": 20},
            {"_id": 3, "val": 30},
        ],
        msg="$out should write the paginated window from $skip and $limit",
    ),
]

# Property [Unwind → Group → Out]: $unwind expands arrays, $group
# re-aggregates, and $out persists the result.
UNWIND_GROUP_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unwind_group_tag_count",
        docs=[
            {"_id": 1, "tags": ["a", "b"]},
            {"_id": 2, "tags": ["b", "c"]},
            {"_id": 3, "tags": ["a"]},
        ],
        pipeline=[
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": "a", "count": 2},
            {"_id": "b", "count": 2},
            {"_id": "c", "count": 1},
        ],
        msg="$out should write unwound-then-grouped tag counts to the target collection",
    ),
]

# Property [AddFields → Out]: $addFields enriches documents with computed
# fields before $out writes the enriched results.
ADDFIELDS_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "addfields_computed",
        docs=[
            {"_id": 1, "price": 100, "qty": 3},
            {"_id": 2, "price": 200, "qty": 1},
        ],
        pipeline=[
            {"$addFields": {"total": {"$multiply": ["$price", "$qty"]}}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 1, "price": 100, "qty": 3, "total": 300},
            {"_id": 2, "price": 200, "qty": 1, "total": 200},
        ],
        msg="$out should write documents enriched by $addFields to the target collection",
    ),
]

# Property [ReplaceRoot → Out]: $replaceRoot reshapes documents to a nested
# sub-document before $out writes the new root structure.
REPLACEROOT_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "replaceroot_nested",
        docs=[
            {"_id": 1, "inner": {"a": 10, "b": 20}},
            {"_id": 2, "inner": {"a": 30, "b": 40}},
        ],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$addFields": {"_id": "$a"}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 10, "a": 10, "b": 20},
            {"_id": 30, "a": 30, "b": 40},
        ],
        msg="$out should write the new root structure after $replaceRoot",
    ),
]

# Property [Redact → Out]: $redact controls document-level access before
# $out writes the redacted results.
REDACT_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "redact_keep_prune",
        docs=[
            {"_id": 1, "level": 1, "data": "public"},
            {"_id": 2, "level": 5, "data": "secret"},
            {"_id": 3, "level": 2, "data": "internal"},
        ],
        pipeline=[
            {
                "$redact": {
                    "$cond": {
                        "if": {"$lte": ["$level", 2]},
                        "then": "$$KEEP",
                        "else": "$$PRUNE",
                    }
                }
            },
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 1, "level": 1, "data": "public"},
            {"_id": 3, "level": 2, "data": "internal"},
        ],
        msg="$out should write only documents kept by $redact",
    ),
]

# Property [Lookup → Out]: $lookup joins documents from a foreign collection
# before $out writes the enriched results.
LOOKUP_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "lookup_equality",
        docs=[
            {"_id": 1, "ref": 1},
            {"_id": 2, "ref": 2},
        ],
        setup=lambda c: c.database[c.name + "_foreign"].insert_many(
            [
                {"_id": 1, "label": "first"},
                {"_id": 2, "label": "second"},
            ]
        ),
        pipeline=[
            {
                "$lookup": {
                    "from": _FOREIGN,
                    "localField": "ref",
                    "foreignField": "_id",
                    "as": "joined",
                }
            },
            {"$project": {"ref": 1, "label": {"$arrayElemAt": ["$joined.label", 0]}}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 1, "ref": 1, "label": "first"},
            {"_id": 2, "ref": 2, "label": "second"},
        ],
        msg="$out should write $lookup-joined documents to the target collection",
    ),
]

# Property [UnionWith → Out]: $unionWith combines documents from multiple
# collections before $out writes the merged results.
UNIONWITH_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unionwith_merge",
        docs=[
            {"_id": 1, "source": "main"},
            {"_id": 2, "source": "main"},
        ],
        setup=lambda c: c.database[c.name + "_foreign"].insert_many(
            [
                {"_id": 3, "source": "other"},
                {"_id": 4, "source": "other"},
            ]
        ),
        pipeline=[
            {"$unionWith": {"coll": _FOREIGN}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 1, "source": "main"},
            {"_id": 2, "source": "main"},
            {"_id": 3, "source": "other"},
            {"_id": 4, "source": "other"},
        ],
        msg="$out should write $unionWith-merged documents to the target collection",
    ),
]

# Property [Multi-Stage Pipeline → Out]: a complex pipeline combining
# multiple transformation stages feeds correct results into $out.
MULTI_STAGE_OUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_group_sort_out",
        docs=[
            {"_id": 1, "dept": "eng", "salary": 100},
            {"_id": 2, "dept": "eng", "salary": 150},
            {"_id": 3, "dept": "sales", "salary": 80},
            {"_id": 4, "dept": "sales", "salary": 120},
            {"_id": 5, "dept": "hr", "salary": 90},
        ],
        pipeline=[
            {"$match": {"salary": {"$gte": 90}}},
            {"$group": {"_id": "$dept", "avg_salary": {"$avg": "$salary"}}},
            {"$sort": {"avg_salary": -1}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": "eng", "avg_salary": 125.0},
            {"_id": "hr", "avg_salary": 90.0},
            {"_id": "sales", "avg_salary": 120.0},
        ],
        msg="$out should write correctly after $match, $group, and $sort combined",
    ),
    StageTestCase(
        "project_addfields_match_out",
        docs=[
            {"_id": 1, "price": 50, "qty": 4},
            {"_id": 2, "price": 30, "qty": 10},
            {"_id": 3, "price": 20, "qty": 2},
        ],
        pipeline=[
            {"$project": {"price": 1, "qty": 1}},
            {"$addFields": {"revenue": {"$multiply": ["$price", "$qty"]}}},
            {"$match": {"revenue": {"$gte": 200}}},
            {"$out": _OUT_TARGET},
        ],
        expected=[
            {"_id": 1, "price": 50, "qty": 4, "revenue": 200},
            {"_id": 2, "price": 30, "qty": 10, "revenue": 300},
        ],
        msg="$out should write correctly after $project, $addFields, and $match combined",
    ),
]

STAGE_COMBINATIONS_OUT_TESTS = (
    MATCH_OUT_TESTS
    + PROJECT_OUT_TESTS
    + GROUP_OUT_TESTS
    + SORT_LIMIT_OUT_TESTS
    + SKIP_LIMIT_OUT_TESTS
    + UNWIND_GROUP_OUT_TESTS
    + ADDFIELDS_OUT_TESTS
    + REPLACEROOT_OUT_TESTS
    + REDACT_OUT_TESTS
    + LOOKUP_OUT_TESTS
    + UNIONWITH_OUT_TESTS
    + MULTI_STAGE_OUT_TESTS
)


def _resolve_placeholders(pipeline: list[dict], out_name: str, foreign_name: str) -> list[dict]:
    """Replace placeholder strings in a pipeline with runtime collection names."""
    import json

    raw = json.dumps(pipeline)
    raw = raw.replace(f'"{_OUT_TARGET}"', f'"{out_name}"')
    raw = raw.replace(f'"{_FOREIGN}"', f'"{foreign_name}"')
    result: list[dict] = json.loads(raw)
    return result


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(STAGE_COMBINATIONS_OUT_TESTS))
def test_stage_combinations_out(collection, test_case: StageTestCase):
    """Test pipeline stages composing with $out."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    db = collection.database
    out_name = collection.name + "_out"
    foreign_name = collection.name + "_foreign"
    pipeline = _resolve_placeholders(test_case.pipeline, out_name, foreign_name)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"find": out_name, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
    db.drop_collection(out_name)
    db.drop_collection(foreign_name)
