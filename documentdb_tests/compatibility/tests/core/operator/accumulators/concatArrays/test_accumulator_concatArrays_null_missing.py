"""Tests for $concatArrays accumulator: null, missing, and type rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null Handling]: null field values produce TYPE_MISMATCH_ERROR in
# accumulator context.
CONCATARRAYS_NULL_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_single",
        docs=[{"_id": 1, "v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on null field value",
    ),
    AccumulatorTestCase(
        "null_all",
        docs=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error when all field values are null",
    ),
    AccumulatorTestCase(
        "null_after_array",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": None},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on null even after valid arrays",
    ),
    AccumulatorTestCase(
        "null_before_array",
        docs=[
            {"_id": 1, "v": None},
            {"_id": 2, "v": [1, 2]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error on null even before valid arrays",
    ),
]

# Property [Non-Array Type Rejection]: every non-array, non-null BSON type
# produces TYPE_MISMATCH_ERROR.
CONCATARRAYS_TYPE_REJECTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_reject_string",
        docs=[{"_id": 1, "v": "hello"}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject string field value",
    ),
    AccumulatorTestCase(
        "type_reject_int32",
        docs=[{"_id": 1, "v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject int32 field value",
    ),
    AccumulatorTestCase(
        "type_reject_int64",
        docs=[{"_id": 1, "v": Int64(42)}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Int64 field value",
    ),
    AccumulatorTestCase(
        "type_reject_double",
        docs=[{"_id": 1, "v": 3.14}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject double field value",
    ),
    AccumulatorTestCase(
        "type_reject_decimal128",
        docs=[{"_id": 1, "v": Decimal128("1.5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Decimal128 field value",
    ),
    AccumulatorTestCase(
        "type_reject_bool_true",
        docs=[{"_id": 1, "v": True}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject boolean True field value",
    ),
    AccumulatorTestCase(
        "type_reject_bool_false",
        docs=[{"_id": 1, "v": False}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject boolean False field value",
    ),
    AccumulatorTestCase(
        "type_reject_object",
        docs=[{"_id": 1, "v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject embedded document field value",
    ),
    AccumulatorTestCase(
        "type_reject_empty_object",
        docs=[{"_id": 1, "v": {}}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject empty document field value",
    ),
    AccumulatorTestCase(
        "type_reject_objectid",
        docs=[{"_id": 1, "v": ObjectId()}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject ObjectId field value",
    ),
    AccumulatorTestCase(
        "type_reject_datetime",
        docs=[{"_id": 1, "v": datetime(2023, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject datetime field value",
    ),
    AccumulatorTestCase(
        "type_reject_binary",
        docs=[{"_id": 1, "v": Binary(b"\x01\x02")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Binary field value",
    ),
    AccumulatorTestCase(
        "type_reject_regex",
        docs=[{"_id": 1, "v": Regex("abc", "i")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Regex field value",
    ),
    AccumulatorTestCase(
        "type_reject_code",
        docs=[{"_id": 1, "v": Code("function(){}")}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Code field value",
    ),
    AccumulatorTestCase(
        "type_reject_timestamp",
        docs=[{"_id": 1, "v": Timestamp(1, 1)}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject Timestamp field value",
    ),
    AccumulatorTestCase(
        "type_reject_minkey",
        docs=[{"_id": 1, "v": MinKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject MinKey field value",
    ),
    AccumulatorTestCase(
        "type_reject_maxkey",
        docs=[{"_id": 1, "v": MaxKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should reject MaxKey field value",
    ),
]

# Property [Mixed Valid and Invalid]: when one document has a valid array and
# another has an invalid type, the error is raised.
CONCATARRAYS_MIXED_INVALID_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_array_and_null",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": None},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error when mixing array and null values",
    ),
    AccumulatorTestCase(
        "mixed_array_and_string",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": "hello"},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error when mixing array and string values",
    ),
    AccumulatorTestCase(
        "mixed_array_and_integer",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": 42},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$concatArrays should error when mixing array and integer values",
    ),
]

CONCATARRAYS_ERROR_TESTS = (
    CONCATARRAYS_NULL_ERROR_TESTS
    + CONCATARRAYS_TYPE_REJECTION_TESTS
    + CONCATARRAYS_MIXED_INVALID_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_ERROR_TESTS))
def test_accumulator_concatArrays_null_missing_errors(collection, test_case):
    """Test $concatArrays null, type rejection, and mixed invalid error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


