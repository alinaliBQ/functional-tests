"""Tests for $max accumulator BSON comparison order and type distinction."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ===========================================================================
# 1. BSON Comparison Order (Cross-Type)
# ===========================================================================

# Property [BSON Comparison Order]: $max compares values using BSON comparison
# order when documents contain different types.
# BSON order: MinKey < Number < String < Object < Array < Binary < ObjectId
# < Boolean < Date < Timestamp < Regex < Code < MaxKey.
MAX_BSON_ORDER_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_minkey_vs_number",
        docs=[{"v": MinKey()}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should pick number over MinKey per BSON order",
    ),
    AccumulatorTestCase(
        "bson_number_vs_string",
        docs=[{"v": 100}, {"v": "hello"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "hello"}],
        msg="$max should pick string over number per BSON order",
    ),
    AccumulatorTestCase(
        "bson_string_vs_object",
        docs=[{"v": "zzz"}, {"v": {"a": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 1}}],
        msg="$max should pick object over string per BSON order",
    ),
    AccumulatorTestCase(
        "bson_object_vs_array",
        docs=[{"v": {"z": 99}}, {"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1]}],
        msg="$max should pick array over object per BSON order",
    ),
    AccumulatorTestCase(
        "bson_array_vs_binary",
        docs=[{"v": [999]}, {"v": Binary(b"\x00")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": b"\x00"}],
        msg="$max should pick binary over array per BSON order",
    ),
    AccumulatorTestCase(
        "bson_binary_vs_objectid",
        docs=[
            {"v": Binary(b"\xff" * 100)},
            {"v": ObjectId("000000000000000000000001")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ObjectId("000000000000000000000001")}],
        msg="$max should pick ObjectId over binary per BSON order",
    ),
    AccumulatorTestCase(
        "bson_objectid_vs_boolean",
        docs=[{"v": ObjectId("ffffffffffffffffffffffff")}, {"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$max should pick boolean over ObjectId per BSON order",
    ),
    AccumulatorTestCase(
        "bson_boolean_vs_datetime",
        docs=[{"v": True}, {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        msg="$max should pick datetime over boolean per BSON order",
    ),
    AccumulatorTestCase(
        "bson_datetime_vs_timestamp",
        docs=[
            {"v": datetime(9999, 12, 31, tzinfo=timezone.utc)},
            {"v": Timestamp(0, 1)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Timestamp(0, 1)}],
        msg="$max should pick timestamp over datetime per BSON order",
    ),
    AccumulatorTestCase(
        "bson_timestamp_vs_regex",
        docs=[{"v": Timestamp(4294967295, 4294967295)}, {"v": Regex("a")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Regex("a")}],
        msg="$max should pick regex over timestamp per BSON order",
    ),
    # NOTE: bson_regex_vs_code, bson_code_vs_maxkey, and bson_minkey_vs_maxkey
    # are stage-dependent and tested in test_accumulator_max_stage_divergence.py.
    AccumulatorTestCase(
        "bson_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$max should pick False over 0 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "bson_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$max should pick True over 1 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "bson_string_before_number",
        docs=[{"v": "a"}, {"v": 999999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "a"}],
        msg="$max should pick string over number regardless of insertion order",
    ),
    # NOTE: bson_maxkey_before_minkey is stage-dependent and tested in
    # test_accumulator_max_stage_divergence.py.
]


# ===========================================================================
# 2. BSON Type Distinction
# ===========================================================================

# Property [BSON Type Distinction]: values of different BSON types are
# distinct even when they appear similar.
MAX_TYPE_DISTINCTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "distinct_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$max should pick False over 0 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "distinct_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$max should pick True over 1 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "distinct_empty_string_vs_null",
        docs=[{"v": ""}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ""}],
        msg="$max should exclude null and return empty string",
    ),
    AccumulatorTestCase(
        "distinct_numeric_string",
        docs=[{"v": "123"}, {"v": 1000000}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "123"}],
        msg="$max should pick string '123' over int 1000000 (string > number, no coercion)",
    ),
]


# ===========================================================================
# Combined success tests and test function
# ===========================================================================

MAX_BSON_ORDER_SUCCESS_TESTS = MAX_BSON_ORDER_TESTS + MAX_TYPE_DISTINCTION_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MAX_BSON_ORDER_SUCCESS_TESTS))
def test_accumulator_max_bson_order(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator BSON comparison order and type distinction via $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
