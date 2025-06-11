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
        List[AnyMessage], Field(description='Original messages that initiated the graph run.'), add_messages
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
        Optional[List[Document]], Field(default=None, description='Original list of retrieved document contents.')
    ]

    generation: Annotated[Optional[str], Field(default=None, description='The raw LLM generation.')]
    answer: Annotated[Optional[str], Field(default=None, description='The final answer to be presented.')]
    citations: Annotated[
        Optional[List[Dict[str, str]]], Field(default=None, description='List of citations supporting the answer.')
    ]

    input_overall_grade: Annotated[
        Optional[UserInputGrade], Field(default=None, description='Overall grade for the user input.')
    ]
    nemo_input_check: Annotated[
        Optional[Annotated[int, Field(ge=0, le=10)]],
        Field(default=None, description='NeMo Guardrails score for input safety (0-10).'),
    ]
    presidio_input_check: Annotated[
        Optional[Annotated[int, Field(ge=0, le=10)]],
        Field(default=None, description='Presidio score for PII in input (0-10).'),
    ]

    retrieval_grade: Annotated[
        Optional[RetrievalOverallGrade],
        Field(default=None, description='Overall grade for retrieved document quality.'),
    ]
    document_relevancy: Annotated[
        Optional[List[Annotated[int, Field(ge=0, le=10)]]],
        Field(default=None, description='Relevancy scores (0-10) for each retrieved document.'),
    ]
    nemo_retrieval_check: Annotated[
        Optional[Annotated[int, Field(ge=0, le=10)]],
        Field(default=None, description='NeMo Guardrails score for retrieved doc safety (0-10).'),
    ]
    presidio_retrieval_check: Annotated[
        Optional[Annotated[int, Field(ge=0, le=10)]],
        Field(default=None, description='Presidio score for PII in retrieved docs (0-10).'),
    ]

    answer_grade: Annotated[
        Optional[ResponseOverallGrade], Field(default=None, description='Overall grade for generated answer quality.')
    ]
    grounded_in_facts: Annotated[
        Optional[str], Field(default=None, description='Is the answer factually grounded in provided documents?')
    ]
    answer_addresses_question: Annotated[
        Optional[str], Field(default=None, description="Does the answer address the user's question?")
    ]
    nemo_output_check: Annotated[
        Optional[Annotated[int, Field(ge=0, le=10)]],
        Field(default=None, description='NeMo Guardrails score for answer safety (0-10).'),
    ]
    presidio_output_check: Annotated[
        Optional[Annotated[int, Field(ge=0, le=10)]],
        Field(default=None, description='Presidio score for PII in the answer (0-10).'),
    ]
