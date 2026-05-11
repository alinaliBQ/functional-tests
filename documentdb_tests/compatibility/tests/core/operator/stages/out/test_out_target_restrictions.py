"""Tests for $out stage - target collection restrictions, options, and special cases."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertFailure,
    assertFailureCode,
    assertResult,
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
from documentdb_tests.framework.parametrize import pytest_params

# Property [Target Collection Restriction Errors]: $out rejects writing to
# capped collections and views, and writing to a view with timeseries options
# produces a timeseries collection type error instead of the view-specific
# error.
OUT_TARGET_RESTRICTION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "capped_target",
        docs=[{"_id": 1, "value": 10}],
        target_coll="capped_out_target",
        setup=lambda c: (
            c.database.drop_collection("capped_out_target"),
            c.database.create_collection("capped_out_target", capped=True, size=1_048_576),
        ),
        msg="$out should reject writing to a capped collection",
        error_code=OUT_CAPPED_COLLECTION_ERROR,
    ),
    OutTestCase(
        "view_target",
        docs=[{"_id": 1, "value": 10}],
        target_coll="view_out_target",
        setup=lambda c: (
            c.database.drop_collection("view_out_target"),
            c.database.command({"create": "view_out_target", "viewOn": c.name, "pipeline": []}),
        ),
        msg="$out should reject writing to a view",
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    ),
    OutTestCase(
        "view_ts_target",
        docs=[{"_id": 1, "value": 10}],
        target_coll="view_ts_out_target",
        out_spec={"timeseries": {"timeField": "ts"}},
        setup=lambda c: (
            c.database.drop_collection("view_ts_out_target"),
            c.database.command({"create": "view_ts_out_target", "viewOn": c.name, "pipeline": []}),
        ),
        msg=(
            "$out to a view with timeseries options should produce a timeseries"
            " collection type error, not the view-specific error"
        ),
        error_code=OUT_TIMESERIES_COLLECTION_TYPE_ERROR,
    ),
]

# Property [Timeseries Existing Collection Errors]: writing with timeseries
# options to an existing regular collection produces a timeseries collection
# type error, and writing with mismatched timeseries options to an existing
# time series collection produces a timeseries options mismatch error
# regardless of which option differs.
OUT_TIMESERIES_EXISTING_COLLECTION_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_to_regular",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_to_regular_target",
        out_spec={"timeseries": {"timeField": "ts"}},
        setup=lambda c: (
            c.database.drop_collection("ts_to_regular_target"),
            c.database.create_collection("ts_to_regular_target"),
        ),
        msg=(
            "$out with timeseries options to an existing regular collection"
            " should produce a timeseries collection type error"
        ),
        error_code=OUT_TIMESERIES_COLLECTION_TYPE_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_different_time_field",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={"timeseries": {"timeField": "other"}},
        setup=lambda c: (
            c.database.drop_collection("ts_mismatch_target"),
            c.database.command({"create": "ts_mismatch_target", "timeseries": {"timeField": "ts"}}),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_meta_field_present_vs_absent",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={"timeseries": {"timeField": "ts", "metaField": "m"}},
        setup=lambda c: (
            c.database.drop_collection("ts_mismatch_target"),
            c.database.command({"create": "ts_mismatch_target", "timeseries": {"timeField": "ts"}}),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_different_meta_field",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={"timeseries": {"timeField": "ts", "metaField": "other"}},
        setup=lambda c: (
            c.database.drop_collection("ts_mismatch_target"),
            c.database.command(
                {
                    "create": "ts_mismatch_target",
                    "timeseries": {"timeField": "ts", "metaField": "m"},
                }
            ),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_different_granularity",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={"timeseries": {"timeField": "ts", "granularity": "hours"}},
        setup=lambda c: (
            c.database.drop_collection("ts_mismatch_target"),
            c.database.command(
                {
                    "create": "ts_mismatch_target",
                    "timeseries": {"timeField": "ts", "granularity": "seconds"},
                }
            ),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_granularity_vs_bucket_options",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={"timeseries": {"timeField": "ts", "granularity": "hours"}},
        setup=lambda c: (
            c.database.drop_collection("ts_mismatch_target"),
            c.database.command(
                {
                    "create": "ts_mismatch_target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": 100,
                        "bucketRoundingSeconds": 100,
                    },
                }
            ),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
    OutTestCase(
        "ts_mismatch_different_bucket_values",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_mismatch_target",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 200,
                "bucketRoundingSeconds": 200,
            }
        },
        setup=lambda c: (
            c.database.drop_collection("ts_mismatch_target"),
            c.database.command(
                {
                    "create": "ts_mismatch_target",
                    "timeseries": {
                        "timeField": "ts",
                        "bucketMaxSpanSeconds": 100,
                        "bucketRoundingSeconds": 100,
                    },
                }
            ),
        ),
        msg=(
            "$out with mismatched timeseries options to an existing time series"
            " collection should produce a timeseries options mismatch error"
        ),
        error_code=OUT_TIMESERIES_OPTIONS_MISMATCH_ERROR,
    ),
]

# Property [Index Constraint Errors]: unique index violations (including
# compound unique indexes) and duplicate _id values in the output produce a
# duplicate key error, and when a unique index violation occurs writing to a
# nonexistent target, the target collection is not created.
OUT_INDEX_CONSTRAINT_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "idx_unique",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 1}],
        target_coll="idx_unique_target",
        setup=lambda c: (
            c.database["idx_unique_target"].insert_many(
                [{"_id": 90, "x": 90}, {"_id": 91, "x": 91}]
            ),
            c.database["idx_unique_target"].create_index("x", unique=True),
        ),
        msg="$out should produce a duplicate key error on unique index violation",
        error_code=DUPLICATE_KEY_ERROR,
    ),
    OutTestCase(
        "idx_compound",
        docs=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1, "b": 2}],
        target_coll="idx_compound_target",
        setup=lambda c: (
            c.database["idx_compound_target"].insert_one({"_id": 99, "a": 99, "b": 99}),
            c.database["idx_compound_target"].create_index([("a", 1), ("b", 1)], unique=True),
        ),
        msg="$out should produce a duplicate key error on compound unique index violation",
        error_code=DUPLICATE_KEY_ERROR,
    ),
    OutTestCase(
        "idx_dup_id",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        target_coll="idx_dup_id_target",
        pipeline=[
            {"$unset": "_id"},
            {"$addFields": {"_id": "same"}},
            {"$out": "idx_dup_id_target"},
        ],
        msg="$out should produce a duplicate key error when output contains duplicate _id values",
        error_code=DUPLICATE_KEY_ERROR,
    ),
]

# Property [Read Concern Errors]: linearizable read concern with $out
# produces an invalid options error.
OUT_READ_CONCERN_ERROR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "rc_linearizable",
        docs=[{"_id": 1, "value": 10}],
        target_coll="rc_linearizable_target",
        pipeline=[
            {"$out": "rc_linearizable_target"},
        ],
        msg="$out should reject linearizable read concern",
        error_code=INVALID_OPTIONS_ERROR,
    ),
]


OUT_TARGET_RESTRICTION_TESTS = (
    OUT_TARGET_RESTRICTION_ERROR_TESTS
    + OUT_TIMESERIES_EXISTING_COLLECTION_ERROR_TESTS
    + OUT_INDEX_CONSTRAINT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TARGET_RESTRICTION_TESTS))
def test_out_target_restriction_error(collection, test_case: OutTestCase):
    """Test $out rejects invalid target configurations with the expected error code."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    if test_case.pipeline:
        pipeline = test_case.resolve_pipeline(collection.database.name)
    else:
        pipeline = [test_case.build_out_stage(collection)]
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_READ_CONCERN_ERROR_TESTS))
def test_out_read_concern_error(collection, test_case: OutTestCase):
    """Test $out rejects invalid read concern levels."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    if test_case.pipeline:
        pipeline = test_case.resolve_pipeline(collection.database.name)
    else:
        pipeline = [test_case.build_out_stage(collection)]
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


@pytest.mark.aggregate
def test_out_unique_violation_nonexistent_target_not_created(collection):
    """Test $out does not create the target when a unique index violation occurs."""
    db = collection.database
    target_name = "idx_nonexist_target"
    db.drop_collection(target_name)
    populate_collection(
        collection,
        OutTestCase(
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
        OutTestCase(
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
        OutTestCase(
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
OUT_AGGREGATION_OPTION_SUCCESS_TESTS: list[OutTestCase] = [
    OutTestCase(
        "agg_opts_collation",
        docs=[{"_id": 1, "value": 10}],
        target_coll="agg_opts_target",
        out_spec={"collation": {"locale": "en", "strength": 2}},
        msg="$out should succeed with aggregation option collation",
    ),
    OutTestCase(
        "agg_opts_hint",
        docs=[{"_id": 1, "value": 10}],
        target_coll="agg_opts_target",
        out_spec={"hint": "_id_"},
        msg="$out should succeed with aggregation option hint",
    ),
    OutTestCase(
        "agg_opts_max_time_ms",
        docs=[{"_id": 1, "value": 10}],
        target_coll="agg_opts_target",
        out_spec={"maxTimeMS": 60_000},
        msg="$out should succeed with aggregation option maxTimeMS",
    ),
    OutTestCase(
        "agg_opts_allow_disk_use",
        docs=[{"_id": 1, "value": 10}],
        target_coll="agg_opts_target",
        out_spec={"allowDiskUse": True},
        msg="$out should succeed with aggregation option allowDiskUse",
    ),
    OutTestCase(
        "agg_opts_bypass_doc_validation",
        docs=[{"_id": 1, "value": 10}],
        target_coll="agg_opts_target",
        out_spec={"bypassDocumentValidation": True},
        msg="$out should succeed with aggregation option bypassDocumentValidation",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_AGGREGATION_OPTION_SUCCESS_TESTS))
def test_out_aggregation_options(collection, test_case: OutTestCase):
    """Test $out succeeds with standard aggregation options."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    pipeline = [{"$out": test_case.target_coll}]
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
            **test_case.out_spec,
        },
    )
    assertSuccess(
        result,
        [],
        msg=test_case.msg,
    )


