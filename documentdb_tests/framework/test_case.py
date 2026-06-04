from dataclasses import dataclass, field
from typing import Any, Optional, Union


@dataclass(frozen=True)
class BaseTestCase:
    """Base dataclass for all parametrized test cases.

    Sub-classes must include `@dataclass(frozen=True)`.

    Attributes:
        id: Unique identifier for the test case
        expected: Expected result value (None for error cases)
        error_code: Expected error code (None for success cases).
            May be a single int or a list of ints when the server returns
            different codes depending on topology (e.g. standalone vs
            replica set).
        msg: Description of expected behavior for assertion messages (required)
    """

    id: str
    expected: Any = None
    error_code: Union[int, list[int], None] = None
    msg: Optional[str] = None
    marks: tuple = field(default=())

    def __post_init__(self):
        if self.msg is None:
            raise ValueError(
                f"BaseTestCase '{self.id}' must have a msg describing expected behavior"
            )
