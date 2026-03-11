"""
This module provides the node that evaluates whether an generated response contains hallucinations.

See: Hallucination Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""

import logging

from ..internal_models import AgentPromptName
from .agent_state import GraphState
from .decorator_util import arunnable
from .grader_util import build_grader
from .internal_models import GradeHallucinations
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)


async def get_hallucination_grader():
    """
    Initializes and returns a hallucination grading chain.

    This function builds a grader that uses a chat prompt (GRADE_HALLUCINATION) and a Pydantic model
    (GradeHallucination) for structured output. The grader is cached to avoid reinitialization.
    """
    prompt = await get_chat_prompt(prompt_name=AgentPromptName.GRADE_HALLUCINATION)

    hallucination_grader = build_grader(prompt, GradeHallucinations, 'hallucination_grader')

    return hallucination_grader


@arunnable
async def grade_hallucination(state: GraphState):
    """
    Determines whether the generation is grounded in the document and agent input.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call

    """
    logger.info('---CHECK HALLUCINATIONS---')

    documents = state.documents
    generation = state.response

    hallucination_grader = await get_hallucination_grader()

    score = await hallucination_grader.ainvoke(
        input={'documents': documents, 'generation': generation},
        config={'metadata': {'chain_name': grade_hallucination.name}},
    )
    grade = score.binary_score if score is not None else 'no'

    return {'grounded_in_facts': grade}
