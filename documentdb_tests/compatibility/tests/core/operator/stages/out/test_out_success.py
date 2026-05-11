"""Tests for $out stage - success cases."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64

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
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
)

# Property [Syntax Forms]: $out accepts a string (same-database output), a
# document with db/coll (cross-database output), or a document with db/coll
# and timeseries (time series collection output), and each form writes the
# pipeline results to the specified target.
OUT_SYNTAX_FORMS_TESTS: list[OutTestCase] = [
    OutTestCase(
        "string_form_same_database",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        target_coll="syntax_string_target",
        out_spec=None,
        expected_type="collection",
        expected_options={},
        msg="$out string form should write results to a collection in the same database",
    ),
    OutTestCase(
        "document_form_db_and_coll",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        target_coll="syntax_doc_target",
        out_spec={},
        expected_type="collection",
        expected_options={},
        msg="$out document form with db and coll should write results to the specified collection",
    ),
    OutTestCase(
        "document_form_with_timeseries",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="syntax_ts_target",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg="$out document form with timeseries should create a time series collection",
    ),
]

# Property [Null as Absent]: null values for timeseries and its sub-fields
# (metaField, granularity, bucketMaxSpanSeconds, bucketRoundingSeconds) are
# treated as absent, producing the same collection as if the field were omitted.
OUT_NULL_SUCCESS_TESTS: list[OutTestCase] = [
    OutTestCase(
        "null_timeseries_regular_collection",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="target_ts_null",
        out_spec={"timeseries": None},
        expected_type="collection",
        expected_options={},
        msg="$out should treat timeseries null as absent and create a regular collection",
    ),
    OutTestCase(
        "null_meta_field_omitted",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="target_meta_null",
        out_spec={"timeseries": {"timeField": "ts", "metaField": None}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg="$out should treat metaField null as absent and omit it from timeseries options",
    ),
    OutTestCase(
        "null_granularity_defaults_to_seconds",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="target_gran_null",
        out_spec={"timeseries": {"timeField": "ts", "granularity": None}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg="$out should treat granularity null as absent and default to 'seconds'",
    ),
    OutTestCase(
        "null_bucket_params_defaults_to_granularity",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="target_bucket_null",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": None,
                "bucketRoundingSeconds": None,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg=(
            "$out should treat null bucketMaxSpanSeconds and bucketRoundingSeconds"
            " as absent and default to granularity-based bucketing"
        ),
    ),
]

# Property [Collection Name Acceptance]: any non-empty string of non-null
# bytes that does not match a rejection rule is accepted as a collection name.
OUT_COLLECTION_NAME_ACCEPTANCE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "control_character",
        docs=[{"_id": 1}],
        target_coll="\x01",
        expected_type="collection",
        expected_options={},
        msg="$out should accept a control character as a collection name",
    ),
    OutTestCase(
        "embedded_control_character",
        docs=[{"_id": 1}],
        target_coll="test\x1fcoll",
        expected_type="collection",
        expected_options={},
        msg="$out should accept embedded control characters in a collection name",
    ),
    OutTestCase(
        "unicode_no_break_space",
        docs=[{"_id": 1}],
        target_coll="\u00a0",
        expected_type="collection",
        expected_options={},
        msg="$out should accept Unicode no-break space as a collection name",
    ),
    OutTestCase(
        "zero_width_space",
        docs=[{"_id": 1}],
        target_coll="\u200b",
        expected_type="collection",
        expected_options={},
        msg="$out should accept zero-width space as a collection name",
    ),
    OutTestCase(
        "bom_character",
        docs=[{"_id": 1}],
        target_coll="\ufeff",
        expected_type="collection",
        expected_options={},
        msg="$out should accept BOM character as a collection name",
    ),
    OutTestCase(
        "emoji",
        docs=[{"_id": 1}],
        target_coll="\U0001f389",
        expected_type="collection",
        expected_options={},
        msg="$out should accept emoji as a collection name",
    ),
    OutTestCase(
        "cjk_characters",
        docs=[{"_id": 1}],
        target_coll="\u4e2d\u6587",
        expected_type="collection",
        expected_options={},
        msg="$out should accept CJK characters as a collection name",
    ),
    OutTestCase(
        "punctuation",
        docs=[{"_id": 1}],
        target_coll="a!@#b",
        expected_type="collection",
        expected_options={},
        msg="$out should accept punctuation in a collection name",
    ),
    OutTestCase(
        "single_character",
        docs=[{"_id": 1}],
        target_coll="a",
        expected_type="collection",
        expected_options={},
        msg="$out should accept a single-character collection name",
    ),
    OutTestCase(
        "single_digit",
        docs=[{"_id": 1}],
        target_coll="1",
        expected_type="collection",
        expected_options={},
        msg="$out should accept a single-digit collection name",
    ),
    OutTestCase(
        "digits_only",
        docs=[{"_id": 1}],
        target_coll="123",
        expected_type="collection",
        expected_options={},
        msg="$out should accept a digits-only collection name",
    ),
    OutTestCase(
        "temp_prefix",
        docs=[{"_id": 1}],
        target_coll="tmp.agg_out.",
        expected_type="collection",
        expected_options={},
        msg="$out should accept the tmp.agg_out. prefix as a regular collection name",
    ),
]

# Property [Timeseries Collection Creation]: $out creates a new time
# series collection when valid timeseries options are provided and the
# target does not exist, including edge cases where metaField is "_id" or
# matches timeField.
OUT_TIMESERIES_CREATION_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_meta_field_is_id",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="ts_creation_meta_id",
        out_spec={"timeseries": {"timeField": "ts", "metaField": "_id"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "metaField": "_id",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg='$out should accept metaField set to "_id" without error',
    ),
    OutTestCase(
        "ts_meta_field_same_as_time_field",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "value": 10}],
        target_coll="ts_creation_meta_same",
        out_spec={"timeseries": {"timeField": "ts", "metaField": "ts"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "metaField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg="$out should accept metaField set to the same value as timeField without error",
    ),
]

# Property [Bucket Param Type Acceptance]: bucketMaxSpanSeconds and
# bucketRoundingSeconds accept int32, Int64, float, and Decimal128, and the
# equality check between them is type-insensitive.
OUT_BUCKET_PARAM_TYPE_ACCEPTANCE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "bucket_int32",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_int32",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 100,
                "bucketRoundingSeconds": 100,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept int32 for bucket parameters",
    ),
    OutTestCase(
        "bucket_int64",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_int64",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Int64(100),
                "bucketRoundingSeconds": Int64(100),
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept Int64 for bucket parameters",
    ),
    OutTestCase(
        "bucket_float",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_float",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 100.0,
                "bucketRoundingSeconds": 100.0,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept float for bucket parameters",
    ),
    OutTestCase(
        "bucket_decimal128",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_decimal128",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": Decimal128("100"),
                "bucketRoundingSeconds": Decimal128("100"),
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept Decimal128 for bucket parameters",
    ),
    OutTestCase(
        "bucket_cross_int32_int64",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_cross_i32_i64",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 100,
                "bucketRoundingSeconds": Int64(100),
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept cross-type int32/Int64 bucket parameters",
    ),
    OutTestCase(
        "bucket_cross_float_decimal128",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_cross_f_d128",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 100.0,
                "bucketRoundingSeconds": Decimal128("100"),
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 100,
                "bucketMaxSpanSeconds": 100,
            }
        },
        msg="$out should accept cross-type float/Decimal128 bucket parameters",
    ),
    OutTestCase(
        "bucket_float_truncation_success",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_float_trunc",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 1.5,
                "bucketRoundingSeconds": 1.5,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 1,
                "bucketMaxSpanSeconds": 1,
            }
        },
        msg="$out should truncate float 1.5 to int32 1 for bucket parameters",
    ),
    OutTestCase(
        "bucket_decimal128_bankers_rounding",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_dec_bankers",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_ONE_AND_HALF,
                "bucketRoundingSeconds": DECIMAL128_ONE_AND_HALF,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 2,
                "bucketMaxSpanSeconds": 2,
            }
        },
        msg="$out should round Decimal128 1.5 to 2 (banker's rounding) for bucket parameters",
    ),
    OutTestCase(
        "bucket_decimal128_bankers_round_down",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_dec_bank_dn",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": DECIMAL128_TWO_AND_HALF,
                "bucketRoundingSeconds": DECIMAL128_TWO_AND_HALF,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 2,
                "bucketMaxSpanSeconds": 2,
            }
        },
        msg="$out should round Decimal128 2.5 to 2 (banker's rounding) for bucket parameters",
    ),
    OutTestCase(
        "bucket_cross_coerced_equality",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_cross_coerce",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 2,
                "bucketRoundingSeconds": DECIMAL128_ONE_AND_HALF,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 2,
                "bucketMaxSpanSeconds": 2,
            }
        },
        msg=(
            "$out should accept cross-type bucket params when coerced values are"
            " equal (int32 2 and Decimal128 1.5 -> 2)"
        ),
    ),
    OutTestCase(
        "bucket_range_min",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_range_min",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 1,
                "bucketRoundingSeconds": 1,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 1,
                "bucketMaxSpanSeconds": 1,
            }
        },
        msg="$out should accept bucket parameters at the minimum valid value (1)",
    ),
    OutTestCase(
        "bucket_range_max",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="bucket_range_max",
        out_spec={
            "timeseries": {
                "timeField": "ts",
                "bucketMaxSpanSeconds": 31_536_000,
                "bucketRoundingSeconds": 31_536_000,
            }
        },
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "bucketRoundingSeconds": 31_536_000,
                "bucketMaxSpanSeconds": 31_536_000,
            }
        },
        msg="$out should accept bucket parameters at the maximum valid value (31536000)",
    ),
]

# Property [Timeseries Granularity]: valid granularity values ("seconds",
# "minutes", "hours") are accepted and each produces the corresponding
# bucketMaxSpanSeconds default.
OUT_TIMESERIES_GRANULARITY_TESTS: list[OutTestCase] = [
    OutTestCase(
        "granularity_seconds",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_gran_seconds",
        out_spec={"timeseries": {"timeField": "ts", "granularity": "seconds"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "seconds",
                "bucketMaxSpanSeconds": 3_600,
            }
        },
        msg="$out should accept granularity 'seconds'",
    ),
    OutTestCase(
        "granularity_minutes",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_gran_minutes",
        out_spec={"timeseries": {"timeField": "ts", "granularity": "minutes"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "minutes",
                "bucketMaxSpanSeconds": 86_400,
            }
        },
        msg="$out should accept granularity 'minutes'",
    ),
    OutTestCase(
        "granularity_hours",
        docs=[{"_id": 1, "ts": datetime(2024, 1, 1), "v": 1}],
        target_coll="ts_gran_hours",
        out_spec={"timeseries": {"timeField": "ts", "granularity": "hours"}},
        expected_type="timeseries",
        expected_options={
            "timeseries": {
                "timeField": "ts",
                "granularity": "hours",
                "bucketMaxSpanSeconds": 2_592_000,
            }
        },
        msg="$out should accept granularity 'hours'",
    ),
]

OUT_SUCCESS_TESTS = (
    OUT_SYNTAX_FORMS_TESTS
    + OUT_NULL_SUCCESS_TESTS
    + OUT_COLLECTION_NAME_ACCEPTANCE_TESTS
    + OUT_TIMESERIES_CREATION_TESTS
    + OUT_BUCKET_PARAM_TYPE_ACCEPTANCE_TESTS
    + OUT_TIMESERIES_GRANULARITY_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_SUCCESS_TESTS))
def test_out_success(collection, test_case: OutTestCase):
    """Test $out writes results and creates the correct collection type."""
    populate_collection(collection, test_case)
    out_stage = test_case.build_out_stage(collection)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
    )
    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": test_case.target_coll}},
    )
    expected_info = {
        "name": test_case.target_coll,
        "type": test_case.expected_type,
        "options": test_case.expected_options,
    }
    assertSuccess(
        result,
        [expected_info],
        msg=test_case.msg,
        transform=lambda docs: [
            {"name": d["name"], "type": d["type"], "options": d.get("options", {})} for d in docs
        ],
    )


# Property [Timeseries DateTime Acceptance]: all datetime boundary values
# are accepted as timeField values when writing to a timeseries collection
# via $out, including Unix epoch, pre-epoch, far future, minimum datetime,
# and millisecond precision.
OUT_TIMESERIES_DATETIME_ACCEPTANCE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_datetime_epoch",
        docs=[{"_id": 1, "ts": datetime(1970, 1, 1), "v": 1}],
        target_coll="ts_dt_epoch",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected=[{"ts": datetime(1970, 1, 1, tzinfo=timezone.utc), "v": 1}],
        msg="$out timeseries should accept Unix epoch as timeField value",
    ),
    OutTestCase(
        "ts_datetime_pre_epoch",
        docs=[{"_id": 1, "ts": datetime(1960, 6, 15), "v": 2}],
        target_coll="ts_dt_pre_epoch",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected=[{"ts": datetime(1960, 6, 15, tzinfo=timezone.utc), "v": 2}],
        msg="$out timeseries should accept pre-epoch dates as timeField value",
    ),
    OutTestCase(
        "ts_datetime_far_future",
        docs=[{"_id": 1, "ts": datetime(9999, 12, 31, 23, 59, 59), "v": 3}],
        target_coll="ts_dt_far_future",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected=[{"ts": datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc), "v": 3}],
        msg="$out timeseries should accept far future dates as timeField value",
    ),
    OutTestCase(
        "ts_datetime_minimum",
        docs=[{"_id": 1, "ts": datetime(1, 1, 1), "v": 4}],
        target_coll="ts_dt_minimum",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected=[{"ts": datetime(1, 1, 1, tzinfo=timezone.utc), "v": 4}],
        msg="$out timeseries should accept minimum datetime (0001-01-01) as timeField value",
    ),
    OutTestCase(
        "ts_datetime_millisecond_precision",
        docs=[{"_id": 1, "ts": datetime(2024, 6, 15, 12, 30, 45, 123_000), "v": 5}],
        target_coll="ts_dt_millis",
        out_spec={"timeseries": {"timeField": "ts"}},
        expected=[{"ts": datetime(2024, 6, 15, 12, 30, 45, 123_000, tzinfo=timezone.utc), "v": 5}],
        msg="$out timeseries should accept datetimes with millisecond precision as timeField value",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TIMESERIES_DATETIME_ACCEPTANCE_TESTS))
def test_out_timeseries_datetime_acceptance(collection, test_case: OutTestCase):
    """Test $out timeseries accepts datetime boundary values as timeField."""
    populate_collection(collection, test_case)
    out_stage = test_case.build_out_stage(collection)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
    )
    result = execute_command(
        collection,
        {
            "find": test_case.target_coll,
            "filter": {},
            "projection": {"_id": 0, "ts": 1, "v": 1},
        },
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Timeseries Existing Collection]: writing to an existing time
# series collection succeeds both with matching timeseries options and
# without specifying timeseries options (string and document form).
def _ts_existing_setup(c):
    c.database.drop_collection("ts_existing_target")
    c.database.command({"create": "ts_existing_target", "timeseries": {"timeField": "ts"}})


OUT_TIMESERIES_EXISTING_TESTS: list[OutTestCase] = [
    OutTestCase(
        "ts_existing_matching_options",
        docs=[{"_id": 1, "ts": datetime(2024, 6, 1), "value": 60}],
        target_coll="ts_existing_target",
        out_spec={"timeseries": {"timeField": "ts"}},
        setup=_ts_existing_setup,
        expected=[{"ts": datetime(2024, 6, 1, tzinfo=timezone.utc), "value": 60}],
        msg=(
            "$out should write to an existing time series collection with"
            " matching timeseries options"
        ),
    ),
    OutTestCase(
        "ts_existing_string_form",
        docs=[{"_id": 1, "ts": datetime(2024, 6, 1), "value": 60}],
        target_coll="ts_existing_target",
        setup=_ts_existing_setup,
        expected=[{"ts": datetime(2024, 6, 1, tzinfo=timezone.utc), "value": 60}],
        msg=(
            "$out should write to an existing time series collection using"
            " string form without timeseries options"
        ),
    ),
    OutTestCase(
        "ts_existing_document_form",
        docs=[{"_id": 1, "ts": datetime(2024, 6, 1), "value": 60}],
        target_coll="ts_existing_target",
        out_spec={},
        setup=_ts_existing_setup,
        expected=[{"ts": datetime(2024, 6, 1, tzinfo=timezone.utc), "value": 60}],
        msg=(
            "$out should write to an existing time series collection using"
            " document form without timeseries options"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_TIMESERIES_EXISTING_TESTS))
def test_out_timeseries_existing(collection, test_case: OutTestCase):
    """Test $out writes to an existing time series collection."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    out_stage = test_case.build_out_stage(collection)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
    )
    result = execute_command(
        collection,
        {
            "find": test_case.target_coll,
            "filter": {},
            "projection": {"_id": 0, "ts": 1, "value": 1},
        },
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Timeseries Cross-Database]: $out creates a time series collection
# in a different database when timeseries options are specified with a
# cross-database target.
@pytest.mark.aggregate
def test_out_timeseries_cross_db(collection):
    """Test $out creates a time series collection in a different database."""
    populate_collection(
        collection,
        OutTestCase(
            id="ts_cross_db",
            docs=[{"_id": 1, "ts": datetime(2024, 7, 1), "value": 70}],
            msg="$out should create a time series collection in a different database",
        ),
    )
    client = collection.database.client
    cross_db_name = collection.database.name + "_ts_cross"
    client.drop_database(cross_db_name)
    try:
        out_stage = {
            "$out": {
                "db": cross_db_name,
                "coll": "ts_cross_target",
                "timeseries": {"timeField": "ts"},
            }
        }
        execute_command(
            collection,
            {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
        )
        cross_db = client[cross_db_name]
        result = execute_command(
            cross_db["ts_cross_target"],
            {"listCollections": 1, "filter": {"name": "ts_cross_target"}},
        )
        assertSuccess(
            result,
            [
                {
                    "name": "ts_cross_target",
                    "type": "timeseries",
                    "options": {
                        "timeseries": {
                            "timeField": "ts",
                            "granularity": "seconds",
                            "bucketMaxSpanSeconds": 3_600,
                        }
                    },
                }
            ],
            msg="$out should create a time series collection in a different database",
            transform=lambda docs: [
                {
                    "name": d["name"],
                    "type": d["type"],
                    "options": d.get("options", {}),
                }
                for d in docs
            ],
        )

    finally:
        client.drop_database(cross_db_name)
