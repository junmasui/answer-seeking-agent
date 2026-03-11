from pydantic import BaseModel, Field


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(description='Documents are relevant to the input, "yes" or "no"')


class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation response."""

    binary_score: str = Field(description='Response is grounded in the facts, "yes" or "no"')


class GradeResponse(BaseModel):
    """Binary score to assess response addresses input."""

    binary_score: str = Field(description='Response addresses the input, "yes" or "no"')
