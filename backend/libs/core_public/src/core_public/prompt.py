import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from core_public import OwnerType

from .base import CamelModel


class AgentPromptStatus(enum.StrEnum):
    """
    Defines the lifecycle status of agent prompt templates.

    Controls whether a prompt version is currently active for use or has been deactivated in favor
    of a newer version.
    """

    ACTIVE = 'active'
    DEACTIVATED = 'deactivated'


class AgentPrompt(CamelModel):
    """
    Represents an agent prompt.

    The data includes its name, status, messages, and version.
    """

    id: UUID
    name: str = Field(description='Name of prompt.')
    status: AgentPromptStatus = Field(description='Status.')
    system_message: Optional[str] = Field(description='Prompt')
    human_message: Optional[str] = Field(description='Prompt')
    include_history: Optional[bool] = Field(description='Include chat history')
    owner_type: OwnerType = Field(description='Record owner type')
    version: int = Field(description='Version number of prompt.')


class AgentPromptStats(CamelModel):
    """
    Provides statistics about agent prompts.

    The statistics include the total count and last update time.
    """

    prompt_count: int = None
    table_updated_time: Optional[datetime] = None


#
#
#


class AgentPromptList(CamelModel):
    """
    Represents a list of agent prompts.

    Addtional information include an optional count and update time information.
    """

    prompts: list[AgentPrompt]
    prompt_count: Optional[int] = None
    table_updated_time: Optional[datetime] = None


#
# Operator Models
#


class AgentPromptAddRequest(CamelModel):
    """Represents a request to add a new agent prompt."""

    name: str = Field(description='Name of prompt.')
    system_message: str = Field(description='Prompt')
    human_message: str = Field(description='Prompt')
    include_history: bool = Field(description='Include chat history')


class AgentPromptUpdateRequest(CamelModel):
    """Represents a request to update an existing agent prompt."""

    name: Optional[str] = Field(description='Name of prompt.', default=None)
    system_message: str = Field(description='Prompt')
    human_message: str = Field(description='Prompt')
    include_history: bool = Field(description='Include chat history')
