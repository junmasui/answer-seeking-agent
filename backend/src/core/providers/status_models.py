import enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class PingStatus(str, enum.Enum):
    """Represents the status of a ping attempt."""

    GOOD = 'good'
    BAD = 'bad'


class PingResult(BaseModel):
    """Represents the result of a ping operation."""

    class Config:
        arbitrary_types_allowed = True  # To allow Exception types if we revert error to Exception

    status: Annotated[PingStatus, Field(description='The status of the ping attempt.')]
    message: Annotated[str, Field(description='A message describing the ping result.')]
    error: Annotated[
        Optional[Exception], Field(default=None, description='An optional exception if an error occurred.')
    ]
