"""
This module provides the node that evaluates whether an generated answer addresses the question.

See: Answer Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""

from functools import cache
import logging

from .internal_models import GradeAnswer, AgentPrompt
from .grader_util import build_grader
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)


@cache
def get_answer_grader():
    """ """

    prompt = get_chat_prompt(prompt_name=AgentPrompt.GRADE_ANSWER)

    answer_grader = build_grader(prompt, GradeAnswer, 'answer_grader')

    return answer_grader


def grade_answer(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    logger.info('---CHECK ANSWER---')

    question = state['question']
    generation = state['generation']

    answer_grader = get_answer_grader()

    score = answer_grader.invoke({'question': question, 'generation': generation})

    grade = score.binary_score

    logger.info('---GRADE: GENERATION ADDRESSES QUESTION %s---', grade)

    return {'answer_addresses_question': grade}