# Property [Missing Field Handling]: missing fields are silently excluded from
# concatenation; when all inputs are missing, the result is an empty array.
CONCATARRAYS_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_all",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        expected=[{"_id": None, "result": []}],
        msg="$concatArrays should return empty array when all fields are missing",
    ),
    AccumulatorTestCase(
        "missing_single",
        docs=[{"_id": 1, "x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        expected=[{"_id": None, "result": []}],
        msg="$concatArrays should return empty array when the single document has missing field",
    ),
    AccumulatorTestCase(
        "missing_some_with_arrays",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "v": [3, 4]},
            {"_id": 3, "v": [5]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [3, 4, 5]}],
        msg="$concatArrays should exclude missing fields and concatenate remaining arrays",
    ),
    AccumulatorTestCase(
        "missing_among_arrays",
        docs=[
            {"_id": 1, "v": [1]},
            {"_id": 2, "x": 1},
            {"_id": 3, "v": [2]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, 2]}],
        msg="$concatArrays should skip missing field in middle and concatenate surrounding arrays",
    ),
    AccumulatorTestCase(
        "missing_first_doc",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "v": [10, 20]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 20]}],
        msg="$concatArrays should handle first document having missing field",
    ),
    AccumulatorTestCase(
        "missing_last_doc",
        docs=[
            {"_id": 1, "v": [10, 20]},
            {"_id": 2, "x": 1},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 20]}],
        msg="$concatArrays should handle last document having missing field",
    ),
    AccumulatorTestCase(
        "missing_many_one_array",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": 2},
            {"_id": 3, "x": 3},
            {"_id": 4, "v": [42]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [42]}],
        msg="$concatArrays should return the single array when most documents have missing field",
    ),
]

# Property [$$REMOVE Handling]: $$REMOVE via $cond is treated as missing and
# excluded from concatenation.
CONCATARRAYS_REMOVE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "remove_all",
        docs=[{"_id": 1, "v": [1]}, {"_id": 2, "v": [2]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$concatArrays": {"$cond": [False, "$v", "$$REMOVE"]}},
                }
            }
        ],
        expected=[{"_id": None, "result": []}],
        msg="$concatArrays should return empty array when all inputs are $$REMOVE",
    ),
    AccumulatorTestCase(
        "remove_some_with_arrays",
        docs=[
            {"_id": 1, "qty": 0, "v": [1, 2]},
            {"_id": 2, "qty": 5, "v": [3, 4]},
            {"_id": 3, "qty": 0, "v": [5, 6]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$concatArrays": {"$cond": [{"$gt": ["$qty", 0]}, "$v", "$$REMOVE"]}
                    },
                }
            },
        ],
        expected=[{"_id": None, "result": [3, 4]}],
        msg="$concatArrays should exclude $$REMOVE and concatenate remaining arrays",
    ),
    AccumulatorTestCase(
        "remove_preserves_duplicates",
        docs=[
            {"_id": 1, "qty": 1, "v": [1, 2]},
            {"_id": 2, "qty": 0, "v": [3, 4]},
            {"_id": 3, "qty": 1, "v": [1, 2]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$concatArrays": {"$cond": [{"$gt": ["$qty", 0]}, "$v", "$$REMOVE"]}
                    },
                }
            },
        ],
        expected=[{"_id": None, "result": [1, 2, 1, 2]}],
        msg="$concatArrays should preserve duplicates when using $$REMOVE conditionally",
    ),
]

CONCATARRAYS_MISSING_AND_REMOVE_TESTS = CONCATARRAYS_MISSING_TESTS + CONCATARRAYS_REMOVE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_MISSING_AND_REMOVE_TESTS))
def test_accumulator_concatArrays_missing(collection, test_case: AccumulatorTestCase):
    """Test $concatArrays missing field and $$REMOVE handling."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
