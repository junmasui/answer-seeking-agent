"""See https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#graph-state"""

import logging

from core.agent.agent_state import GraphState

from .constants import ResponseOverallGrade, RetrievalOverallGrade, UserInputGrade

logger = logging.getLogger(__name__)


def check_if_safe_input(state: GraphState):
    """
    Determines whether to accept user input or not.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """
    logger.info('---ASSESS USER INPUT---')

    accept_input = (
        state.injection_detected < 5 and state.privacy_violation_detected < 5 or state.toxic_input_detected < 5
    )

    if not accept_input:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        logger.info('---DECISION: REJECT USER INPUT---')
        grade = UserInputGrade.REJECT_USER_INPUT
    else:
        # We have relevant documents, so generate answer
        logger.info('---DECISION: ACCEPT USER INPUT---')
        grade = UserInputGrade.ACCEPT_USER_INPUT

    return {'input_overall_grade': grade}


def filter_documents(state: GraphState):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict): Updates with relevant documents
    """
    logger.info('---CHECK DOCUMENT RELEVANCE TO QUESTION---')

    documents = state.documents

    # Score each doc
    filtered_docs = []
    for index, doc in enumerate(documents):
        keep = state.document_relevancy[index] > 5 and state.toxic_content_detected[index]

        if keep:
            logger.info('---FILTER: DOCUMENT ACCEPT---')
            filtered_docs.append(doc)
        else:
            logger.info('---FILTER: DOCUMENT REJECT---')
            continue

    # Keep only the relevant documents
    return {'documents': filtered_docs}


def check_for_relevant_documents(state: GraphState):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """
    logger.info('---ASSESS GRADED DOCUMENTS---')

    filtered_documents = state.documents

    if not filtered_documents:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        logger.info('---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---')
        return RetrievalOverallGrade.NO_RELEVANT_DOCS

    # We have relevant documents, so generate answer
    logger.info('---DECISION: GENERATE---')
    return RetrievalOverallGrade.RELEVANT_DOCS_FOUND


def check_response_quality(state: GraphState):
    """
    Determines whether the generation the answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """
    grade = state.grounded_in_facts
    if grade != 'yes':
        logger.info('---DECISION: GENERATION IS NOT GROUNDED IN FACTS FROM DOCUMENTS---')
    else:
        logger.info('---DECISION: GENERATION IS GROUNDED IN FACTS FROM DOCUMENTS---')

    grade = state.answer_addresses_question

    if grade != 'yes':
        logger.info('---DECISION: GENERATION DOES NOT ADDRESS QUESTION---')
    else:
        logger.info('---DECISION: GENERATION ADDRESSES QUESTION---')

    return ResponseOverallGrade.ACCEPT_ANSWER
