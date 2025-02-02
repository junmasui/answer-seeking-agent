"""
See https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#graph-state
"""
import logging

from .hallucination_grader import get_hallucination_grader
from .answer_grader import get_answer_grader


logger = logging.getLogger(__name__)


def decide_to_generate(state):
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
        logger.info(
            '---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---'
        )
        return 'rewrite_query'
    else:
        # We have relevant documents, so generate answer
        logger.info('---DECISION: GENERATE---')
        return 'generate'


def grade_generation_v_documents_and_question(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    logger.info('---CHECK HALLUCINATIONS---')
    question = state['question']
    documents = state['documents']
    generation = state['generation']

    hallucination_grader = get_hallucination_grader()
    answer_grader = get_answer_grader()

    score = hallucination_grader.invoke(
        {'documents': documents, 'generation': generation}
    )
    grade = score.binary_score if score is not None else 'no'

    # Check hallucination
    if grade == 'yes':
        logger.info('---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---')
        
        # Check question-answering
        logger.info('---GRADE GENERATION vs QUESTION---')
        score = answer_grader.invoke({'question': question, 'generation': generation})
        grade = score.binary_score
        if grade == 'yes':
            logger.info('---DECISION: GENERATION ADDRESSES QUESTION---')
            return 'useful'
        else:
            logger.info('---DECISION: GENERATION DOES NOT ADDRESS QUESTION---')
            return 'not useful'
    else:
        logger.info('---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---')
        return 'not supported'
