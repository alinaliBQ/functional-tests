"""
Shared test infrastructure for $concatArrays expression tests.
"""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ConcatArraysTest(BaseTestCase):
    """Test case for $concatArrays operator."""

    arrays: Any = None
