from typing import Optional
from uuid import UUID
from datetime import datetime
import enum

from pydantic import Field

from .base import CamelModel

class AgentPromptStatus(str, enum.Enum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"

class AgentPrompt(CamelModel):
    id: UUID
    name: str = Field(
        description="Name of prompt.",
    )
    status: AgentPromptStatus = Field(
        description="Status.",
    )
    system_prompt: str = Field(
        description='Prompt'
    )
    human_prompt: str = Field(
        description='Prompt'
    )
    version: int = Field(
        description = 'Version number of prompt.'
    )

class AgentPromptStats(CamelModel):
    prompt_count: int = None
    table_updated_time: Optional[datetime] = None

#
#
#

class AgentPromptList(CamelModel):
    prompts: list[AgentPrompt]
    prompt_count: Optional[int] = None
    table_updated_time: Optional[datetime] = None


#
# Operator Models
#

class AgentPromptAddRequest(CamelModel):
    name: str = Field(
        description="Name of prompt.",
    )
    system_prompt: str = Field(
        description='Prompt'
    )
    human_prompt: str = Field(
        description='Prompt'
    )

class AgentPromptUpdateRequest(CamelModel):
    name: Optional[str] = Field(
        description="Name of prompt.",
        default = None
    )
    system_prompt: str = Field(
        description='Prompt'
    )
    human_prompt: str = Field(
        description='Prompt'
    )
