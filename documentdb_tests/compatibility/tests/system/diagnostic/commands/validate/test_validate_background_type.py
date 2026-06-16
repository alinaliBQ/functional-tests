"""Tests for validate command 'background' parameter type coercion.

Validates that the background parameter accepts all BSON types via coercion.
Note: background: true is not supported on standalone mode, so truthy values
are tested with assertFailureCode for the standalone error.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Falsy Type Acceptance]: validate accepts falsy BSON types for the background parameter.
FALSY_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_false",
        checks={"ok": Eq(1.0)},
        msg="background should accept bool false",
    ),
    DiagnosticTestCase(
        "int32_0",
        checks={"ok": Eq(1.0)},
        msg="background should accept int32 0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "double_0",
        checks={"ok": Eq(1.0)},
        msg="background should accept double 0.0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "int64_0",
        checks={"ok": Eq(1.0)},
        msg="background should accept Int64(0) (coerces to false)",
    ),
    DiagnosticTestCase(
        "decimal128_0",
        checks={"ok": Eq(1.0)},
        msg="background should accept Decimal128('0') (coerces to false)",
    ),
    DiagnosticTestCase(
        "null",
        checks={"ok": Eq(1.0)},
        msg="background should accept null (treated as omitted/false)",
    ),
]

_FALSY_VALUES = {
    "bool_false": False,
    "int32_0": 0,
    "double_0": 0.0,
    "int64_0": Int64(0),
    "decimal128_0": Decimal128("0"),
    "null": None,
}


@pytest.mark.parametrize("test", pytest_params(FALSY_TYPE_TESTS))
def test_validate_background_falsy_types(collection, test):
    """Test that validate accepts falsy types for the background parameter."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, "background": _FALSY_VALUES[test.id]},
    )
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


# Property [Truthy Standalone Error]: validate rejects truthy background values on standalone mode.
TRUTHY_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_true",
        error_code=COMMAND_NOT_SUPPORTED_ERROR,
        msg="background: true not supported on standalone",
    ),
    DiagnosticTestCase(
        "int32_1",
        error_code=COMMAND_NOT_SUPPORTED_ERROR,
        msg="background: int 1 (truthy) not supported on standalone",
    ),
    DiagnosticTestCase(
        "string",
        error_code=COMMAND_NOT_SUPPORTED_ERROR,
        msg="background: string (truthy) not supported on standalone",
    ),
]

_TRUTHY_VALUES = {
    "bool_true": True,
    "int32_1": 1,
    "string": "true",
}


@pytest.mark.parametrize("test", pytest_params(TRUTHY_TYPE_TESTS))
def test_validate_background_truthy_standalone_error(collection, test):
    """Test that background with truthy values errors on standalone mode."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, "background": _TRUTHY_VALUES[test.id]},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)
