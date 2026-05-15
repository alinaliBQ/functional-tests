"""Shared test case for $max accumulator tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AccumulatorMaxTestCase(BaseTestCase):
    """Test case for $max accumulator."""

    docs: list[dict] | None = None
    accumulator: Any = None
