"""Tests for $concatArrays accumulator: BSON type preservation in array elements."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Regex

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [BSON Element Preservation]: $concatArrays preserves all BSON types
# when they appear as array elements.
CONCATARRAYS_BSON_ELEMENT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_int32_elements",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": [3]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, 2, 3]}],
        msg="$concatArrays should preserve int32 elements",
    ),
    AccumulatorTestCase(
        "bson_int64_elements",
        docs=[
            {"_id": 1, "v": [Int64(100)]},
            {"_id": 2, "v": [Int64(200)]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Int64(100), Int64(200)]}],
        msg="$concatArrays should preserve Int64 elements",
    ),
    AccumulatorTestCase(
        "bson_double_elements",
        docs=[
            {"_id": 1, "v": [1.5]},
            {"_id": 2, "v": [2.5]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1.5, 2.5]}],
        msg="$concatArrays should preserve double elements",
    ),
    AccumulatorTestCase(
        "bson_decimal128_elements",
        docs=[
            {"_id": 1, "v": [Decimal128("1.1")]},
            {"_id": 2, "v": [Decimal128("2.2")]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Decimal128("1.1"), Decimal128("2.2")]}],
        msg="$concatArrays should preserve Decimal128 elements",
    ),
    AccumulatorTestCase(
        "bson_string_elements",
        docs=[
            {"_id": 1, "v": ["hello"]},
            {"_id": 2, "v": ["world"]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": ["hello", "world"]}],
        msg="$concatArrays should preserve string elements",
    ),
    AccumulatorTestCase(
        "bson_boolean_elements",
        docs=[
            {"_id": 1, "v": [True]},
            {"_id": 2, "v": [False]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [True, False]}],
        msg="$concatArrays should preserve boolean elements",
    ),
    AccumulatorTestCase(
        "bson_datetime_elements",
        docs=[
            {"_id": 1, "v": [datetime(2023, 1, 1, tzinfo=timezone.utc)]},
            {"_id": 2, "v": [datetime(2024, 6, 15, tzinfo=timezone.utc)]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[
            {
                "_id": None,
                "result": [
                    datetime(2023, 1, 1, tzinfo=timezone.utc),
                    datetime(2024, 6, 15, tzinfo=timezone.utc),
                ],
            }
        ],
        msg="$concatArrays should preserve datetime elements",
    ),
    AccumulatorTestCase(
        "bson_objectid_elements",
        docs=[
            {"_id": 1, "v": [ObjectId("000000000000000000000001")]},
            {"_id": 2, "v": [ObjectId("000000000000000000000002")]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[
            {
                "_id": None,
                "result": [
                    ObjectId("000000000000000000000001"),
                    ObjectId("000000000000000000000002"),
                ],
            }
        ],
        msg="$concatArrays should preserve ObjectId elements",
    ),
    AccumulatorTestCase(
        "bson_embedded_document_elements",
        docs=[
            {"_id": 1, "v": [{"a": 1}]},
            {"_id": 2, "v": [{"b": 2}]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{"a": 1}, {"b": 2}]}],
        msg="$concatArrays should preserve embedded document elements",
    ),
    AccumulatorTestCase(
        "bson_null_elements",
        docs=[
            {"_id": 1, "v": [None]},
            {"_id": 2, "v": [None]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [None, None]}],
        msg="$concatArrays should preserve null as array element (not error)",
    ),
    AccumulatorTestCase(
        "bson_binary_elements",
        docs=[
            {"_id": 1, "v": [Binary(b"\x01")]},
            {"_id": 2, "v": [Binary(b"\x02")]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [b"\x01", b"\x02"]}],
        msg="$concatArrays should preserve Binary elements",
    ),
    AccumulatorTestCase(
        "bson_regex_elements",
        docs=[
            {"_id": 1, "v": [Regex("abc", "i")]},
            {"_id": 2, "v": [Regex("def", "")]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Regex("abc", "i"), Regex("def", "")]}],
        msg="$concatArrays should preserve Regex elements",
    ),
    AccumulatorTestCase(
        "bson_mixed_type_elements",
        docs=[
            {"_id": 1, "v": [1, "hello", True]},
            {"_id": 2, "v": [None, 3.14]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, "hello", True, None, 3.14]}],
        msg="$concatArrays should preserve mixed BSON types in order",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_BSON_ELEMENT_TESTS))
def test_concatArrays_bson_elements(collection, test_case: AccumulatorTestCase):
    """Test $concatArrays BSON element type preservation."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
