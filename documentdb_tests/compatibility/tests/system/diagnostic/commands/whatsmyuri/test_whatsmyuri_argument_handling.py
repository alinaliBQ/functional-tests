"""Tests for whatsmyuri command argument handling.

Validates that whatsmyuri accepts any BSON type as its argument value.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


ARGUMENT_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "int_1", command={"whatsmyuri": 1}, checks={"ok": Eq(1.0)}, msg="Should accept int 1"
    ),
    DiagnosticTestCase(
        "int_0", command={"whatsmyuri": 0}, checks={"ok": Eq(1.0)}, msg="Should accept int 0"
    ),
    DiagnosticTestCase(
        "int_neg1", command={"whatsmyuri": -1}, checks={"ok": Eq(1.0)}, msg="Should accept int -1"
    ),
    DiagnosticTestCase(
        "bool_true", command={"whatsmyuri": True}, checks={"ok": Eq(1.0)}, msg="Should accept true"
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"whatsmyuri": False},
        checks={"ok": Eq(1.0)},
        msg="Should accept false",
    ),
    DiagnosticTestCase(
        "string",
        command={"whatsmyuri": "hello"},
        checks={"ok": Eq(1.0)},
        msg="Should accept string",
    ),
    DiagnosticTestCase(
        "null", command={"whatsmyuri": None}, checks={"ok": Eq(1.0)}, msg="Should accept null"
    ),
    DiagnosticTestCase(
        "empty_object",
        command={"whatsmyuri": {}},
        checks={"ok": Eq(1.0)},
        msg="Should accept empty object",
    ),
    DiagnosticTestCase(
        "empty_array",
        command={"whatsmyuri": []},
        checks={"ok": Eq(1.0)},
        msg="Should accept empty array",
    ),
    DiagnosticTestCase(
        "double", command={"whatsmyuri": 1.5}, checks={"ok": Eq(1.0)}, msg="Should accept double"
    ),
    DiagnosticTestCase(
        "int64",
        command={"whatsmyuri": Int64(1)},
        checks={"ok": Eq(1.0)},
        msg="Should accept int64",
    ),
    DiagnosticTestCase(
        "decimal128",
        command={"whatsmyuri": Decimal128("1")},
        checks={"ok": Eq(1.0)},
        msg="Should accept decimal128",
    ),
    DiagnosticTestCase(
        "decimal128_nan",
        command={"whatsmyuri": Decimal128("NaN")},
        checks={"ok": Eq(1.0)},
        msg="Should accept decimal128 NaN",
    ),
    DiagnosticTestCase(
        "infinity",
        command={"whatsmyuri": float("inf")},
        checks={"ok": Eq(1.0)},
        msg="Should accept infinity",
    ),
    DiagnosticTestCase(
        "date",
        command={"whatsmyuri": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        checks={"ok": Eq(1.0)},
        msg="Should accept date",
    ),
    DiagnosticTestCase(
        "binData",
        command={"whatsmyuri": Binary(b"")},
        checks={"ok": Eq(1.0)},
        msg="Should accept binData",
    ),
    DiagnosticTestCase(
        "objectId",
        command={"whatsmyuri": ObjectId()},
        checks={"ok": Eq(1.0)},
        msg="Should accept objectId",
    ),
    DiagnosticTestCase(
        "regex",
        command={"whatsmyuri": Regex("test")},
        checks={"ok": Eq(1.0)},
        msg="Should accept regex",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"whatsmyuri": Timestamp(0, 0)},
        checks={"ok": Eq(1.0)},
        msg="Should accept timestamp",
    ),
    DiagnosticTestCase(
        "minKey",
        command={"whatsmyuri": MinKey()},
        checks={"ok": Eq(1.0)},
        msg="Should accept minKey",
    ),
    DiagnosticTestCase(
        "maxKey",
        command={"whatsmyuri": MaxKey()},
        checks={"ok": Eq(1.0)},
        msg="Should accept maxKey",
    ),
    DiagnosticTestCase(
        "code",
        command={"whatsmyuri": Code("function(){}")},
        checks={"ok": Eq(1.0)},
        msg="Should accept JavaScript code",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_TYPE_TESTS))
def test_whatsmyuri_argument_types(collection, test):
    """Test that whatsmyuri accepts various BSON types as argument value."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
