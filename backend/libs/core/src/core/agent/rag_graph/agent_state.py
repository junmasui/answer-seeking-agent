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

    input: Annotated[str, Field(description="The user's current input.")]

    query_rewrite_count: Annotated[
        int,
        Field(
            default=0,
            description='The number of times the user input has been rewritten.',
            json_schema_extra={'reset_on_start': True},
        ),
    ]
    document_set_ids: Annotated[
        Optional[List[UUID]],
        Field(
            default=None,
            description='IDs of document sets relevant to the user input.',
            json_schema_extra={'reset_on_start': True},
        ),
    ]

    documents: Annotated[
        Optional[List[Document]],
        Field(
            default=None, description='List of retrieved document contents.', json_schema_extra={'reset_on_start': True}
        ),
    ]
    original_documents: Annotated[
        Optional[List[Document]],
        Field(
            default=None,
            description='Original list of retrieved document contents.',
            json_schema_extra={'reset_on_start': True},
        ),
    ]

    generation: Annotated[
        Optional[str],
        Field(default=None, description='The raw LLM generation.', json_schema_extra={'reset_on_start': True}),
    ]
    response: Annotated[
        Optional[str],
        Field(
            default=None, description='The final response to be presented.', json_schema_extra={'reset_on_start': True}
        ),
    ]
    citations: Annotated[
        Optional[List[Dict[str, str]]],
        Field(
            default=None,
            description='List of citations supporting the response.',
            json_schema_extra={'reset_on_start': True},
        ),
    ]
    response_generation_count: Annotated[
        int,
        Field(
            default=0,
            description='The number of times the response has been generated.',
            json_schema_extra={'reset_on_start': True},
        ),
    ]

    input_overall_grade: Annotated[
        Optional[UserInputGrade],
        Field(
            default=None, description='Overall grade for the user input.', json_schema_extra={'reset_on_start': True}
        ),
    ]
    nemo_input_check: Annotated[
        Optional[Annotated[int, Field(ge=0, le=100)]],
        Field(
            default=None,
            description='NeMo Guardrails score for input safety (0-100).',
            json_schema_extra={'reset_on_start': True},
        ),
    ]
    presidio_input_check: Annotated[
        Optional[Annotated[int, Field(ge=0, le=100)]],
        Field(
            default=None,
            description='Presidio score for PII in input (0-100).',
            json_schema_extra={'reset_on_start': True},
        ),
    ]

    retrieval_grade: Annotated[
        Optional[RetrievalOverallGrade],
        Field(
            default=None,
            description='Overall grade for retrieved document quality.',
            json_schema_extra={'reset_on_start': True},
        ),
    ]
    document_relevancy: Annotated[
        Optional[List[Annotated[int, Field(ge=0, le=10)]]],
        Field(
            default=None,
            description='Relevancy scores (0-10) for each retrieved document.',
            json_schema_extra={'reset_on_start': True},
        ),
    ]
    nemo_retrieval_check: Annotated[
        Optional[List[Annotated[int, Field(ge=0, le=100)]]],
        Field(
            default=None,
            description='NeMo Guardrails score for retrieved doc safety (0-100).',
            json_schema_extra={'reset_on_start': True},
        ),
    ]
    presidio_retrieval_check: Annotated[
        Optional[List[Annotated[int, Field(ge=0, le=100)]]],
        Field(
            default=None,
            description='Presidio score for PII in retrieved docs (0-100).',
            json_schema_extra={'reset_on_start': True},
        ),
    ]

    response_grade: Annotated[
        Optional[ResponseOverallGrade],
        Field(
            default=None,
            description='Overall grade for generated response quality.',
            json_schema_extra={'reset_on_start': True},
        ),
    ]
    grounded_in_facts: Annotated[
        Optional[str],
        Field(
            default=None,
            description='Is the response factually grounded in provided documents?',
            json_schema_extra={'reset_on_start': True},
        ),
    ]
    response_addresses_input: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Does the response address the user's input?",
            json_schema_extra={'reset_on_start': True},
        ),
    ]
    nemo_output_check: Annotated[
        Optional[Annotated[int, Field(ge=0, le=100)]],
        Field(
            default=None,
            description='NeMo Guardrails score for response safety (0-100).',
            json_schema_extra={'reset_on_start': True},
        ),
    ]
    presidio_output_check: Annotated[
        Optional[Annotated[int, Field(ge=0, le=100)]],
        Field(
            default=None,
            description='Presidio score for PII in the response (0-100).',
            json_schema_extra={'reset_on_start': True},
        ),
    ]
