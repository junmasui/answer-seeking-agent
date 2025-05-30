from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import CamelModel

#
# Domain Models
#


class Citation(CamelModel):
    """
    Represents a citation for a document, including its source and
    specific location.
    """

    doc_uuid: UUID = Field(description='Document UUID.')
    source_url: str = Field(description='URL of source document.')
    text: str = Field(description='Citation text.')
    file_name: Optional[str] = Field(default=None, description='File name of source document.')
    page_number: Optional[int] = Field(default=None, description='Page number of text within source document.')


class Answer(CamelModel):
    """
    Represents an answer to a user's question, including the question, answer, citations,
    and conversation context.
    """

    question: str = Field(description="User's question.")
    answer: str = Field(description="Answer to the user's question with citations.")
    citations: list[Citation] = Field(description='List of citations.')
    thread_id: UUID = Field(description='Conversation UUID. A conversation is a sequence of questions and answers.')
    user_id: Optional[str] = Field(default=None, description='User UUID associated this question and answer.')


#
# Operator Models
#
class AnswerRequestBody(CamelModel):
    """
    Represents the request body for seeking an answer, containing the user's input
    and optional conversation thread ID.
    """

    input: str
    thread_id: Optional[UUID] = Field(
        default=None, description='Conversation UUID. A conversation is a sequence of questions and answers.'
    )
