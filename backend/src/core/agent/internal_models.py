from enum import StrEnum


class AgentPromptName(StrEnum):
    """Enumeration of available agent prompt templates for different AI operations."""

    # Static constants for core prompts
    GENERATE_ANSWER = 'Generate Answer'
    REWRITE_QUERY = 'Rewrite Query'
    GRADE_RETRIEVED_DOCUMENTS = 'Grade Retrieved Documents'
    GRADE_ANSWER = 'Grade Answer'
    GRADE_HALLUCINATION = 'Grade Hallucination'
