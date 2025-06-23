import logging

from .agent_state import GraphState
from .nemo_guards import execute_nemo_guardrails_check
from .presidio_guard import execute_presidio_check

logger = logging.getLogger(__name__)


def check_retrieval_with_nemo(state: GraphState):
    """
    Determines .

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call

    """
    logger.info('---CHECK RETRIEVED DOCUMENTS WITH NEMO GUARDRAILS---')
    documents = state.documents

    # When processing is concurrently parallel, there is zero guarantee
    # that an async for-loop over an array will have the computation
    # finish in the same order as the array. Thus, we need a data structure
    # that explicitly tracks the original ordering and restores it in
    # the final result.
    scores = {}

    for index, doc in enumerate(documents):
        docs_content = doc.page_content

        result = execute_nemo_guardrails_check('content_check', [{'role': 'user', 'content': docs_content}])

        triggered_rail = result['output_data']['triggered_input_rail']

        scores[index] = 100 if triggered_rail else 0

    scores = [scores[key] for key in sorted(scores.keys())]

    return {'nemo_retrieval_check': scores}


def check_retrieval_with_presidio(state: GraphState):
    """
    Determines .

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call

    """
    logger.info('---CHECK RETRIEVED DOCUMENTS WITH PRESIDIO---')
    documents = state.documents

    # When processing is concurrently parallel, there is zero guarantee
    # that an async for-loop over an array will have the computation
    # finish in the same order as the array. Thus, we need a data structure
    # that explicitly tracks the original ordering and restores it in
    # the final result.
    scores = {}

    for index, doc in enumerate(documents):
        docs_content = doc.page_content

        result = execute_presidio_check(docs_content)

        result = [x for x in result if x.get('score', 0.0) < 0.2]
        result = [x for x in result if x.get('entity_type') not in ['PERSON', 'LOCATION', 'DATE_TIME']]

        violation_score = len(result)
        scores[index] = 100 if violation_score else 0

    scores = [scores[key] for key in sorted(scores.keys())]

    return {'presidio_retrieval_check': scores}
