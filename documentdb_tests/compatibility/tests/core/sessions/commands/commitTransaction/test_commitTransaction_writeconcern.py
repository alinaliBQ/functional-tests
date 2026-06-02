"""Tests for commitTransaction writeConcern parameter type acceptance.

Validates that writeConcern must be a document. Document types (including
empty and null) are accepted and produce NoSuchTransaction (125). All
non-document types are rejected with TypeMismatch (14).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_command_test_case import (  # noqa: E501
    SessionCommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    NO_SUCH_TRANSACTION_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [writeConcern Document Acceptance]: writeConcern accepts document values.
WRITECONCERN_ACCEPTANCE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "writeconcern_doc_w1",
        command={"commitTransaction": 1, "writeConcern": {"w": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern document with w:1",
    ),
    SessionCommandTestCase(
        "writeconcern_empty_doc",
        command={"commitTransaction": 1, "writeConcern": {}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept empty writeConcern document",
    ),
    SessionCommandTestCase(
        "writeconcern_null",
        command={"commitTransaction": 1, "writeConcern": None},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern:null",
    ),
]

# Property [writeConcern Type Rejection]: non-document types are rejected with TypeMismatch.
WRITECONCERN_TYPE_REJECTION_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "writeconcern_string",
        command={"commitTransaction": 1, "writeConcern": "majority"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:string as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_int32",
        command={"commitTransaction": 1, "writeConcern": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:int32 as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_int64",
        command={"commitTransaction": 1, "writeConcern": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Int64 as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_double",
        command={"commitTransaction": 1, "writeConcern": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:double as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_decimal128",
        command={"commitTransaction": 1, "writeConcern": Decimal128("1")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Decimal128 as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_bool_true",
        command={"commitTransaction": 1, "writeConcern": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:true as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_bool_false",
        command={"commitTransaction": 1, "writeConcern": False},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:false as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_array_empty",
        command={"commitTransaction": 1, "writeConcern": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:[] as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_array_nonempty",
        command={"commitTransaction": 1, "writeConcern": [{"w": 1}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:[{w:1}] as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_binary",
        command={"commitTransaction": 1, "writeConcern": Binary(b"\x00")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Binary as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_objectid",
        command={"commitTransaction": 1, "writeConcern": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:ObjectId as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_datetime",
        command={"commitTransaction": 1, "writeConcern": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:datetime as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_regex",
        command={"commitTransaction": 1, "writeConcern": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Regex as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_timestamp",
        command={"commitTransaction": 1, "writeConcern": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Timestamp as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_code",
        command={"commitTransaction": 1, "writeConcern": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:Code as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_minkey",
        command={"commitTransaction": 1, "writeConcern": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:MinKey as wrong type",
    ),
    SessionCommandTestCase(
        "writeconcern_maxkey",
        command={"commitTransaction": 1, "writeConcern": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern:MaxKey as wrong type",
    ),
]

WRITECONCERN_TESTS: list[SessionCommandTestCase] = (
    WRITECONCERN_ACCEPTANCE_TESTS + WRITECONCERN_TYPE_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(WRITECONCERN_TESTS))
def test_commitTransaction_writeconcern(collection, test):
    """Test commitTransaction writeConcern parameter type acceptance."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
