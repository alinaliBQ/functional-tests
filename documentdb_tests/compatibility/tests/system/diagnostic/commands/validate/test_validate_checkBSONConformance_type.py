"""Tests for validate command 'checkBSONConformance' parameter type coercion.

Validates that the checkBSONConformance parameter accepts all BSON types via
coercion.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Type Coercion]: validate accepts all BSON types for the
# checkBSONConformance parameter via coercion.
ACCEPTED_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_true",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept bool true",
    ),
    DiagnosticTestCase(
        "bool_false",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept bool false",
    ),
    DiagnosticTestCase(
        "int32_1",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept int32 1 (coerces to true)",
    ),
    DiagnosticTestCase(
        "int32_0",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept int32 0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "double_1",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept double 1.0 (coerces to true)",
    ),
    DiagnosticTestCase(
        "double_0",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept double 0.0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "int64_1",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept Int64(1) (coerces to true)",
    ),
    DiagnosticTestCase(
        "int64_0",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept Int64(0) (coerces to false)",
    ),
    DiagnosticTestCase(
        "decimal128_1",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept Decimal128('1') (coerces to true)",
    ),
    DiagnosticTestCase(
        "decimal128_0",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept Decimal128('0') (coerces to false)",
    ),
    DiagnosticTestCase(
        "null",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept null (treated as omitted/false)",
    ),
    DiagnosticTestCase(
        "string",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept string (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "object",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept object (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "array",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept array (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "binary",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept Binary (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "objectid",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept ObjectId (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "datetime",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept datetime (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "regex",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept Regex (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "timestamp",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept Timestamp (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "code",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept JavaScript Code (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "minkey",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept MinKey (coerces to truthy)",
    ),
    DiagnosticTestCase(
        "maxkey",
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept MaxKey (coerces to truthy)",
    ),
]

_VALUES = {
    "bool_true": True,
    "bool_false": False,
    "int32_1": 1,
    "int32_0": 0,
    "double_1": 1.0,
    "double_0": 0.0,
    "int64_1": Int64(1),
    "int64_0": Int64(0),
    "decimal128_1": Decimal128("1"),
    "decimal128_0": Decimal128("0"),
    "null": None,
    "string": "true",
    "object": {},
    "array": [],
    "binary": Binary(b""),
    "objectid": ObjectId(),
    "datetime": datetime(2024, 1, 1, tzinfo=timezone.utc),
    "regex": Regex(".*"),
    "timestamp": Timestamp(0, 0),
    "code": Code("function(){}"),
    "minkey": MinKey(),
    "maxkey": MaxKey(),
}


@pytest.mark.parametrize("test", pytest_params(ACCEPTED_TYPE_TESTS))
def test_validate_checkBSONConformance_accepted_types(collection, test):
    """Test that validate accepts all BSON types for checkBSONConformance."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, "checkBSONConformance": _VALUES[test.id]},
    )
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
