import logging

from .agent_state import GraphState
from .constants import ResponseOverallGrade, RetrievalOverallGrade, UserInputGrade
from .decorator_util import runnable

logger = logging.getLogger(__name__)

@runnable
def check_if_safe_input(state: GraphState):
    """
    Determines whether to accept user input or not.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call

    """
    logger.info('---ASSESS USER INPUT---')

    accept_input = state.nemo_input_check < 5 and state.presidio_input_check < 5

    if not accept_input:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        logger.info('---DECISION: REJECT USER INPUT---')
        overall_grade = UserInputGrade.REJECT_USER_INPUT
    else:
        # We have relevant documents, so generate answer
        logger.info('---DECISION: ACCEPT USER INPUT---')
        overall_grade = UserInputGrade.ACCEPT_USER_INPUT

    return {'input_overall_grade': overall_grade}


@runnable
def gather_relevant_documents(state: GraphState):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict): Updates with relevant documents

    """
    logger.info('---CHECK DOCUMENT RELEVANCE TO QUESTION---')

    documents = state.documents

    logger.info('---Document relevancy %r---', state.document_relevancy)
    logger.info('---Presidio check %r---', state.presidio_retrieval_check)
    logger.info('---Nemo check %r---', state.nemo_retrieval_check)

    filtered_docs = []
    # Score each doc
    for index, doc in enumerate(documents):
        keep = (
            state.document_relevancy[index] > 5
            and state.presidio_retrieval_check[index] < 40
            and state.nemo_retrieval_check[index] < 40
        )

        if keep:
            logger.info('---FILTER: DOCUMENT %d ACCEPT---', index)
            filtered_docs.append(doc)
        else:
            logger.info('---FILTER: DOCUMENT %s REJECT---', index)
            continue

    # Keep only the relevant documents
    return {'documents': filtered_docs}


@runnable
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
        logger.info('---DECISION: NO DOCUMENTS ARE RELEVANT TO QUESTIION---')
        overall_grade = RetrievalOverallGrade.NO_RELEVANT_DOCS
    else:
        # We have relevant documents, so generate answer
        logger.info('---DECISION: GENERATE---')
        overall_grade = RetrievalOverallGrade.RELEVANT_DOCS_FOUND
    return {'retrieval_grade': overall_grade}


def check_response_quality(state: GraphState):
    """
    Determines whether the generation the answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call

    """
    grade = state.answer_addresses_question

    if grade != 'yes':
        logger.info('---DECISION: GENERATION DOES NOT ADDRESS QUESTION---')
        overall_grade = ResponseOverallGrade.REDO_RESPONSE_GENERATION
    else:
        logger.info('---DECISION: GENERATION ADDRESSES QUESTION---')
        grade = state.grounded_in_facts
        if grade != 'yes':
            logger.info('---DECISION: GENERATION IS NOT GROUNDED IN FACTS FROM DOCUMENTS---')
            overall_grade = ResponseOverallGrade.REDO_DOCUMENT_RETRIEVAL
        else:
            logger.info('---DECISION: GENERATION IS GROUNDED IN FACTS FROM DOCUMENTS---')
            overall_grade = ResponseOverallGrade.ACCEPT_RESPONSE

    return {'answer_grade': overall_grade}
