"""
BSON type element preservation tests for $concatArrays expression.

Tests that various BSON types are preserved when concatenating arrays,
including special numeric values and boundary values.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.concatArrays.utils.concatArrays_common import (  # noqa: E501
    ConcatArraysTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# ---------------------------------------------------------------------------
# BSON types preserved after concatenation
# ---------------------------------------------------------------------------
BSON_TYPE_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="int64_values",
        arrays=[[Int64(1), Int64(2)], [Int64(3)]],
        expected=[Int64(1), Int64(2), Int64(3)],
        msg="Should preserve Int64 values",
    ),
    ConcatArraysTest(
        id="decimal128_values",
        arrays=[[Decimal128("1.5")], [Decimal128("2.5"), Decimal128("3.5")]],
        expected=[Decimal128("1.5"), Decimal128("2.5"), Decimal128("3.5")],
        msg="Should preserve Decimal128 values",
    ),
    ConcatArraysTest(
        id="datetime_values",
        arrays=[
            [datetime(2024, 1, 1, tzinfo=timezone.utc)],
            [datetime(2024, 6, 1, tzinfo=timezone.utc)],
        ],
        expected=[
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 6, 1, tzinfo=timezone.utc),
        ],
        msg="Should preserve datetime values",
    ),
    ConcatArraysTest(
        id="objectid_values",
        arrays=[
            [ObjectId("000000000000000000000001")],
            [ObjectId("000000000000000000000002")],
        ],
        expected=[
            ObjectId("000000000000000000000001"),
            ObjectId("000000000000000000000002"),
        ],
        msg="Should preserve ObjectId values",
    ),
    ConcatArraysTest(
        id="binary_values",
        arrays=[[Binary(b"\x01", 0)], [Binary(b"\x02", 0)]],
        expected=[b"\x01", b"\x02"],
        msg="Should preserve Binary values",
    ),
    ConcatArraysTest(
        id="regex_values",
        arrays=[[Regex("^a", "i")], [Regex("^b", "i")]],
        expected=[Regex("^a", "i"), Regex("^b", "i")],
        msg="Should preserve Regex values",
    ),
    ConcatArraysTest(
        id="timestamp_values",
        arrays=[[Timestamp(1, 0)], [Timestamp(2, 0)]],
        expected=[Timestamp(1, 0), Timestamp(2, 0)],
        msg="Should preserve Timestamp values",
    ),
    ConcatArraysTest(
        id="minkey_maxkey",
        arrays=[[MinKey()], [MaxKey()]],
        expected=[MinKey(), MaxKey()],
        msg="Should preserve MinKey/MaxKey values",
    ),
    ConcatArraysTest(
        id="uuid_values",
        arrays=[
            [Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))],
            [Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef"))],
        ],
        expected=[
            Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
            Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef")),
        ],
        msg="Should preserve UUID binary values",
    ),
]

# ---------------------------------------------------------------------------
# Mixed BSON types across arrays
# ---------------------------------------------------------------------------
MIXED_BSON_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="mixed_bson_types",
        arrays=[[1, "two", Int64(3)], [Decimal128("4"), True, None, MinKey()]],
        expected=[1, "two", Int64(3), Decimal128("4"), True, None, MinKey()],
        msg="Should concatenate mixed BSON types preserving each",
    ),
    ConcatArraysTest(
        id="mixed_dates_and_ids",
        arrays=[
            [datetime(2024, 1, 1, tzinfo=timezone.utc), ObjectId("000000000000000000000001")],
            [Timestamp(1, 0), Binary(b"\x01", 0)],
        ],
        expected=[
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            ObjectId("000000000000000000000001"),
            Timestamp(1, 0),
            b"\x01",
        ],
        msg="Should concatenate dates, ObjectIds, timestamps, and binary",
    ),
    ConcatArraysTest(
        id="mixed_extremes",
        arrays=[[MinKey(), FLOAT_NEGATIVE_INFINITY, None], [FLOAT_INFINITY, MaxKey()]],
        expected=[MinKey(), FLOAT_NEGATIVE_INFINITY, None, FLOAT_INFINITY, MaxKey()],
        msg="Should concatenate MinKey, MaxKey, infinities, and null",
    ),
]

# ---------------------------------------------------------------------------
# Special numeric values as elements
# ---------------------------------------------------------------------------
SPECIAL_NUMERIC_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="infinity_values",
        arrays=[[FLOAT_INFINITY], [FLOAT_NEGATIVE_INFINITY]],
        expected=[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY],
        msg="Should preserve infinity values",
    ),
    ConcatArraysTest(
        id="decimal128_infinity",
        arrays=[[DECIMAL128_INFINITY], [DECIMAL128_NEGATIVE_INFINITY]],
        expected=[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        msg="Should preserve Decimal128 infinity values",
    ),
    ConcatArraysTest(
        id="boundary_values",
        arrays=[[INT32_MIN, INT32_MAX], [INT64_MIN, INT64_MAX]],
        expected=[INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX],
        msg="Should preserve numeric boundary values",
    ),
    ConcatArraysTest(
        id="negative_zero",
        arrays=[[DOUBLE_NEGATIVE_ZERO], [DECIMAL128_NEGATIVE_ZERO]],
        expected=[DOUBLE_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO],
        msg="Should preserve negative zero values",
    ),
]

# ---------------------------------------------------------------------------
# Element identity preservation
# ---------------------------------------------------------------------------
ELEMENT_PRESERVATION_TESTS: list[ConcatArraysTest] = [
    ConcatArraysTest(
        id="decimal128_trailing_zeros",
        arrays=[[Decimal128("1.0")], [Decimal128("1.00"), Decimal128("1.000")]],
        expected=[Decimal128("1.0"), Decimal128("1.00"), Decimal128("1.000")],
        msg="Decimal128 trailing zeros preserved",
    ),
    ConcatArraysTest(
        id="decimal128_nan",
        arrays=[[DECIMAL128_NAN], [Decimal128("1")]],
        expected=[DECIMAL128_NAN, Decimal128("1")],
        msg="Decimal128 NaN preserved",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_BSON_TESTS = (
    BSON_TYPE_TESTS + MIXED_BSON_TESTS + SPECIAL_NUMERIC_TESTS + ELEMENT_PRESERVATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_concatArrays_bson_insert(collection, test):
    """Test $concatArrays BSON types with values from inserted documents."""
    doc = {f"arr{i}": a for i, a in enumerate(test.arrays)}
    refs = [f"$arr{i}" for i in range(len(test.arrays))]
    result = execute_expression_with_insert(collection, {"$concatArrays": refs}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


TEST_SUBSET_FOR_LITERAL = [
    BSON_TYPE_TESTS[0],  # int64_values
    BSON_TYPE_TESTS[4],  # binary_values
    MIXED_BSON_TESTS[0],  # mixed_bson_types
    SPECIAL_NUMERIC_TESTS[0],  # infinity_values
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_concatArrays_bson_literal(collection, test):
    """Test $concatArrays BSON types with literal values."""
    args = [{"$literal": a} if isinstance(a, list) else a for a in test.arrays]
    result = execute_expression(collection, {"$concatArrays": args})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