# Property [Read Concern Acceptance]: non-linearizable read concerns
# (majority, local, available) are accepted with $out pipelines.
OUT_READ_CONCERN_ACCEPTANCE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "rc_majority",
        docs=[{"_id": 1, "value": 10}],
        target_coll="rc_majority_target",
        out_spec={"readConcern": "majority"},
        msg="$out should succeed with readConcern level 'majority'",
    ),
    OutTestCase(
        "rc_local",
        docs=[{"_id": 1, "value": 10}],
        target_coll="rc_local_target",
        out_spec={"readConcern": "local"},
        msg="$out should succeed with readConcern level 'local'",
    ),
    OutTestCase(
        "rc_available",
        docs=[{"_id": 1, "value": 10}],
        target_coll="rc_available_target",
        out_spec={"readConcern": "available"},
        msg="$out should succeed with readConcern level 'available'",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_READ_CONCERN_ACCEPTANCE_TESTS))
def test_out_read_concern_acceptance(collection, test_case: OutTestCase):
    """Test $out succeeds with non-linearizable read concern levels."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    pipeline = [{"$out": test_case.target_coll}]
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
            "readConcern": {"level": test_case.out_spec["readConcern"]},
        },
    )
    assertSuccess(
        result,
        [],
        msg=test_case.msg,
    )


# Property [Schema Validation Success]: when the target collection has
# validationAction set to warn the write succeeds, and
# bypassDocumentValidation bypasses schema validation errors.
OUT_SCHEMA_VALIDATION_SUCCESS_TESTS: list[OutTestCase] = [
    OutTestCase(
        "schema_val_warn",
        docs=[{"_id": 1, "value": "not_a_number"}],
        target_coll="schema_val_warn_target",
        out_spec={"bypassDocumentValidation": False},
        setup=lambda c: (
            c.database.drop_collection("schema_val_warn_target"),
            c.database.command(
                {
                    "create": "schema_val_warn_target",
                    "validator": {
                        "$jsonSchema": {
                            "bsonType": "object",
                            "required": ["value"],
                            "properties": {"value": {"bsonType": "int"}},
                        }
                    },
                    "validationAction": "warn",
                }
            ),
        ),
        expected=[{"_id": 1, "value": "not_a_number"}],
        msg="$out should succeed with validationAction='warn'",
    ),
    OutTestCase(
        "schema_val_bypass",
        docs=[{"_id": 1, "value": "not_a_number"}],
        target_coll="schema_val_bypass_target",
        out_spec={"bypassDocumentValidation": True},
        setup=lambda c: (
            c.database.drop_collection("schema_val_bypass_target"),
            c.database.command(
                {
                    "create": "schema_val_bypass_target",
                    "validator": {
                        "$jsonSchema": {
                            "bsonType": "object",
                            "required": ["value"],
                            "properties": {"value": {"bsonType": "int"}},
                        }
                    },
                    "validationAction": "error",
                }
            ),
        ),
        expected=[{"_id": 1, "value": "not_a_number"}],
        msg="$out should succeed with bypassDocumentValidation=True",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_SCHEMA_VALIDATION_SUCCESS_TESTS))
def test_out_schema_validation_success(collection, test_case: OutTestCase):
    """Test $out succeeds when schema validation is warn or bypassed."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    pipeline = [{"$out": test_case.target_coll}]
    db = collection.database
    cmd: dict[str, Any] = {
        "aggregate": collection.name,
        "pipeline": pipeline,
        "cursor": {},
    }
    if test_case.out_spec["bypassDocumentValidation"]:
        cmd["bypassDocumentValidation"] = True
    result = execute_command(collection, cmd)
    assertSuccess(
        result,
        test_case.expected,
        msg=test_case.msg,
        transform=lambda _: list(db[test_case.target_coll].find({}, {"_id": 1, "value": 1})),
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
        OutTestCase(
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
        OutTestCase(
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
        OutTestCase(
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
