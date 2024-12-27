
from typing import Annotated, NotRequired
from typing_extensions import TypedDict

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
    generation: NotRequired[str]
    documents: NotRequired[list[str]]
