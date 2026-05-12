"""Tests for $out stage - individual write properties."""

from __future__ import annotations

from datetime import datetime
from typing import cast

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertSuccess,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Write Behavior - Auto-Generated _id]: documents with _id removed
# via a pipeline stage receive auto-generated ObjectId _id values in the
# output collection.
OUT_AUTO_GENERATED_ID_TESTS: list[OutTestCase] = [
    OutTestCase(
        "auto_id",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        target_coll="write_auto_id_target",
        expected=[{"value": 10, "is_objectid": True}, {"value": 20, "is_objectid": True}],
        msg="$out should auto-generate ObjectId _id when _id is removed",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_AUTO_GENERATED_ID_TESTS))
def test_out_auto_generated_id(collection, test_case: OutTestCase):
    """Test $out auto-generates ObjectId _id when _id is removed."""
    populate_collection(collection, test_case)
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unset": "_id"}, {"$out": test_case.target_coll}],
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}, "sort": {"value": 1}},
    )
    assertSuccess(
        result,
        test_case.expected,
        msg=test_case.msg,
        transform=lambda docs: [
            {"value": d["value"], "is_objectid": isinstance(d["_id"], ObjectId)} for d in docs
        ],
    )


# Property [Write Behavior - Empty Cursor]: the aggregation cursor returned
# by a pipeline ending with $out contains an empty result list.
OUT_EMPTY_CURSOR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "empty_cursor",
        docs=[{"_id": 1, "value": 10}],
        target_coll="write_cursor_target",
        expected=[],
        msg="$out aggregation cursor should return an empty result list",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_EMPTY_CURSOR_TESTS))
def test_out_empty_cursor(collection, test_case: OutTestCase):
    """Test $out returns an empty cursor result."""
    populate_collection(collection, test_case)
    pipeline = [{"$out": test_case.target_coll}]
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Write Behavior - Explain No Write]: explain does not perform the
# write - the target collection is not created or modified.
OUT_EXPLAIN_NO_WRITE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "explain_no_write",
        docs=[{"_id": 1, "value": 10}],
        target_coll="write_explain_target",
        expected=[],
        msg="explain with $out should not create the target collection",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_EXPLAIN_NO_WRITE_TESTS))
def test_out_explain_no_write(collection, test_case: OutTestCase):
    """Test explain with $out does not create or modify the target collection."""
    populate_collection(collection, test_case)
    pipeline = [{"$out": test_case.target_coll}]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}, "explain": True},
    )
    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": test_case.target_coll}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


OUT_EXPLAIN_NO_MODIFY_TESTS: list[OutTestCase] = [
    OutTestCase(
        "explain_no_modify",
        docs=[{"_id": 10, "new": True}],
        target_coll="write_explain_existing_target",
        setup=lambda c: c.database["write_explain_existing_target"].insert_many(
            [{"_id": 1, "old": True}, {"_id": 2, "old": True}]
        ),
        expected=[{"_id": 1, "old": True}, {"_id": 2, "old": True}],
        msg="explain with $out should not modify existing target collection",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_EXPLAIN_NO_MODIFY_TESTS))
