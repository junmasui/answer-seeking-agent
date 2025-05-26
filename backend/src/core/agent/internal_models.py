from enum import Enum

from pydantic import BaseModel, Field

# Data model


class AgentPrompt(str, Enum):
    """Enumeration of available agent prompt templates for different AI operations."""

    GENERATE_ANSWER = 'Generate Answer'
    REWRITE_QUERY = 'Rewrite Query'
    GRADE_RETRIEVED_DOCUMENTS = 'Grade Retrieved Documents'
    GRADE_ANSWER = 'Grade Answer'
    GRADE_HALLUCINATION = 'Grade Hallucination'


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(description='Documents are relevant to the question, "yes" or "no"')


class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(description='Answer is grounded in the facts, "yes" or "no"')


class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(description='Answer addresses the question, "yes" or "no"')
