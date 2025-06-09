from typing import Annotated, Dict, List, Optional
from uuid import UUID

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field

from .constants import ResponseOverallGrade, RetrievalOverallGrade, UserInputGrade


class GraphState(BaseModel):
    """Represents the state of our graph."""

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Important for types like AnyMessage

    messages: Annotated[
        List[AnyMessage], Field(description='The accumulated list of messages in the current graph run.'), add_messages
    ]
    original_messages: Annotated[
        List[AnyMessage], Field(description='The original list of messages that initiated the graph run.'), add_messages
    ]
    next_message_id: Annotated[
        Optional[int], Field(default=None, description='ID for the next message to be processed.')
    ]

    question: Annotated[str, Field(description="The user's current question.")]
    document_set_ids: Annotated[
        Optional[List[UUID]], Field(default=None, description='IDs of document sets relevant to the question.')
    ]

    documents: Annotated[
        Optional[List[Document]], Field(default=None, description='List of retrieved document contents.')
    ]
    original_documents: Annotated[
        Optional[List[Document]], Field(default=None, description='List of retrieved document contents.')
    ]

    generation: Annotated[Optional[str], Field(default=None, description='The raw LLM generation.')]
    answer: Annotated[Optional[str], Field(default=None, description='The final answer to be presented.')]
    citations: Annotated[
        Optional[List[Dict[str, str]]], Field(default=None, description='List of citations supporting the answer.')
    ]

    input_overall_grade: Annotated[Optional[UserInputGrade], Field(default=None, description='Overall grade.')]
    injection_detected: Annotated[
        Optional[int],
        Field(default=None, ge=0, le=10, description='Score indicating likelihood of prompt injection (0-10).'),
    ]
    privacy_violation_detected: Annotated[
        Optional[int],
        Field(default=None, ge=0, le=10, description='Score indicating likelihood of privacy violation (0-10).'),
    ]
    toxic_input_detected: Annotated[
        Optional[int],
        Field(default=None, ge=0, le=10, description='Score indicating likelihood of toxic user input (0-10).'),
    ]

    retrieval_grade: Annotated[
        Optional[RetrievalOverallGrade],
        Field(default=None, description='Grade assessing the quality of the retrieval.'),
    ]
    document_relevancy: Annotated[
        Optional[List[Annotated[int, Field(ge=0, le=10)]]],
        Field(default=None, description='Score indicating document relevancy (0-10).'),
    ]
    toxic_content_detected: Annotated[
        Optional[List[Annotated[int, Field(ge=0, le=10)]]],
        Field(default=None, description='Score indicating likelihood of toxic LLM generation (0-10).'),
    ]

    answer_grade: Annotated[
        Optional[ResponseOverallGrade], Field(default=None, description='Grade assessing the quality of the answer.')
    ]
    grounded_in_facts: Annotated[
        Optional[str], Field(default=None, description='Assessment of whether the answer is factually grounded.')
    ]
    answer_addresses_question: Annotated[
        Optional[str],
        Field(default=None, description="Assessment of whether the answer addresses the user's question."),
    ]
    sensitive_info_exposure_detected: Annotated[
        Optional[int],
        Field(
            default=None,
            ge=0,
            le=10,
            description='Score indicating likelihood of sensitive information exposure (0-10).',
        ),
    ]
    toxic_response_detected: Annotated[
        Optional[int],
        Field(default=None, ge=0, le=10, description='Score indicating likelihood of overall toxic response (0-10).'),
    ]
