"""Tests for $out stage - target collection restrictions, options, and special cases."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertFailure,
    assertFailureCode,
    assertSuccess,
)
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    DOCUMENT_VALIDATION_FAILURE_ERROR,
    DUPLICATE_KEY_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    INVALID_VIEW_PIPELINE_ERROR,
    OUT_CAPPED_COLLECTION_ERROR,
    OUT_TIMESERIES_COLLECTION_TYPE_ERROR,
    OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command


# Property [Target Collection Restriction Errors]: $out rejects writing to
# capped collections and views, and writing to a view with timeseries options
# produces a timeseries collection type error instead of the view-specific
# error.
@pytest.mark.aggregate
def test_out_capped_collection_error(collection):
    """Test $out rejects writing to a capped collection."""
    populate_collection(
        collection,
        StageTestCase(
            id="capped_target",
            docs=[{"_id": 1, "value": 10}],
            msg="$out should reject writing to a capped collection",
        ),
    )
    db = collection.database
    target_name = "capped_out_target"
    db.drop_collection(target_name)
    db.create_collection(target_name, capped=True, size=1_048_576)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": target_name}], "cursor": {}},
    )
    assertFailureCode(
        result,
        OUT_CAPPED_COLLECTION_ERROR,
        msg="$out should reject writing to a capped collection",
    )


@pytest.mark.aggregate
def test_out_view_error(collection):
    """Test $out rejects writing to a view."""
    populate_collection(
        collection,
        StageTestCase(
            id="view_target",
            docs=[{"_id": 1, "value": 10}],
            msg="$out should reject writing to a view",
        ),
    )
    db = collection.database
    target_name = "view_out_target"
    db.drop_collection(target_name)
    db.command({"create": target_name, "viewOn": collection.name, "pipeline": []})
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": target_name}], "cursor": {}},
    )
    assertFailureCode(
        result,
        COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$out should reject writing to a view",
    )


@pytest.mark.aggregate
def test_out_view_with_timeseries_error(collection):
    """Test $out to a view with timeseries options produces a timeseries error."""
    populate_collection(
        collection,
        StageTestCase(
            id="view_ts_target",
            docs=[{"_id": 1, "value": 10}],
            msg="$out to a view with timeseries should produce a timeseries error",
        ),
    )
    db = collection.database
    target_name = "view_ts_out_target"
    db.drop_collection(target_name)
    db.command({"create": target_name, "viewOn": collection.name, "pipeline": []})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$out": {
                        "db": db.name,
                        "coll": target_name,
                        "timeseries": {"timeField": "ts"},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        OUT_TIMESERIES_COLLECTION_TYPE_ERROR,
        msg=(
            "$out to a view with timeseries options should produce a timeseries"
            " collection type error, not the view-specific error"
        ),
    )


# Property [Timeseries Existing Collection Errors]: writing with timeseries
# options to an existing regular collection produces a timeseries collection
# type error, and writing with mismatched timeseries options to an existing
# time series collection produces a timeseries options mismatch error
# regardless of which option differs.
@pytest.mark.aggregate
def test_out_timeseries_to_regular_collection_error(collection):
    """Test $out with timeseries options to an existing regular collection fails."""
    db = collection.database
    target_name = "ts_to_regular_target"
    db.drop_collection(target_name)
    db.create_collection(target_name)
    populate_collection(
        collection,
        StageTestCase(
            id="ts_to_regular",
            docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
            msg="$out with timeseries to a regular collection should fail",
        ),
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$out": {
                        "db": db.name,
                        "coll": target_name,
                        "timeseries": {"timeField": "ts"},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        OUT_TIMESERIES_COLLECTION_TYPE_ERROR,
        msg=(
            "$out with timeseries options to an existing regular collection"
            " should produce a timeseries collection type error"
        ),
    )


@pytest.mark.aggregate
@pytest.mark.parametrize(
    "existing_opts,mismatched_opts",
    [
        pytest.param(
            {"timeField": "ts"},
            {"timeField": "other"},
            id="different_time_field",
        ),
        pytest.param(
            {"timeField": "ts"},
            {"timeField": "ts", "metaField": "m"},
            id="meta_field_present_vs_absent",
        ),
        pytest.param(
            {"timeField": "ts", "metaField": "m"},
            {"timeField": "ts", "metaField": "other"},
            id="different_meta_field",
        ),
        pytest.param(
            {"timeField": "ts", "granularity": "seconds"},
            {"timeField": "ts", "granularity": "hours"},
            id="different_granularity",
        ),
        pytest.param(
            {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 100,
                "bucketRoundingSeconds": 100,
            },
            {"timeField": "ts", "granularity": "hours"},
            id="granularity_vs_bucket_options",
        ),
        pytest.param(
            {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 100,
                "bucketRoundingSeconds": 100,
            },
            {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 200,
                "bucketRoundingSeconds": 200,
            },
            id="different_bucket_values",
        ),
    ],
)
def test_out_timeseries_mismatch_error(collection, existing_opts, mismatched_opts):
    """Test $out with mismatched timeseries options to an existing time series collection fails."""
    db = collection.database
    target_name = "ts_mismatch_target"
    db.drop_collection(target_name)
    db.command({"create": target_name, "timeseries": existing_opts})
    populate_collection(
        collection,
        StageTestCase(
            id="ts_mismatch",
            docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
            msg="$out with mismatched timeseries options should fail",
        ),
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$out": {
                        "db": db.name,
                        "coll": target_name,
                        "timeseries": mismatched_opts,
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
    )


# Property [Index Constraint Errors]: unique index violations (including
# compound unique indexes) and duplicate _id values in the output produce a
# duplicate key error, and when a unique index violation occurs writing to a
# nonexistent target, the target collection is not created.
@pytest.mark.aggregate
def test_out_unique_index_violation(collection):
    """Test $out produces a duplicate key error on unique index violation."""
    db = collection.database
    target_name = "idx_unique_target"
    populate_collection(
        collection,
        StageTestCase(
            id="idx_unique",
            docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 1}],
            msg="$out should produce a duplicate key error on unique index violation",
        ),
    )
    db[target_name].insert_many([{"_id": 90, "x": 90}, {"_id": 91, "x": 91}])
    db[target_name].create_index("x", unique=True)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": target_name}], "cursor": {}},
    )
    assertFailureCode(
        result,
        DUPLICATE_KEY_ERROR,
        msg="$out should produce a duplicate key error on unique index violation",
    )


@pytest.mark.aggregate
def test_out_compound_unique_index_violation(collection):
    """Test $out produces a duplicate key error on compound unique index violation."""
    db = collection.database
    target_name = "idx_compound_target"
    populate_collection(
        collection,
        StageTestCase(
            id="idx_compound",
            docs=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1, "b": 2}],
            msg="$out should produce a duplicate key error on compound unique index violation",
        ),
    )
    db[target_name].insert_one({"_id": 99, "a": 99, "b": 99})
    db[target_name].create_index([("a", 1), ("b", 1)], unique=True)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": target_name}], "cursor": {}},
    )
    assertFailureCode(
        result,
        DUPLICATE_KEY_ERROR,
        msg="$out should produce a duplicate key error on compound unique index violation",
    )


@pytest.mark.aggregate
def test_out_duplicate_id_error(collection):
    """Test $out produces a duplicate key error when output contains duplicate _id values."""
    populate_collection(
        collection,
        StageTestCase(
            id="idx_dup_id",
            docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
            msg="$out should produce a duplicate key error on duplicate _id in output",
        ),
    )
    target_name = "idx_dup_id_target"
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$unset": "_id"},
                {"$addFields": {"_id": "same"}},
                {"$out": target_name},
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        DUPLICATE_KEY_ERROR,
        msg="$out should produce a duplicate key error when output contains duplicate _id values",
    )


@pytest.mark.aggregate
def test_out_unique_violation_nonexistent_target_not_created(collection):
    """Test $out does not create the target when a unique index violation occurs."""
    db = collection.database
    target_name = "idx_nonexist_target"
    db.drop_collection(target_name)
    populate_collection(
        collection,
        StageTestCase(
            id="idx_nonexist",
            docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
            msg="$out should not create target on unique index violation",
        ),
    )
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$unset": "_id"},
                {"$addFields": {"_id": "same"}},
                {"$out": target_name},
            ],
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": target_name}},
    )
    assertSuccess(
        result,
        [],
        msg="$out should not create the target collection when a unique index violation occurs",
    )


# Property [Nested Pipeline Restriction - View Definition]: $out in a view
# definition is rejected, but $out from a view source (not in the view
# definition) succeeds.
@pytest.mark.aggregate
def test_out_in_view_definition_error(collection):
    """Test $out in a view definition is rejected."""
    populate_collection(
        collection,
        StageTestCase(
            id="view_def_out",
            docs=[{"_id": 1, "value": 10}],
            msg="$out in a view definition should be rejected",
        ),
    )
    result = execute_command(
        collection,
        {
            "create": "bad_view",
            "viewOn": collection.name,
            "pipeline": [{"$out": "target"}],
        },
    )
    assertFailureCode(
        result,
        INVALID_VIEW_PIPELINE_ERROR,
        msg="$out in a view definition should produce an invalid view pipeline error",
    )


@pytest.mark.aggregate
def test_out_from_view_source_succeeds(collection):
    """Test $out from a view source succeeds."""
    populate_collection(
        collection,
        StageTestCase(
            id="view_source_out",
            docs=[{"_id": 1, "value": 10}],
            msg="$out from a view source should succeed",
        ),
    )
    db = collection.database
    view_name = "good_view_for_out"
    db.drop_collection(view_name)
    db.command(
        {"create": view_name, "viewOn": collection.name, "pipeline": [{"$match": {"_id": 1}}]}
    )
    target_name = "view_source_out_target"
    execute_command(
        db[view_name],
        {
            "aggregate": view_name,
            "pipeline": [{"$out": target_name}],
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {"find": target_name, "filter": {}},
    )
    assertSuccess(
        result,
        [{"_id": 1, "value": 10}],
        msg="$out from a view source should write the view's results to the target collection",
    )


# Property [Aggregation Options]: standard aggregation options (collation,
# hint, maxTimeMS, allowDiskUse, bypassDocumentValidation) are accepted
# with $out pipelines.
@pytest.mark.aggregate
@pytest.mark.parametrize(
    "extra_opts",
    [
        pytest.param({"collation": {"locale": "en", "strength": 2}}, id="collation"),
        pytest.param({"hint": "_id_"}, id="hint"),
        pytest.param({"maxTimeMS": 60_000}, id="maxTimeMS"),
        pytest.param({"allowDiskUse": True}, id="allowDiskUse"),
        pytest.param({"bypassDocumentValidation": True}, id="bypassDocumentValidation"),
    ],
)
def test_out_aggregation_options(collection, extra_opts):
    """Test $out succeeds with standard aggregation options."""
    populate_collection(
        collection,
        StageTestCase(
            id="agg_opts",
            docs=[{"_id": 1, "value": 10}],
            msg="$out should accept standard aggregation options",
        ),
    )
    target_name = "agg_opts_target"
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$out": target_name}],
            "cursor": {},
            **extra_opts,
        },
    )
    assertSuccess(
        result,
        [],
        msg=f"$out should succeed with aggregation options {extra_opts!r}",
    )


# Property [Read Concern Acceptance]: non-linearizable read concerns
# (majority, local, available) are accepted with $out pipelines.
@pytest.mark.aggregate
@pytest.mark.parametrize(
    "read_concern_level",
    [
        pytest.param("majority", id="majority"),
        pytest.param("local", id="local"),
        pytest.param("available", id="available"),
    ],
)
def test_out_read_concern_acceptance(collection, read_concern_level):
    """Test $out succeeds with non-linearizable read concern levels."""
    populate_collection(
        collection,
        StageTestCase(
            id="read_concern",
            docs=[{"_id": 1, "value": 10}],
            msg="$out should accept non-linearizable read concerns",
        ),
    )
    target_name = f"rc_{read_concern_level}_target"
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$out": target_name}],
            "cursor": {},
            "readConcern": {"level": read_concern_level},
        },
    )
    assertSuccess(
        result,
        [],
        msg=f"$out should succeed with readConcern level {read_concern_level!r}",
    )


# Property [Read Concern Errors]: linearizable read concern with $out
# produces an invalid options error.
@pytest.mark.aggregate
def test_out_read_concern_linearizable_error(collection):
    """Test $out rejects linearizable read concern."""
    populate_collection(
        collection,
        StageTestCase(
            id="rc_linearizable",
            docs=[{"_id": 1, "value": 10}],
            msg="$out should reject linearizable read concern",
        ),
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$out": "rc_linearizable_target"}],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
    )
    assertFailureCode(
        result,
        INVALID_OPTIONS_ERROR,
        msg="$out should reject linearizable read concern",
    )


# Property [Schema Validation Success]: when the target collection has
# validationAction set to warn the write succeeds, and
# bypassDocumentValidation bypasses schema validation errors.
@pytest.mark.aggregate
@pytest.mark.parametrize(
    "validation_action,bypass",
    [
        pytest.param("warn", False, id="validation_action_warn"),
        pytest.param("error", True, id="bypass_document_validation"),
    ],
)
def test_out_schema_validation_success(collection, validation_action, bypass):
    """Test $out succeeds when schema validation is warn or bypassed."""
    populate_collection(
        collection,
        StageTestCase(
            id="schema_val",
            docs=[{"_id": 1, "value": "not_a_number"}],
            msg="$out should succeed with schema validation warn or bypass",
        ),
    )
    db = collection.database
    target_name = f"schema_val_{validation_action}_{bypass}_target"
    db.drop_collection(target_name)
    db.command(
        {
            "create": target_name,
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["value"],
                    "properties": {"value": {"bsonType": "int"}},
                }
            },
            "validationAction": validation_action,
        }
    )
    cmd: dict[str, Any] = {
        "aggregate": collection.name,
        "pipeline": [{"$out": target_name}],
        "cursor": {},
    }
    if bypass:
        cmd["bypassDocumentValidation"] = True
    result = execute_command(collection, cmd)
    assertSuccess(
        result,
        [{"_id": 1, "value": "not_a_number"}],
        msg=(
            f"$out should succeed with validationAction={validation_action!r}"
            f" and bypass={bypass!r}"
        ),
        transform=lambda _: list(db[target_name].find({}, {"_id": 1, "value": 1})),
    )


# Property [Schema Validation Errors]: when the target collection has
# validationAction set to error and an invalid document is produced, the
# write fails with a document validation failure error and the pre-existing
# collection is unchanged.
@pytest.mark.aggregate
def test_out_schema_validation_error(collection):
    """Test $out fails with schema validation error and leaves existing data unchanged."""
    populate_collection(
        collection,
        StageTestCase(
            id="schema_val_err",
            docs=[{"_id": 1, "value": "not_a_number"}],
            msg="$out should fail with schema validation error",
        ),
    )
    db = collection.database
    target_name = "schema_val_error_target"
    db.drop_collection(target_name)
    db.command(
        {
            "create": target_name,
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["value"],
                    "properties": {"value": {"bsonType": "int"}},
                }
            },
            "validationAction": "error",
        }
    )
    db[target_name].insert_one({"_id": 99, "value": 42})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$out": target_name}],
            "cursor": {},
        },
    )
    assertFailure(
        result,
        {"code": DOCUMENT_VALIDATION_FAILURE_ERROR, "unchanged": [{"_id": 99, "value": 42}]},
        msg=(
            "$out should fail with document validation failure when validationAction"
            " is error and the pre-existing collection should be unchanged"
        ),
        transform=lambda err: {
            "code": err["code"],
            "unchanged": list(db[target_name].find({}, {"_id": 1, "value": 1})),
        },
    )


def _execute_in_transaction(collection, command: dict[str, Any]) -> Any:
    """Execute a command inside a transaction, returning the result or exception."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        try:
            return collection.database.command(command, session=session)
        except Exception as e:
            return e
        finally:
            session.abort_transaction()


