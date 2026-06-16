"""Tests for validate command response structure.

Validates presence, types, and values of response fields for healthy collections.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Gte, IsType

# Property [Response Structure]: validate returns expected field types and values for
# healthy collections.
PROPERTY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "ok_is_1",
        checks={"ok": Eq(1.0)},
        msg="'ok' field should be 1.0",
    ),
    DiagnosticTestCase(
        "ns_is_string",
        checks={"ns": IsType("string")},
        msg="'ns' field should be a string",
    ),
    DiagnosticTestCase(
        "nInvalidDocuments_is_int",
        checks={"nInvalidDocuments": IsType("int")},
        msg="'nInvalidDocuments' field should be an int",
    ),
    DiagnosticTestCase(
        "nNonCompliantDocuments_is_int",
        checks={"nNonCompliantDocuments": IsType("int")},
        msg="'nNonCompliantDocuments' field should be an int",
    ),
    DiagnosticTestCase(
        "nrecords_is_int",
        checks={"nrecords": IsType("int")},
        msg="'nrecords' field should be an int",
    ),
    DiagnosticTestCase(
        "nIndexes_is_int",
        checks={"nIndexes": IsType("int")},
        msg="'nIndexes' field should be an int",
    ),
    DiagnosticTestCase(
        "keysPerIndex_is_object",
        checks={"keysPerIndex": IsType("object")},
        msg="'keysPerIndex' field should be an object",
    ),
    DiagnosticTestCase(
        "indexDetails_is_object",
        checks={"indexDetails": IsType("object")},
        msg="'indexDetails' field should be an object",
    ),
    DiagnosticTestCase(
        "valid_is_bool",
        checks={"valid": IsType("bool")},
        msg="'valid' field should be a bool",
    ),
    DiagnosticTestCase(
        "repaired_is_bool",
        checks={"repaired": IsType("bool")},
        msg="'repaired' field should be a bool",
    ),
    DiagnosticTestCase(
        "warnings_is_array",
        checks={"warnings": IsType("array")},
        msg="'warnings' field should be an array",
    ),
    DiagnosticTestCase(
        "errors_is_array",
        checks={"errors": IsType("array")},
        msg="'errors' field should be an array",
    ),
    DiagnosticTestCase(
        "extraIndexEntries_is_array",
        checks={"extraIndexEntries": IsType("array")},
        msg="'extraIndexEntries' field should be an array",
    ),
    DiagnosticTestCase(
        "missingIndexEntries_is_array",
        checks={"missingIndexEntries": IsType("array")},
        msg="'missingIndexEntries' field should be an array",
    ),
    DiagnosticTestCase(
        "corruptRecords_is_array",
        checks={"corruptRecords": IsType("array")},
        msg="'corruptRecords' field should be an array",
    ),
    DiagnosticTestCase(
        "uuid_exists",
        checks={"uuid": Exists()},
        msg="'uuid' field should exist (since 6.2)",
    ),
    DiagnosticTestCase(
        "nInvalidDocuments_zero_healthy",
        checks={"nInvalidDocuments": Eq(0)},
        msg="'nInvalidDocuments' should be 0 for a healthy collection",
    ),
    DiagnosticTestCase(
        "nNonCompliantDocuments_zero_healthy",
        checks={"nNonCompliantDocuments": Eq(0)},
        msg="'nNonCompliantDocuments' should be 0 for a healthy collection",
    ),
    DiagnosticTestCase(
        "valid_true_healthy",
        checks={"valid": Eq(True)},
        msg="'valid' should be true for a healthy collection",
    ),
    DiagnosticTestCase(
        "repaired_false_no_repair",
        checks={"repaired": Eq(False)},
        msg="'repaired' should be false when no repair requested",
    ),
    DiagnosticTestCase(
        "warnings_empty_healthy",
        checks={"warnings": Eq([])},
        msg="'warnings' should be empty for a healthy collection",
    ),
    DiagnosticTestCase(
        "errors_empty_healthy",
        checks={"errors": Eq([])},
        msg="'errors' should be empty for a healthy collection",
    ),
    DiagnosticTestCase(
        "extraIndexEntries_empty_healthy",
        checks={"extraIndexEntries": Eq([])},
        msg="'extraIndexEntries' should be empty for a healthy collection",
    ),
    DiagnosticTestCase(
        "missingIndexEntries_empty_healthy",
        checks={"missingIndexEntries": Eq([])},
        msg="'missingIndexEntries' should be empty for a healthy collection",
    ),
    DiagnosticTestCase(
        "corruptRecords_empty_healthy",
        checks={"corruptRecords": Eq([])},
        msg="'corruptRecords' should be empty for a healthy collection",
    ),
    DiagnosticTestCase(
        "nIndexes_gte_1",
        checks={"nIndexes": Gte(1)},
        msg="'nIndexes' should be >= 1 (at least _id index)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_TESTS))
def test_validate_response_properties(collection, test):
    """Test validate response fields have expected types and values."""
    collection.insert_many([{"_id": i, "x": i} for i in range(5)])
    result = execute_command(collection, {"validate": collection.name})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_validate_ns_matches_namespace(collection):
    """Test validate ns field matches the actual database.collection namespace."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"validate": collection.name})
    expected_ns = f"{collection.database.name}.{collection.name}"
    assertSuccessPartial(result, {"ns": expected_ns}, msg="ns should match actual namespace")


def test_validate_nrecords_matches_count(collection):
    """Test validate nrecords matches the number of inserted documents."""
    collection.insert_many([{"_id": i} for i in range(10)])
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(result, {"nrecords": 10}, msg="nrecords should match document count")


def test_validate_nIndexes_with_secondary(collection):
    """Test validate nIndexes includes secondary indexes."""
    collection.insert_one({"_id": 1, "x": 1, "y": 1})
    collection.create_index("x")
    collection.create_index("y")
    result = execute_command(collection, {"validate": collection.name})
    assertSuccessPartial(result, {"nIndexes": 3}, msg="nIndexes should be 3 (_id + x + y)")
