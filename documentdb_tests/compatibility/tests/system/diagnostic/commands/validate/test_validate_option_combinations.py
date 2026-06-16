"""Tests for validate command option combinations and error conditions.

Validates valid and invalid option combinations, repair/fixMultikey specifics,
and unrecognized field handling.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Valid Combinations]: validate succeeds with valid option combinations.
VALID_COMBINATION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "minimal_command",
        checks={"ok": Eq(1.0)},
        msg="Minimal validate command should succeed",
    ),
    DiagnosticTestCase(
        "all_defaults_explicit",
        checks={"ok": Eq(1.0)},
        msg="All options set to false explicitly should succeed",
    ),
    DiagnosticTestCase(
        "full_true",
        checks={"ok": Eq(1.0)},
        msg="validate with full: true should succeed",
    ),
    DiagnosticTestCase(
        "checkBSONConformance_true",
        checks={"ok": Eq(1.0)},
        msg="validate with checkBSONConformance: true should succeed",
    ),
    DiagnosticTestCase(
        "full_and_checkBSONConformance",
        checks={"ok": Eq(1.0)},
        msg="validate with full: true and checkBSONConformance: true should succeed",
    ),
    DiagnosticTestCase(
        "metadata_true",
        checks={"ok": Eq(1.0)},
        msg="validate with metadata: true should succeed",
    ),
    DiagnosticTestCase(
        "fixMultikey_true_alone",
        checks={"ok": Eq(1.0)},
        msg="validate with fixMultikey: true alone should succeed",
    ),
    DiagnosticTestCase(
        "repair_true_alone",
        checks={"ok": Eq(1.0)},
        msg="validate with repair: true alone should succeed",
    ),
    DiagnosticTestCase(
        "repair_true_with_fixMultikey",
        checks={"ok": Eq(1.0)},
        msg="validate with repair: true and fixMultikey: true should succeed",
    ),
    DiagnosticTestCase(
        "background_false",
        checks={"ok": Eq(1.0)},
        msg="validate with background: false should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_COMBINATION_TESTS))
def test_validate_valid_option_combinations(collection, test):
    """Test that validate succeeds with valid option combinations."""
    collection.insert_one({"_id": 1})
    commands = {
        "minimal_command": {"validate": collection.name},
        "all_defaults_explicit": {
            "validate": collection.name,
            "full": False,
            "repair": False,
            "metadata": False,
            "checkBSONConformance": False,
        },
        "full_true": {"validate": collection.name, "full": True},
        "checkBSONConformance_true": {
            "validate": collection.name,
            "checkBSONConformance": True,
        },
        "full_and_checkBSONConformance": {
            "validate": collection.name,
            "full": True,
            "checkBSONConformance": True,
        },
        "metadata_true": {"validate": collection.name, "metadata": True},
        "fixMultikey_true_alone": {"validate": collection.name, "fixMultikey": True},
        "repair_true_alone": {"validate": collection.name, "repair": True},
        "repair_true_with_fixMultikey": {
            "validate": collection.name,
            "repair": True,
            "fixMultikey": True,
        },
        "background_false": {"validate": collection.name, "background": False},
    }
    result = execute_command(collection, commands[test.id])
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


# Property [Invalid Combinations]: validate rejects incompatible option combinations.
INVALID_COMBINATION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "metadata_with_full",
        error_code=INVALID_OPTIONS_ERROR,
        msg="metadata: true with full: true should error",
    ),
    DiagnosticTestCase(
        "metadata_with_repair",
        error_code=INVALID_OPTIONS_ERROR,
        msg="metadata: true with repair: true should error",
    ),
    DiagnosticTestCase(
        "metadata_with_checkBSONConformance",
        error_code=INVALID_OPTIONS_ERROR,
        msg="metadata: true with checkBSONConformance: true should error",
    ),
    DiagnosticTestCase(
        "checkBSONConformance_with_repair",
        error_code=INVALID_OPTIONS_ERROR,
        msg="checkBSONConformance: true with repair: true should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_COMBINATION_TESTS))
def test_validate_invalid_option_combinations(collection, test):
    """Test that validate errors on invalid option combinations."""
    collection.insert_one({"_id": 1})
    commands = {
        "metadata_with_full": {
            "validate": collection.name,
            "metadata": True,
            "full": True,
        },
        "metadata_with_repair": {
            "validate": collection.name,
            "metadata": True,
            "repair": True,
            "fixMultikey": True,
        },
        "metadata_with_checkBSONConformance": {
            "validate": collection.name,
            "metadata": True,
            "checkBSONConformance": True,
        },
        "checkBSONConformance_with_repair": {
            "validate": collection.name,
            "checkBSONConformance": True,
            "repair": True,
            "fixMultikey": True,
        },
    }
    result = execute_command(collection, commands[test.id])
    assertFailureCode(result, test.error_code, msg=test.msg)
