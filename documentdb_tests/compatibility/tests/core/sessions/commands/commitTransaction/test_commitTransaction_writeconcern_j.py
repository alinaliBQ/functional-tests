"""Tests for commitTransaction writeConcern.j sub-field validation.

Validates type acceptance for the writeConcern.j sub-field. j accepts boolean
and numeric values (which are coerced). String, object, and array types are
rejected with TypeMismatch. Null is accepted.
"""

from __future__ import annotations

import pytest

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


# Property [j Accepted Values]: j accepts boolean and numeric types.
J_ACCEPTANCE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "j_bool_true",
        command={"commitTransaction": 1, "writeConcern": {"j": True}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.j:true",
    ),
    SessionCommandTestCase(
        "j_bool_false",
        command={"commitTransaction": 1, "writeConcern": {"j": False}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.j:false",
    ),
    SessionCommandTestCase(
        "j_int32_one",
        command={"commitTransaction": 1, "writeConcern": {"j": 1}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.j:1 (coerced to true)",
    ),
    SessionCommandTestCase(
        "j_int32_zero",
        command={"commitTransaction": 1, "writeConcern": {"j": 0}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.j:0 (coerced to false)",
    ),
    SessionCommandTestCase(
        "j_null",
        command={"commitTransaction": 1, "writeConcern": {"j": None}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="commitTransaction should accept writeConcern.j:null",
    ),
]

# Property [j Type Rejection]: non-boolean non-numeric types are rejected with TypeMismatch.
J_TYPE_REJECTION_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "j_string",
        command={"commitTransaction": 1, "writeConcern": {"j": "true"}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern.j:'true' as wrong type",
    ),
    SessionCommandTestCase(
        "j_object",
        command={"commitTransaction": 1, "writeConcern": {"j": {}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern.j:{} as wrong type",
    ),
    SessionCommandTestCase(
        "j_array",
        command={"commitTransaction": 1, "writeConcern": {"j": []}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="commitTransaction should reject writeConcern.j:[] as wrong type",
    ),
]

J_TESTS: list[SessionCommandTestCase] = J_ACCEPTANCE_TESTS + J_TYPE_REJECTION_TESTS


@pytest.mark.parametrize("test", pytest_params(J_TESTS))
def test_commitTransaction_writeconcern_j(collection, test):
    """Test commitTransaction writeConcern.j sub-field validation."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
