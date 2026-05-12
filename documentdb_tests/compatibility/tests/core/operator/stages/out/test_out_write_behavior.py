"""Tests for $out stage - write behavior."""

from __future__ import annotations

import threading
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

# Property [Database Name Acceptance]: any non-empty string of non-null
# bytes that does not contain a slash, backslash, dot, ASCII space, or dollar
# prefix is accepted as a database name.
OUT_DATABASE_NAME_ACCEPTANCE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "db_control_character",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="\x01",
        msg="$out should accept a control character as a database name",
    ),
    OutTestCase(
        "db_unicode_no_break_space",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="\u00a0",
        msg="$out should accept Unicode no-break space as a database name",
    ),
    OutTestCase(
        "db_zero_width_space",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="\u200b",
        msg="$out should accept zero-width space as a database name",
    ),
    OutTestCase(
        "db_emoji",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="\U0001f389",
        msg="$out should accept emoji as a database name",
    ),
    OutTestCase(
        "db_cjk_characters",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="\u4e2d\u6587",
        msg="$out should accept CJK characters as a database name",
    ),
    OutTestCase(
        "db_punctuation",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="a!@#b",
        msg="$out should accept punctuation in a database name",
    ),
    OutTestCase(
        "db_single_character",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="a",
        msg="$out should accept a single-character database name",
    ),
    OutTestCase(
        "db_digits_only",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="123",
        msg="$out should accept a digits-only database name",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_DATABASE_NAME_ACCEPTANCE_TESTS))
