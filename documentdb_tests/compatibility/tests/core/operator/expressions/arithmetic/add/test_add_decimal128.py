"""Tests for $add Decimal128 precision and special representations."""

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import DECIMAL128_MAX


@dataclass(frozen=True)
class AddTest(BaseTestCase):
    """Test case for $add operator."""

    args: Any = None


DECIMAL128_PRECISION_TESTS: list[AddTest] = [
    AddTest(
        "max_plus_small",
        args=[DECIMAL128_MAX, Decimal128("1")],
        expected=DECIMAL128_MAX,
        msg="Should absorb small value at max precision",
    ),
    AddTest(
        "high_precision",
        args=[
            Decimal128("1.234567890123456789012345678901234"),
            Decimal128("0.000000000000000000000000000000001"),
        ],
        expected=Decimal128("1.234567890123456789012345678901235"),
        msg="Should add high precision values correctly",
    ),
    AddTest(
        "trailing_zero_preserved",
        args=[Decimal128("1.0"), Decimal128("0")],
        expected=Decimal128("1.0"),
        msg="Should preserve trailing zero",
    ),
    AddTest(
        "many_trailing_zeros",
        args=[Decimal128("1.00000000000000000000000000000000"), Decimal128("0")],
        expected=Decimal128("1.00000000000000000000000000000000"),
        msg="Should preserve many trailing zeros",
    ),
    AddTest(
        "different_exponents",
        args=[Decimal128("1E+10"), Decimal128("1E-10")],
        expected=Decimal128("10000000000.0000000001"),
        msg="Should handle different exponents",
    ),
    AddTest(
        "max_coefficient_plus_1",
        args=[Decimal128("9999999999999999999999999999999999"), Decimal128("1")],
        expected=Decimal128("1.000000000000000000000000000000000E+34"),
        msg="Should handle max coefficient overflow",
    ),
    AddTest(
        "trailing_zero_add",
        args=[Decimal128("1.0"), Decimal128("2.0")],
        expected=Decimal128("3.0"),
        msg="Should preserve trailing zero in addition",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DECIMAL128_PRECISION_TESTS))
def test_add_decimal128_precision(collection, test):
    """Test $add Decimal128 precision handling."""
    result = execute_expression(collection, {"$add": test.args})
    assert_expression_result(result, expected=test.expected, msg=test.msg)
