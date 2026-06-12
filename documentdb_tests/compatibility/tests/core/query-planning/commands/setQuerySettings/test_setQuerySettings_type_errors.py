"""Tests for setQuerySettings command BSON type rejection.

Validates that the setQuerySettings command rejects invalid BSON types for
the primary argument field, the queryFramework sub-field, the reject sub-field,
and the indexHints namespace and allowedIndexes sub-fields.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from pymongo.collection import Collection

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command

# Property [Primary Argument Type Rejection]: the setQuerySettings field must
# be a document (query shape) or string (hash). All other BSON types are
# rejected with TYPE_MISMATCH_ERROR.
_PRIMARY_ARG_INVALID_TYPES: list[tuple[str, Any]] = [
    ("null", None),
    ("int32", 42),
    ("int64", Int64(42)),
    ("double", 3.14),
    ("decimal128", Decimal128("1")),
    ("bool_true", True),
    ("bool_false", False),
    ("array", [1, 2, 3]),
    ("objectid", ObjectId()),
    ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ("timestamp", Timestamp(0, 0)),
    ("binary", Binary(b"\x00")),
    ("regex", Regex(".*")),
    ("code", Code("function(){}")),
    ("minkey", MinKey()),
    ("maxkey", MaxKey()),
]

# Property [queryFramework Type Rejection]: the queryFramework field must be a
# string. Non-string BSON types are rejected with TYPE_MISMATCH_ERROR.
_QUERY_FRAMEWORK_INVALID_TYPES: list[tuple[str, Any]] = [
    ("int32", 42),
    ("int64", Int64(42)),
    ("double", 3.14),
    ("decimal128", Decimal128("1")),
    ("bool_true", True),
    ("bool_false", False),
    ("array", [1]),
    ("object", {"k": "v"}),
    ("objectid", ObjectId()),
    ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ("timestamp", Timestamp(0, 0)),
    ("binary", Binary(b"\x00")),
    ("regex", Regex(".*")),
    ("code", Code("function(){}")),
    ("minkey", MinKey()),
    ("maxkey", MaxKey()),
]

# Property [reject Type Rejection]: the reject field must be a boolean.
# Non-boolean BSON types are rejected with TYPE_MISMATCH_ERROR.
_REJECT_INVALID_TYPES: list[tuple[str, Any]] = [
    ("null", None),
    ("int32", 42),
    ("int64", Int64(42)),
    ("double", 3.14),
    ("decimal128", Decimal128("1")),
    ("string", "true"),
    ("array", [True]),
    ("object", {"k": "v"}),
    ("objectid", ObjectId()),
    ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ("timestamp", Timestamp(0, 0)),
    ("binary", Binary(b"\x00")),
    ("regex", Regex(".*")),
    ("code", Code("function(){}")),
    ("minkey", MinKey()),
    ("maxkey", MaxKey()),
]

# Property [indexHints.ns.db Type Rejection]: the ns.db field must be a string.
_NS_DB_INVALID_TYPES: list[tuple[str, Any]] = [
    ("int32", 42),
    ("bool", True),
    ("array", ["test"]),
    ("object", {"k": "v"}),
]

# Property [indexHints.ns.coll Type Rejection]: the ns.coll field must be a string.
_NS_COLL_INVALID_TYPES: list[tuple[str, Any]] = [
    ("int32", 42),
    ("bool", True),
]

# Property [indexHints.allowedIndexes Type Rejection]: allowedIndexes must be an array.
_ALLOWED_INDEXES_INVALID_TYPES: list[tuple[str, Any]] = [
    ("string", "_id_"),
    ("int32", 42),
]


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize(
    "tid, value",
    _PRIMARY_ARG_INVALID_TYPES,
    ids=[t[0] for t in _PRIMARY_ARG_INVALID_TYPES],
)
def test_setQuerySettings_primary_arg_type_rejection(collection: Collection, tid: str, value: Any):
    """Test setQuerySettings rejects invalid BSON types for the primary argument."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": value,
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as the primary argument",
    )


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize(
    "tid, value",
    _QUERY_FRAMEWORK_INVALID_TYPES,
    ids=[t[0] for t in _QUERY_FRAMEWORK_INVALID_TYPES],
)
def test_setQuerySettings_query_framework_type_rejection(
    collection: Collection, tid: str, value: Any
):
    """Test setQuerySettings rejects invalid BSON types for queryFramework."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "queryFramework": value,
            },
        },
    )
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as queryFramework",
    )


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize(
    "tid, value",
    _REJECT_INVALID_TYPES,
    ids=[t[0] for t in _REJECT_INVALID_TYPES],
)
def test_setQuerySettings_reject_type_rejection(collection: Collection, tid: str, value: Any):
    """Test setQuerySettings rejects invalid BSON types for reject field."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "reject": value,
            },
        },
    )
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as reject field",
    )


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize(
    "tid, value",
    _NS_DB_INVALID_TYPES,
    ids=[t[0] for t in _NS_DB_INVALID_TYPES],
)
def test_setQuerySettings_ns_db_type_rejection(collection: Collection, tid: str, value: Any):
    """Test setQuerySettings rejects invalid BSON types for indexHints.ns.db."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": value, "coll": collection.name},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as indexHints.ns.db",
    )


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize(
    "tid, value",
    _NS_COLL_INVALID_TYPES,
    ids=[t[0] for t in _NS_COLL_INVALID_TYPES],
)
def test_setQuerySettings_ns_coll_type_rejection(collection: Collection, tid: str, value: Any):
    """Test setQuerySettings rejects invalid BSON types for indexHints.ns.coll."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": value},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as indexHints.ns.coll",
    )


@pytest.mark.admin
@pytest.mark.replica_set
@pytest.mark.parametrize(
    "tid, value",
    _ALLOWED_INDEXES_INVALID_TYPES,
    ids=[t[0] for t in _ALLOWED_INDEXES_INVALID_TYPES],
)
def test_setQuerySettings_allowed_indexes_type_rejection(
    collection: Collection, tid: str, value: Any
):
    """Test setQuerySettings rejects invalid BSON types for indexHints.allowedIndexes."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": value,
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as indexHints.allowedIndexes",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_allowed_indexes_null_missing(collection: Collection):
    """Test setQuerySettings rejects null allowedIndexes as missing required field."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": None,
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=MISSING_FIELD_ERROR,
        msg="setQuerySettings should reject null allowedIndexes as missing field",
    )


@pytest.mark.admin
@pytest.mark.replica_set
def test_setQuerySettings_allowed_indexes_non_string_element(collection: Collection):
    """Test setQuerySettings rejects non-string elements in allowedIndexes array."""
    result = execute_admin_command(
        collection,
        {
            "setQuerySettings": {
                "find": collection.name,
                "filter": {"x": 1},
                "$db": collection.database.name,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": collection.database.name, "coll": collection.name},
                        "allowedIndexes": [42],
                    }
                ],
            },
        },
    )
    assertResult(
        result,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="setQuerySettings should reject non-string elements in allowedIndexes",
    )