def test_out_database_name_acceptance(collection, test_case: OutTestCase):
    """Test $out accepts various character classes as database names."""
    populate_collection(collection, test_case)
    db_name = test_case.target_db  # type: ignore[arg-type]
    client = collection.database.client
    client.drop_database(db_name)
    try:
        out_stage = {"$out": {"db": db_name, "coll": test_case.target_coll}}
        execute_command(
            collection,
            {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
        )
        target_db = client[db_name]
        result = execute_command(
            target_db[test_case.target_coll],
            {"listCollections": 1, "filter": {"name": test_case.target_coll}},
        )
        assertSuccess(
            result,
            [{"name": test_case.target_coll, "type": "collection", "options": {}}],
            msg=test_case.msg,
            transform=lambda docs: [
                {"name": d["name"], "type": d["type"], "options": d.get("options", {})}
                for d in docs
            ],
        )
    finally:
        client.drop_database(db_name)


# Property [Collection Creation]: $out creates a new collection (and database
# if needed) when the target does not exist, and an empty pipeline result
# creates an empty collection or empties an existing one.
OUT_COLLECTION_CREATION_TESTS: list[OutTestCase] = [
    OutTestCase(
        "new_collection_created",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        target_coll="creation_new_target",
        out_spec=None,
        expected=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        msg="$out should create a new collection when the target does not exist",
    ),
    OutTestCase(
        "new_database_created",
        docs=[{"_id": 1, "value": 10}],
        target_coll="creation_cross_db_target",
        target_db="__CROSS_DB__",
        expected=[{"_id": 1, "value": 10}],
        msg="$out should create a new database when the output database does not exist",
    ),
    OutTestCase(
        "empty_pipeline_creates_empty_collection",
        docs=[],
        target_coll="creation_empty_target",
        out_spec=None,
        expected=[],
        msg="$out with no documents should create an empty collection",
    ),
    OutTestCase(
        "empty_pipeline_empties_existing_collection",
        docs=[],
        target_coll="creation_emptied_target",
        out_spec=None,
        expected=[],
        msg="$out with no documents should empty an existing collection",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_COLLECTION_CREATION_TESTS))
def test_out_collection_creation(collection, test_case: OutTestCase):
    """Test $out creates collections and databases as needed."""
    populate_collection(collection, test_case)
    db = collection.database
    client = db.client
    cross_db_name = db.name + "_cross"
    if test_case.id == "empty_pipeline_empties_existing_collection":
        db[test_case.target_coll].insert_one({"_id": 99, "old": True})
    # Replace placeholder with a unique cross-database name.
    if test_case.target_db == "__CROSS_DB__":
        client.drop_database(cross_db_name)
        effective_case = OutTestCase(
            id=test_case.id,
            docs=test_case.docs,
            target_coll=test_case.target_coll,
            target_db=cross_db_name,
            expected=test_case.expected,
            msg=test_case.msg,
        )
    else:
        effective_case = test_case
    try:
        out_stage = effective_case.build_out_stage(collection)
        execute_command(
            collection,
            {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
        )
        target_db = client[effective_case.target_db] if effective_case.target_db else db
        target_coll = target_db[effective_case.target_coll]
        # Use listCollections to verify the collection exists. This is
        # necessary because find on a non-existent collection also returns
        # an empty firstBatch, which would make empty-result cases pass
        # even if $out never created the target.
        result = execute_command(
            target_coll,
            {"listCollections": 1, "filter": {"name": effective_case.target_coll}},
        )
        expected_docs = effective_case.expected
        assertSuccess(
            result,
            {"exists": True, "docs": expected_docs},
            msg=effective_case.msg,
            transform=lambda r: {
                "exists": len(r) == 1,
                "docs": sorted(
                    target_coll.find(
                        {},
                        {k: 1 for d in (expected_docs or [{}]) for k in d},
                    ),
                    key=lambda d: d.get("_id", 0),
                ),
            },
        )
    finally:
        if effective_case.target_db and effective_case.target_db != db.name:
            client.drop_database(effective_case.target_db)


# Property [Collection Replacement - Atomic Replace]: an existing collection
# is atomically replaced with the new pipeline results upon $out completion.
OUT_REPLACEMENT_ATOMIC_TESTS: list[OutTestCase] = [
    OutTestCase(
        "replacement_atomic",
        docs=[{"_id": 10, "new": True}, {"_id": 20, "new": True}],
        target_coll="replacement_atomic_target",
        setup=lambda c: c.database["replacement_atomic_target"].insert_many(
            [{"_id": 1, "old": True}, {"_id": 2, "old": True}]
        ),
        expected=[{"_id": 10, "new": True}, {"_id": 20, "new": True}],
        msg="$out should replace existing documents with new pipeline results",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_REPLACEMENT_ATOMIC_TESTS))
def test_out_replacement_atomic(collection, test_case: OutTestCase):
    """Test $out atomically replaces an existing collection with new results."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    pipeline = [{"$out": test_case.target_coll}]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Collection Replacement - Index Preservation]: indexes from the
# previous collection are preserved after $out replaces its contents.
OUT_REPLACEMENT_INDEX_TESTS: list[OutTestCase] = [
    OutTestCase(
        "replacement_preserves_indexes",
        docs=[{"_id": 10, "x": 100}, {"_id": 20, "x": 200}],
        target_coll="replacement_idx_target",
        setup=lambda c: (
            c.database["replacement_idx_target"].insert_one({"_id": 1, "x": 1}),
            c.database["replacement_idx_target"].create_index("x", name="x_idx", unique=True),
        ),
        expected=[{"name": "_id_"}, {"name": "x_idx", "unique": True}],
        msg="$out should preserve indexes from the previous collection",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_REPLACEMENT_INDEX_TESTS))
def test_out_replacement_preserves_indexes(collection, test_case: OutTestCase):
    """Test $out preserves indexes from the previous collection after replacement."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    pipeline = [{"$out": test_case.target_coll}]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"listIndexes": test_case.target_coll},
    )
    assertSuccess(
        result,
        test_case.expected,
        msg=test_case.msg,
        transform=lambda docs: [
            {"name": d["name"], **({"unique": d["unique"]} if d.get("unique") else {})}
            for d in sorted(docs, key=lambda d: d["name"])
        ],
    )


# Property [Collection Replacement - Self-Replacement]: writing to the same
# collection as the input succeeds and the collection contains the transformed
# results.
OUT_REPLACEMENT_SELF_TESTS: list[OutTestCase] = [
    OutTestCase(
        "replacement_self",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        expected=[{"_id": 1, "value": 10, "doubled": 20}, {"_id": 2, "value": 20, "doubled": 40}],
        msg="$out self-replacement should contain transformed results",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_REPLACEMENT_SELF_TESTS))
def test_out_replacement_self(collection, test_case: OutTestCase):
    """Test $out self-replacement writes transformed results back to the source."""
    populate_collection(collection, test_case)
    pipeline = [
        {"$addFields": {"doubled": {"$multiply": ["$value", 2]}}},
        {"$out": collection.name},
    ]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Collection Replacement - Failure Rollback]: if the aggregation
