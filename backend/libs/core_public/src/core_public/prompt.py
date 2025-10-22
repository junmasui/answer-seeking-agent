import enum
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from pydantic import Field

from core_public import OwnerType

from .base import CamelModel


class Prompt(CamelModel):
    """
    Represents an LLM prompt.

    The data includes its name, status, messages, and version.
    """

    id: Annotated[UUID, Field(description='ID of the prompt.')]
    name: Annotated[str, Field(description='Name of prompt.')]
    owner_type: Annotated[OwnerType, Field(description='Record owner type')]


class PromptStats(CamelModel):
    """
    Provides statistics about LLM prompts.

    The statistics include the total count and last update time.
    """

    prompt_count: Annotated[Optional[int], Field(description='Total number of prompts.', default=None)]
    table_updated_time: Annotated[
        Optional[datetime], Field(description='Last time the prompt table was updated.', default=None)
    ]


#
#
#


class PromptList(CamelModel):
    """
    Represents a list of agent prompts.

    Addtional information include an optional count and update time information.
    """

    prompts: Annotated[list[Prompt], Field(description='List of prompts.')]
    prompt_count: Annotated[Optional[int], Field(description='Total number of prompts.', default=None)]
    table_updated_time: Annotated[
        Optional[datetime], Field(description='Last time the prompt table was updated.', default=None)
    ]


#
# Operator Models
#


class PromptAddRequest(CamelModel):
    """Represents a request to add a new agent prompt."""

    name: Annotated[str, Field(description='Name of prompt.')]


class PromptUpdateRequest(CamelModel):
    """Represents a request to update an existing agent prompt."""

    name: Annotated[Optional[str], Field(description='Name of prompt.', default=None)]
