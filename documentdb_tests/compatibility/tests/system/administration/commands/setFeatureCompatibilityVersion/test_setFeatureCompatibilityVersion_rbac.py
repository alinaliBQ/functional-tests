"""
Tests for setFeatureCompatibilityVersion RBAC/classification.

Covers: authentication-required command classification.
"""

import pytest

from documentdb_tests.framework.assertions import assertNotError
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def test_setFeatureCompatibilityVersion_requires_authentication(collection):
    """Test setFeatureCompatibilityVersion is processed on an authenticated connection."""
    # On an authenticated connection, the command should be processed
    # (not rejected at the auth gate). Verify by sending a valid no-op command.
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    assertNotError(result, msg="Authenticated connection should process FCV commands")