# fails during $out, the pre-existing collection and its indexes are unchanged.
OUT_REPLACEMENT_FAILURE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "replacement_failure_unchanged",
        docs=[{"_id": 10, "x": 1}, {"_id": 20, "x": 1}],
        target_coll="replacement_fail_target",
        setup=lambda c: (
            c.database["replacement_fail_target"].insert_many(
                [{"_id": 1, "x": 1}, {"_id": 2, "x": 2}]
            ),
            c.database["replacement_fail_target"].create_index("x", unique=True),
        ),
        expected={
            "docs": [{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
            "indexes": [{"name": "_id_"}, {"name": "x_1", "unique": True}],
        },
        msg="$out failure should leave pre-existing collection and indexes unchanged",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_REPLACEMENT_FAILURE_TESTS))
def test_out_replacement_failure_unchanged(collection, test_case: OutTestCase):
    """Test $out leaves the pre-existing collection unchanged on failure."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    pipeline = [{"$out": test_case.target_coll}]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    # The aggregation fails due to unique index violation; verify the
    # pre-existing collection and its indexes are unchanged.
    idx_result = execute_command(
        collection,
        {"listIndexes": test_case.target_coll},
    )
    target = collection.database[test_case.target_coll]
    assertSuccess(
        idx_result,
        test_case.expected,
        msg=test_case.msg,
        transform=lambda idx_docs: {
            "docs": sorted(target.find({}, {"_id": 1, "x": 1}), key=lambda d: d["_id"]),
            "indexes": [
                {
                    "name": d["name"],
                    **({"unique": d["unique"]} if d.get("unique") else {}),
                }
                for d in sorted(idx_docs, key=lambda d: d["name"])
            ],
        },
    )


OUT_TEMP_COLLECTION_TESTS: list[OutTestCase] = [
    OutTestCase(
        "temp_coll",
        docs=[{"_id": i, "value": i} for i in range(10_000)],
        target_coll="creation_temp_target",
        expected={"observed": True, "remaining": []},
        msg="$out should use a temp collection during execution and clean it up after",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TEMP_COLLECTION_TESTS))
def test_out_temp_collection_during_execution(collection, test_case: OutTestCase):
    """Test $out uses a temporary collection that is cleaned up after completion."""
    populate_collection(collection, test_case)
    db = collection.database

    found_tmp: list[str] = []
    stop = threading.Event()

    def poll_collections() -> None:
        while not stop.is_set():
            try:
                names = db.list_collection_names()
                for name in names:
                    if name.startswith("tmp.agg_out."):
                        found_tmp.append(name)
                        return
            except Exception:
                pass

    t = threading.Thread(target=poll_collections, daemon=True)
    t.start()

    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": test_case.target_coll}], "cursor": {}},
    )

    stop.set()
    t.join(timeout=5)

    # Verify temp collection was observed during execution and cleaned up after.
    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": {"$regex": "^tmp\\.agg_out\\."}}},
    )
    assertSuccess(
        result,
        test_case.expected,
        raw_res=True,
        msg=test_case.msg,
        transform=lambda r: {
            "observed": len(found_tmp) > 0,
            "remaining": [d["name"] for d in r["cursor"]["firstBatch"]],
        },
    )


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
