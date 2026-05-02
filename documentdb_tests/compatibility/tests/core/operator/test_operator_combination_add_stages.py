"""Tests for $add in pipeline contexts — $project, $addFields, $match+$expr, $group."""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

SETUP_DOCS = [{"a": 3, "b": 4}, {"a": 7, "b": 8}]


def test_add_in_project(collection):
    """Test $add in $project stage."""
    collection.insert_many(SETUP_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": {"$add": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"result": 7}, {"result": 15}], msg="Should compute $add in $project")


def test_add_in_addfields(collection):
    """Test $add in $addFields stage."""
    collection.insert_many(SETUP_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"result": {"$add": ["$a", "$b"]}}},
                {"$project": {"_id": 0, "result": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"result": 7}, {"result": 15}], msg="Should compute $add in $addFields")


def test_add_in_match_expr(collection):
    """Test $add in $match with $expr."""
    collection.insert_many(SETUP_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$expr": {"$gt": [{"$add": ["$a", "$b"]}, 10]}}},
                {"$project": {"_id": 0, "a": 1, "b": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"a": 7, "b": 8}], msg="Should filter using $add in $match $expr")


def test_add_in_group_expression(collection):
    """Test $add in $group accumulator expression."""
    collection.insert_many(SETUP_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": None, "result": {"$max": {"$add": ["$a", "$b"]}}}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result, [{"_id": None, "result": 15}], msg="Should compute $add in $group accumulator"
    )


def test_add_in_group_id(collection):
    """Test $add as $group _id expression."""
    collection.insert_many(SETUP_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": {"$add": ["$a", "$b"]}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 7}, {"_id": 15}], msg="Should group by computed $add value")
