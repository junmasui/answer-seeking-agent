import functools
import re

from pydantic import BaseModel, Field


class AgentPromptName:
    """
    Enumeration of available agent prompt templates for different AI operations.

    Supports both static constants and dynamic runtime additions.
    """

    # Static constants for core prompts
    GENERATE_ANSWER = 'Generate Answer'
    REWRITE_QUERY = 'Rewrite Query'
    GRADE_RETRIEVED_DOCUMENTS = 'Grade Retrieved Documents'
    GRADE_ANSWER = 'Grade Answer'
    GRADE_HALLUCINATION = 'Grade Hallucination'

    @classmethod
    @functools.cache
    def all_prompts(cls):
        """
        Get a list of all static constant values from this class.

        Returns:
            list: List of prompt template names (cached after first call)
        """
        prompts = []
        for attr_name in dir(cls):
            # Skip private/magic methods and attributes, check if not callable,
            # and ensure name contains only uppercase letters and underscores
            if (
                not attr_name.startswith('_')
                and not callable(getattr(cls, attr_name))
                and re.match(r'^[A-Z_]+$', attr_name)
            ):
                attr_value = getattr(cls, attr_name)
                # Only include string constants (our prompt names)
                if isinstance(attr_value, str):
                    prompts.append(attr_value)
        return prompts


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(description='Documents are relevant to the question, "yes" or "no"')


class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(description='Answer is grounded in the facts, "yes" or "no"')


class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(description='Answer addresses the question, "yes" or "no"')
