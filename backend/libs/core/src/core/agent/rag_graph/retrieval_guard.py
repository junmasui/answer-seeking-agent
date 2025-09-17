import logging

from langgraph.graph import StateGraph

from .agent_state import GraphState
from .constants import NodeName
from .deciders import check_for_relevant_documents, gather_relevant_documents
from .nemo_guards import execute_nemo_guardrails_check
from .node_util import no_op
from .presidio_guard import execute_presidio_check
from .retrieval_grader import grade_document_relevancies

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

        # Some nemo responses may not include the expected keys. Handle missing
        # 'output_data' or 'triggered_input_rail' by treating them as False so
        # the returned scores match the behavior when triggered_rail is False.
        triggered_rail = False
        try:
            if isinstance(result, dict):
                output_data = result.get('output_data')
                if isinstance(output_data, dict):
                    triggered_rail = bool(output_data.get('triggered_input_rail', False))
        except Exception:
            # Be conservative: if anything unexpected happens, treat as not triggered
            triggered_rail = False

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
        result = [x for x in result if x.get('entity_type', None) not in ['PERSON', 'LOCATION', 'DATE_TIME']]

        violation_score = len(result)
        scores[index] = 100 if violation_score else 0

    scores = [scores[key] for key in sorted(scores.keys())]

    return {'presidio_retrieval_check': scores}


def build_retrieval_guard_subgraph():
    """
    Build and return a StateGraph for the retrieval guard subgraph.

    This subgraph handles tasks related to document retrieval, such as
    grading relevancies and detecting toxic content.

    Returns:
        A StateGraph instance for the retrieval guard subgraph.

    """
    retrieval_guard_subgraph = StateGraph(GraphState)

    retrieval_guard_subgraph.add_node(NodeName.RETRIEVAL_GUARD_START, no_op('Enter Retrieval Guard'))
    retrieval_guard_subgraph.add_node(NodeName.GATHER_RELEVANT_DOCUMENTS, gather_relevant_documents)
    retrieval_guard_subgraph.add_node(NodeName.RETRIEVAL_GUARD_DECISION, check_for_relevant_documents)

    retrieval_guard_subgraph.add_node(NodeName.GRADE_RELEVANCIES, grade_document_relevancies)
    retrieval_guard_subgraph.add_node(NodeName.CHECK_RETRIEVAL_WITH_NEMO, check_retrieval_with_nemo)
    retrieval_guard_subgraph.add_node(NodeName.CHECK_RETRIEVAL_WITH_PRESIDIO, check_retrieval_with_presidio)

    retrieval_guard_subgraph.set_entry_point(NodeName.RETRIEVAL_GUARD_START)

    retrieval_guard_subgraph.add_edge(NodeName.RETRIEVAL_GUARD_START, NodeName.GRADE_RELEVANCIES)
    retrieval_guard_subgraph.add_edge(NodeName.RETRIEVAL_GUARD_START, NodeName.CHECK_RETRIEVAL_WITH_NEMO)
    retrieval_guard_subgraph.add_edge(NodeName.RETRIEVAL_GUARD_START, NodeName.CHECK_RETRIEVAL_WITH_PRESIDIO)

    retrieval_guard_subgraph.add_edge(
        [NodeName.GRADE_RELEVANCIES, NodeName.CHECK_RETRIEVAL_WITH_NEMO, NodeName.CHECK_RETRIEVAL_WITH_PRESIDIO],
        NodeName.GATHER_RELEVANT_DOCUMENTS,
    )
    retrieval_guard_subgraph.add_edge(NodeName.GATHER_RELEVANT_DOCUMENTS, NodeName.RETRIEVAL_GUARD_DECISION)

    retrieval_guard_subgraph.set_finish_point(NodeName.RETRIEVAL_GUARD_DECISION)
    return retrieval_guard_subgraph
