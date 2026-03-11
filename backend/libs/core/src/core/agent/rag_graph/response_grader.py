"""
This module provides the node that evaluates whether an generated response addresses the input.

See: Response Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""

import logging

from ..internal_models import AgentPromptName
from .agent_state import GraphState
from .decorator_util import arunnable
from .grader_util import build_grader
from .internal_models import GradeResponse
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)


async def get_response_grader():
    """
    Initializes and returns a response grading chain.

    This function builds a grader that uses a chat prompt (GRADE_RESPONSE) and a Pydantic model
    (GradeResponse) for structured output. The grader is cached to avoid reinitialization.
    """
    prompt = await get_chat_prompt(prompt_name=AgentPromptName.GRADE_RESPONSE)

    response_grader = build_grader(prompt, GradeResponse, 'response_grader')

    return response_grader


@arunnable
async def grade_response(state: GraphState):
    """
    Determines whether the generation is grounded in the document and agent input.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call

    """
    logger.info('---CHECK RESPONSE---')

    user_input = state.input
    generation = state.generation

    response_grader = await get_response_grader()

    score = await response_grader.ainvoke(
        input={'user_input': user_input, 'generation': generation}, config={'metadata': {'chain_name': grade_response.name}}
    )

    grade = score.binary_score

    logger.info('---GRADE: GENERATION ADDRESSES INPUT %s---', grade)

    return {'response_addresses_input': grade}