# Property [Transaction Errors]: using $out inside a transaction produces
# an error.
@pytest.mark.aggregate
def test_out_transaction_error(collection):
    """Test $out inside a transaction produces an error."""
    populate_collection(
        collection,
        StageTestCase(
            id="transaction_out",
            docs=[{"_id": 1, "value": 10}],
            msg="$out inside a transaction should produce an error",
        ),
    )
    # Verify the pipeline works outside a transaction first.
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$out": "txn_target"}],
            "cursor": {},
        },
    )
    result = _execute_in_transaction(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$out": "txn_target"}],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg="$out inside a transaction should produce an error",
    )


# Property [Byte-Based Namespace Limit]: the namespace length limit (255
# bytes) is byte-based, not character-based - multi-byte characters consume
# more of the limit per character than single-byte characters.
@pytest.mark.aggregate
def test_out_byte_based_namespace_limit(collection):
    """Test $out namespace limit is byte-based, not character-based."""
    populate_collection(
        collection,
        StageTestCase(
            id="byte_limit",
            docs=[{"_id": 1}],
            msg="$out namespace limit should be byte-based",
        ),
    )
    db_name = collection.database.name
    # Namespace = db_name + "." + coll_name; limit is 255 bytes.
    prefix_bytes = len(db_name.encode("utf-8")) + 1
    max_coll_bytes = 255 - prefix_bytes

    # CJK character U+4E2D is 3 bytes in UTF-8. Use enough CJK characters
    # to exceed the byte limit while staying under the character count that
    # would fit with single-byte characters.
    cjk_char_count = (max_coll_bytes // 3) + 1
    cjk_name = "\u4e2d" * cjk_char_count
    # The CJK name has fewer characters than max_coll_bytes but exceeds
    # the byte limit.
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": cjk_name}], "cursor": {}},
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg=(
            "$out should reject a collection name that exceeds 255 namespace bytes"
            " even though the character count is within the single-byte limit"
        ),
    )
