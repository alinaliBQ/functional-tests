"""
Shared test infrastructure for $arrayToObject expression tests.
"""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ArrayToObjectTest(BaseTestCase):
    """Test case for $arrayToObject operator."""

    array: Any = None
