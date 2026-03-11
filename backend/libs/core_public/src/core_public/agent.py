from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import CamelModel

#
# Domain Models
#


class Citation(CamelModel):
    """
    Represents a citation for a document.

    The data includes its source and specific location.
    """

    doc_uuid: UUID = Field(description='Document UUID.')
    source_url: str = Field(description='URL of source document.')
    text: str = Field(description='Citation text.')
    file_name: Optional[str] = Field(default=None, description='File name of source document.')
    page_number: Optional[int] = Field(default=None, description='Page number of text within source document.')


class AgentResponse(CamelModel):
    """
    Represents a response from an agent.

    The data includes the input, response, citations, and conversation context.
    """

    input: str = Field(description="User's input.")
    response: str = Field(description="Response to the user's input with citations.")
    citations: list[Citation] = Field(description='List of citations.')
    thread_id: UUID = Field(description='Conversation UUID. A conversation is a sequence of inputs and responses.')
    user_id: Optional[UUID] = Field(default=None, description='User UUID associated with this input and response.')


#
# Operator Models
#
class AgentRequestBody(CamelModel):
    """
    Represents the request body for seeking a response.

    The body includes the user's input and optional conversation thread ID.
    """

    input: str
    thread_id: Optional[UUID] = Field(
        default=None, description='Conversation UUID. A conversation is a sequence of inputs and responses.'
    )
