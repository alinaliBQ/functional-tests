"""
Shared test infrastructure for $arrayElemAt expression tests.

Provides the ArrayElemAtTest dataclass and common imports used across
all $arrayElemAt test files.
"""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ArrayElemAtTest(BaseTestCase):
    """Test case for $arrayElemAt operator."""

    array: Any = None
    idx: Any = None
