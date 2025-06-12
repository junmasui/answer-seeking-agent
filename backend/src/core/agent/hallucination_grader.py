"""
This module provides the node that evaluates whether an generated answer contains hallucinations.

See: Hallucination Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""

import logging
from functools import cache

from core.agent.agent_state import GraphState

from .grader_util import build_grader
from .internal_models import AgentPromptName, GradeHallucinations
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)


@cache
def get_hallucination_grader():
    """
    Initializes and returns a hallucination grading chain.

    This function builds a grader that uses a chat prompt (GRADE_HALLUCINATION) and a Pydantic model
    (GradeHallucination) for structured output. The grader is cached to avoid reinitialization.
    """
    prompt = get_chat_prompt(prompt_name=AgentPromptName.GRADE_HALLUCINATION)

    hallucination_grader = build_grader(prompt, GradeHallucinations, 'hallucination_grader')

    return hallucination_grader


def grade_hallucination(state: GraphState):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call

    """
    logger.info('---CHECK HALLUCINATIONS---')

    documents = state.documents
    generation = state.answer

    hallucination_grader = get_hallucination_grader()

    score = hallucination_grader.invoke({'documents': documents, 'generation': generation})
    grade = score.binary_score if score is not None else 'no'

    return {'grounded_in_facts': grade}
