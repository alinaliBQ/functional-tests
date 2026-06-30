"""
Shared test case for array expression operator tests.

Used across the $arrayElemAt, $arrayToObject, and $concatArrays test files.
"""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ArrayTestClass(BaseTestCase):
    """Test case for array expression operators.

    Attributes:
        idx: An index argument (e.g. $arrayElemAt).
        arrays: The array input. Holds a single array for $arrayElemAt and
            $arrayToObject, or a list of arrays for $concatArrays.
    """

    idx: Any = None
    arrays: Any = None
