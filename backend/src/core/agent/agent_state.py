
from typing import Annotated, NotRequired
from typing_extensions import TypedDict
from uuid import UUID

from langgraph.graph.message import add_messages

from langchain_core.messages import MessageLikeRepresentation, AnyMessage

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """

    messages: Annotated[list[AnyMessage], add_messages]
    original_messages: Annotated[list[AnyMessage], add_messages]
    next_message_id: NotRequired[int]

    question: str
    document_set_ids: NotRequired[list[UUID]]

    documents: NotRequired[list[str]]

    generation: NotRequired[str]
    answer: NotRequired[str]
    citations: NotRequired[list[dict[str, str]]]

    answer_grade: NotRequired[str]
    grounded_in_facts: NotRequired[str]
    answer_addresses_question: NotRequired[str]