"""
See https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#graph-state
"""

import logging

from .answer_grader import get_answer_grader
from .hallucination_grader import get_hallucination_grader

logger = logging.getLogger(__name__)


def check_for_relevant_documents(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    logger.info('---ASSESS GRADED DOCUMENTS---')

    filtered_documents = state['documents']

    if not filtered_documents:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        logger.info('---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---')
        return 'no relevant docs'
    else:
        # We have relevant documents, so generate answer
        logger.info('---DECISION: GENERATE---')
        return 'relevant docs found'


def check_for_halluciation(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    grade = state['grounded_in_facts']

    if grade == 'yes':
        logger.info('---DECISION: GENERATION IS GROUNDED IN FACTS FROM DOCUMENTS---')
        return 'not hallucinating'
    logger.info('---DECISION: GENERATION IS NOT GROUNDED IN FACTS FROM DOCUMENTS---')
    return 'is hallucinating'


def check_for_answer_relevancy(state):
    """
    Determines whether the generation the answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    grade = state['answer_addresses_question']

    if grade == 'yes':
        logger.info('---DECISION: GENERATION ADDRESSES QUESTION---')
        return 'useful'

    logger.info('---DECISION: GENERATION DOES NOT ADDRESS QUESTION---')
    return 'not useful'
