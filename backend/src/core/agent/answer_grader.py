"""
This module provides the node that evaluates whether an generated answer addresses the question.

See: Answer Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""

import logging
from functools import cache

from core.agent.agent_state import GraphState

from .grader_util import build_grader
from .internal_models import AgentPromptName, GradeAnswer
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)


@cache
def get_answer_grader():
    """
    Initializes and returns an answer grading chain.

    This function builds a grader that uses a chat prompt (GRADE_ANSWER) and a Pydantic model
    (GradeAnswer) for structured output. The grader is cached to avoid reinitialization.
    """
    prompt = get_chat_prompt(prompt_name=AgentPromptName.GRADE_ANSWER)

    answer_grader = build_grader(prompt, GradeAnswer, 'answer_grader')

    return answer_grader


def grade_answer(state: GraphState):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call

    """
    logger.info('---CHECK ANSWER---')

    question = state.question
    generation = state.generation

    answer_grader = get_answer_grader()

    score = answer_grader.invoke({'question': question, 'generation': generation})

    grade = score.binary_score

    logger.info('---GRADE: GENERATION ADDRESSES QUESTION %s---', grade)

    return {'answer_addresses_question': grade}
