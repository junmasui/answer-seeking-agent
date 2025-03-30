"""
This module provides the node that evaluates whether an generated answer contains hallucinations.

See: Hallucination Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""
from functools import cache
import textwrap
import logging

from .internal_models import GradeHallucinations
from .grader_util import build_grader
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)

PROMPT_NAME='Grade Hallucination'

@cache
def get_hallucination_grader():
    """
    """

    # Instructions
    system = '''\
        You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts.

        Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts.'''
    human = '''\
        Set of facts:

        {documents}
        
        LLM generation:
        
        {generation}
        '''
    prompt = get_chat_prompt(prompt_name=PROMPT_NAME, default_system_message=system, default_human_message=human)

    hallucination_grader = build_grader(prompt, GradeHallucinations, 'hallucination_grader')

    return hallucination_grader


def grade_hallucination(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    logger.info('---CHECK HALLUCINATIONS---')
    documents = state['documents']
    generation = state['answer']

    hallucination_grader = get_hallucination_grader()

    score = hallucination_grader.invoke(
        {'documents': documents, 'generation': generation}
    )
    grade = score.binary_score if score is not None else 'no'

    return {
        'grounded_in_facts': grade
    }