def test_out_explain_no_modify(collection, test_case: OutTestCase):
    """Test explain with $out does not modify an existing target collection."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    pipeline = [{"$out": test_case.target_coll}]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}, "explain": True},
    )
    result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Write Behavior - Idempotent]: running the same $out pipeline to
# the same target twice produces the same result in the target collection.
OUT_IDEMPOTENT_TESTS: list[OutTestCase] = [
    OutTestCase(
        "idempotent",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        target_coll="write_idempotent_target",
        expected=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        msg="$out should produce the same result when run twice to the same target",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_IDEMPOTENT_TESTS))
def test_out_idempotent(collection, test_case: OutTestCase):
    """Test $out is idempotent when run twice to the same target."""
    populate_collection(collection, test_case)
    pipeline = [{"$out": test_case.target_coll}]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Write Behavior - BSON Round-Trip]: all BSON types representable
# by pymongo round-trip through $out without modification.
OUT_BSON_ROUND_TRIP_TESTS: list[OutTestCase] = [
    OutTestCase(
        "bson_round_trip",
        docs=[
            {
                "_id": 1,
                "double_val": 3.14,
                "string_val": "hello",
                "object_val": {"nested": True},
                "array_val": [1, 2, 3],
                "binary_val": Binary(b"\x01\x02\x03"),
                "objectid_val": ObjectId("507f1f77bcf86cd799439011"),
                "bool_val": True,
                "date_val": datetime(2024, 1, 1),
                "null_val": None,
                "regex_val": Regex("abc", "i"),
                "int32_val": 42,
                "timestamp_val": Timestamp(1_234_567_890, 1),
                "int64_val": Int64(9_876_543_210),
                "decimal128_val": Decimal128("123.456"),
                "minkey_val": MinKey(),
                "maxkey_val": MaxKey(),
                "code_val": Code("function() {}"),
            }
        ],
        target_coll="write_bson_target",
        msg="all BSON types should round-trip through $out without modification",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_BSON_ROUND_TRIP_TESTS))
def test_out_bson_round_trip(collection, test_case: OutTestCase):
    """Test all BSON types round-trip through $out without modification."""
    populate_collection(collection, test_case)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": test_case.target_coll}], "cursor": {}},
    )
    source_result = execute_command(
        collection,
        {"find": collection.name, "filter": {}},
    )
    target_result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}},
    )
    assertSuccess(
        target_result,
        cast(dict, source_result)["cursor"]["firstBatch"],
        msg=test_case.msg,
    )


# Property [Write Behavior - Large Documents]: documents up to 15 MB are
# written successfully through $out.
OUT_LARGE_DOCUMENT_TESTS: list[OutTestCase] = [
    OutTestCase(
        "large_doc",
        docs=[{"_id": 1, "data": "x" * (15 * 1_024 * 1_024)}],
        target_coll="write_large_target",
        expected=[{"_id": 1}],
        msg="$out should successfully write a 15 MB document",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_LARGE_DOCUMENT_TESTS))
def test_out_large_document(collection, test_case: OutTestCase):
    """Test $out writes documents up to 15 MB successfully."""
    populate_collection(collection, test_case)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": test_case.target_coll}], "cursor": {}},
    )
    result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}, "projection": {"_id": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [No Unicode Normalization - Collections]: precomposed and combining
# forms of the same character create separate, distinct collections - no
# Unicode normalization is applied to collection names.

# U+00E9 (precomposed e-acute, 2 UTF-8 bytes)
_PRECOMPOSED_COLL = "\u00e9"
# U+0065 U+0301 (e + combining acute, 3 UTF-8 bytes)
_COMBINING_COLL = "\u0065\u0301"

OUT_NO_UNICODE_NORMALIZATION_TESTS: list[OutTestCase] = [
    OutTestCase(
        "no_normalization",
        docs=[{"_id": 1, "form": "precomposed"}, {"_id": 2, "form": "combining"}],
        expected={
            "precomposed_docs": [{"_id": 1, "form": "precomposed"}],
            "combining_docs": [{"_id": 2, "form": "combining"}],
            "collection_count": 2,
        },
        msg="$out should create separate collections for precomposed and combining forms",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_NO_UNICODE_NORMALIZATION_TESTS))
def test_out_no_unicode_normalization(collection, test_case: OutTestCase):
    """Test $out treats precomposed and combining Unicode forms as distinct collection names."""
    populate_collection(collection, test_case)
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"_id": 1}}, {"$out": _PRECOMPOSED_COLL}],
            "cursor": {},
        },
    )
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"_id": 2}}, {"$out": _COMBINING_COLL}],
            "cursor": {},
        },
    )
    db = collection.database
    precomposed_docs = list(db[_PRECOMPOSED_COLL].find({}, {"_id": 1, "form": 1}))
    combining_docs = list(db[_COMBINING_COLL].find({}, {"_id": 1, "form": 1}))
    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": {"$in": [_PRECOMPOSED_COLL, _COMBINING_COLL]}}},
    )
    assertSuccess(
        result,
        test_case.expected,
        msg=test_case.msg,
        transform=lambda docs: {
            "precomposed_docs": precomposed_docs,
            "combining_docs": combining_docs,
            "collection_count": len(docs),
        },
    )


# Property [No Unicode Normalization - Databases]: precomposed and combining
# forms of the same character create separate, distinct databases - no Unicode
# normalization is applied to database names.

# U+00E9 (precomposed e-acute, 2 UTF-8 bytes)
_PRECOMPOSED_DB = "\u00e9"
# U+0065 U+0301 (e + combining acute, 3 UTF-8 bytes)
_COMBINING_DB = "\u0065\u0301"

OUT_NO_UNICODE_NORMALIZATION_DB_TESTS: list[OutTestCase] = [
    OutTestCase(
        "no_normalization_db",
        docs=[{"_id": 1, "form": "precomposed"}, {"_id": 2, "form": "combining"}],
        target_coll="target",
        expected={
            "precomposed_docs": [{"_id": 1, "form": "precomposed"}],
            "combining_docs": [{"_id": 2, "form": "combining"}],
            "both_exist": True,
        },
        msg="$out should create separate databases for precomposed and combining forms",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_NO_UNICODE_NORMALIZATION_DB_TESTS))
def test_out_no_unicode_normalization_database(collection, test_case: OutTestCase):
    """Test $out treats precomposed and combining Unicode forms as distinct database names."""
    populate_collection(collection, test_case)
    client = collection.database.client
    client.drop_database(_PRECOMPOSED_DB)
    client.drop_database(_COMBINING_DB)
    try:
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {"$match": {"_id": 1}},
                    {"$out": {"db": _PRECOMPOSED_DB, "coll": test_case.target_coll}},
                ],
                "cursor": {},
            },
        )
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {"$match": {"_id": 2}},
                    {"$out": {"db": _COMBINING_DB, "coll": test_case.target_coll}},
                ],
                "cursor": {},
            },
        )
        precomposed_docs = list(
            client[_PRECOMPOSED_DB][test_case.target_coll].find({}, {"_id": 1, "form": 1})
        )
        combining_docs = list(
            client[_COMBINING_DB][test_case.target_coll].find({}, {"_id": 1, "form": 1})
        )
        db_names = client.list_database_names()
        assertSuccess(
            {"cursor": {"firstBatch": [{"result": True}]}},
            test_case.expected,
            msg=test_case.msg,
            transform=lambda _: {
                "precomposed_docs": precomposed_docs,
                "combining_docs": combining_docs,
                "both_exist": _PRECOMPOSED_DB in db_names and _COMBINING_DB in db_names,
            },
        )
    finally:
        client.drop_database(_PRECOMPOSED_DB)
        client.drop_database(_COMBINING_DB)
