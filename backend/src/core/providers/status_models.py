import enum
from typing import Annotated, Dict, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class PingStatus(str, enum.Enum):
    """Represents the status of a ping attempt."""

    GOOD = 'good'
    BAD = 'bad'


class PingResult(BaseModel):
    """Represents the result of a ping operation."""

    model_config = ConfigDict(extra='forbid', arbitrary_types_allowed=True)

    status: Annotated[PingStatus, Field(description='The status of the ping attempt.')]
    message: Annotated[str, Field(description='A message describing the ping result.')]
    statistics: Annotated[
        Optional[Dict[str, Union[int, float]]],
        Field(default=None, description='Optional statistics about the ping attempt.'),
    ]
    error: Annotated[
        Optional[Exception], Field(default=None, description='An optional exception if an error occurred.')
    ]
