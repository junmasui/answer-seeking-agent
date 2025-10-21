import enum
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from pydantic import Field

from .base import CamelModel


class PromptStatus(enum.StrEnum):
    """
    Defines the lifecycle status of LLM prompt templates.

    Controls whether a prompt version is currently active for use or has been deactivated in favor
    of a newer version.
    """

    ACTIVE = 'active'
    DEACTIVATED = 'deactivated'


class PromptVersion(CamelModel):
    """
    Represents an LLM prompt.

    The data includes its name, status, messages, and version.
    """

    id: Annotated[UUID, Field(description='ID of the prompt version.')]
    prompt_id: Annotated[UUID, Field(description='ID of prompt.')]
    prompt_name: Annotated[str, Field(description='Name of prompt.')]
    status: Annotated[PromptStatus, Field(description='Status.')]
    include_history: Annotated[Optional[bool], Field(description='Include chat history')]
    system_message: Annotated[Optional[str], Field(description='Prompt')]
    human_message: Annotated[Optional[str], Field(description='Prompt')]
    version: Annotated[int, Field(description='Version number of prompt.')]


class PromptVersionStats(CamelModel):
    """
    Provides statistics about LLM prompts.

    The statistics include the total count and last update time.
    """

    prompt_version_count: Annotated[
        Optional[int], Field(description='Total number of prompt versions.', default=None)
    ]
    table_updated_time: Annotated[
        Optional[datetime], Field(description='Last time the prompt version table was updated.', default=None)
    ]


#
#
#


class PromptVersionList(CamelModel):
    """
    Represents a list of agent prompts.

    Addtional information include an optional count and update time information.
    """

    prompt_versions: Annotated[list[PromptVersion], Field(description='List of prompt versions.')]
    prompt_version_count: Annotated[
        Optional[int], Field(description='Total number of prompt versions.', default=None)
    ]
    table_updated_time: Annotated[
        Optional[datetime], Field(description='Last time the prompt version table was updated.', default=None)
    ]


#
# Operator Models
#


class PromptVersionAddRequest(CamelModel):
    """Represents a request to add a new prompt version."""

    status: Annotated[Optional[PromptStatus], Field(description='Status.', default=None)]
    include_history: Annotated[bool, Field(description='Include chat history')]
    system_message: Annotated[str, Field(description='Prompt')]
    human_message: Annotated[str, Field(description='Prompt')]


class PromptVersionUpdateRequest(CamelModel):
    """Represents a request to update an existing prompt version."""

    version: Annotated[Optional[int], Field(description='Version number of prompt.', default=None)]

    status: Annotated[Optional[PromptStatus], Field(description='Status.', default=None)]
    include_history: Annotated[Optional[bool], Field(description='Include chat history', default=None)]
    system_message: Annotated[Optional[str], Field(description='Prompt', default=None)]
    human_message: Annotated[Optional[str], Field(description='Prompt', default=None)]
