"""Tests for $unwind stage — error precedence."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FIELD_PATH_TRAILING_DOT_ERROR,
    UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
    UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
    UNWIND_PATH_NO_DOLLAR_ERROR,
    UNWIND_PATH_TYPE_ERROR,
    UNWIND_PRESERVE_NULL_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Error Precedence]: validation proceeds in two phases - phase 1
# iterates fields in BSON document order (path type, includeArrayIndex
# type/dollar, preserveNullAndEmptyArrays type, unrecognized field, missing
# path) and phase 2 performs post-iteration semantic validation (path
# no-dollar, path field path, includeArrayIndex field path); the first error
# encountered wins, and all validation errors fire even on empty and
# non-existent collections.
UNWIND_ERROR_PRECEDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "precedence_path_type_over_index_type",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": 123, "includeArrayIndex": 456}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="path type error should take precedence over includeArrayIndex type error",
    ),
    StageTestCase(
        "precedence_path_type_over_preserve_type",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": 123, "preserveNullAndEmptyArrays": "bad"}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="path type error should take precedence over preserveNullAndEmptyArrays type error",
    ),
    StageTestCase(
        "precedence_path_type_over_unrecognized",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": 123, "badField": True}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="path type error should take precedence over unrecognized field error",
    ),
    StageTestCase(
        "precedence_index_type_over_preserve_type",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": 123,
                    "preserveNullAndEmptyArrays": "bad",
                }
            }
        ],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg=(
            "includeArrayIndex type error should take precedence over"
            " preserveNullAndEmptyArrays type error"
        ),
    ),
    StageTestCase(
        "precedence_index_type_over_path_no_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "no_dollar", "includeArrayIndex": 456}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg=(
            "includeArrayIndex type error (phase 1) should take precedence"
            " over path no-dollar (phase 2)"
        ),
    ),
    StageTestCase(
        "precedence_preserve_type_over_index_field_path",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "a..b",
                    "preserveNullAndEmptyArrays": "bad",
                }
            }
        ],
        error_code=UNWIND_PRESERVE_NULL_TYPE_ERROR,
        msg=(
            "preserveNullAndEmptyArrays type error (phase 1) should take"
            " precedence over includeArrayIndex field path (phase 2)"
        ),
    ),
    StageTestCase(
        "precedence_path_no_dollar_over_index_field_path",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "no_dollar", "includeArrayIndex": "a..b"}}],
        error_code=UNWIND_PATH_NO_DOLLAR_ERROR,
        msg=(
            "path no-dollar error should take precedence over"
            " includeArrayIndex field path error in phase 2"
        ),
    ),
    StageTestCase(
        "precedence_bson_order_index_type_before_path_type",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"includeArrayIndex": 456, "path": 123}}],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_TYPE_ERROR,
        msg=(
            "When includeArrayIndex appears before path in BSON document order,"
            " includeArrayIndex type error should win over path type error"
        ),
    ),
    StageTestCase(
        "precedence_index_dollar_precedes_path_no_dollar",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "a",
                    "includeArrayIndex": "$idx",
                }
            }
        ],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
        msg=(
            "includeArrayIndex dollar prefix error should fire before"
            " path no-dollar semantic validation error"
        ),
    ),
    StageTestCase(
        "precedence_index_dollar_precedes_preserve_type",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "$idx",
                    "preserveNullAndEmptyArrays": "invalid",
                }
            }
        ],
        error_code=UNWIND_INCLUDE_ARRAY_INDEX_DOLLAR_PREFIX_ERROR,
        msg=(
            "includeArrayIndex dollar prefix error should fire before"
            " preserveNullAndEmptyArrays type error"
        ),
    ),
    StageTestCase(
        "precedence_path_field_path_over_index_field_path",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": "$a..b", "includeArrayIndex": "x."}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg=(
            "path field path error should take precedence over"
            " includeArrayIndex field path error in phase 2"
        ),
    ),
    StageTestCase(
        "precedence_error_fires_on_empty_collection",
        docs=[],
        pipeline=[{"$unwind": {"path": 123}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="validation errors should fire on empty collections",
    ),
    StageTestCase(
        "precedence_error_fires_on_nonexistent_collection",
        docs=None,
        pipeline=[{"$unwind": {"path": 123}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="validation errors should fire on non-existent collections",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_ERROR_PRECEDENCE_TESTS))
def test_unwind_error_precedence(collection, test_case: StageTestCase):
    """Test $unwind error precedence."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
