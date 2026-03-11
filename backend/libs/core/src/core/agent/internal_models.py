from enum import StrEnum


class AgentPromptName(StrEnum):
    """Enumeration of available agent prompt templates for different AI operations."""

    # Static constants for core prompts
    GENERATE_RESPONSE = 'Generate Response'
    REWRITE_INPUT = 'Rewrite Input'
    GRADE_RETRIEVED_DOCUMENTS = 'Grade Retrieved Documents'
    GRADE_RESPONSE = 'Grade Response'
    GRADE_HALLUCINATION = 'Grade Hallucination'
