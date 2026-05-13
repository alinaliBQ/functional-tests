"""Tests for $out stage - write behavior."""

from __future__ import annotations

import threading

import pytest

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


# Property [Collection Creation]: $out creates a new collection when the
# target does not exist, and an empty pipeline result creates an empty
# collection or empties an existing one.
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
        setup=lambda c: c.database["creation_emptied_target"].insert_one({"_id": 99, "old": True}),
        expected=[],
        msg="$out with no documents should empty an existing collection",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_COLLECTION_CREATION_TESTS))
def test_out_collection_creation(collection, test_case: OutTestCase):
    """Test $out creates collections as needed."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    out_stage = test_case.build_out_stage(collection)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
    )
    # Use listCollections to verify the collection exists. find on a
    # non-existent collection also returns empty, which would make
    # empty-result cases pass even if $out never created the target.
    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": test_case.target_coll}},
    )
    db = collection.database
    assertSuccess(
        result,
        {"exists": True, "docs": test_case.expected},
        msg=test_case.msg,
        transform=lambda r: {
            "exists": len(r) == 1,
            "docs": list(db[test_case.target_coll].find({}, sort=[("_id", 1)])),
        },
    )


# Property [Database Creation]: $out creates a new database when the output
# database does not exist.


@pytest.mark.aggregate
def test_out_database_creation(collection):
    """Test $out creates a new database when the output database does not exist."""
    collection.insert_many([{"_id": 1, "value": 10}])
    db = collection.database
    client = db.client
    cross_db_name = db.name + "_cross"
    target_coll_name = "creation_cross_db_target"
    client.drop_database(cross_db_name)
    try:
        out_stage = {"$out": {"db": cross_db_name, "coll": target_coll_name}}
        execute_command(
            collection,
            {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
        )
        target_coll = client[cross_db_name][target_coll_name]
        result = execute_command(
            target_coll,
            {"find": target_coll_name, "filter": {}},
        )
        assertSuccess(
            result,
            [{"_id": 1, "value": 10}],
            msg="$out should create a new database when the output database does not exist",
        )
    finally:
        client.drop_database(cross_db_name)


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
OUT_REPLACEMENT_FAILURE_UNCHANGED_TESTS: list[OutTestCase] = [
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
@pytest.mark.parametrize("test_case", pytest_params(OUT_REPLACEMENT_FAILURE_UNCHANGED_TESTS))
def test_out_replacement_failure_unchanged(collection, test_case: OutTestCase):
    """Test $out leaves the pre-existing collection unchanged on failure."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": test_case.target_coll}], "cursor": {}},
    )
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
