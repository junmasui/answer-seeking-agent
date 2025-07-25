import logging

from langgraph.graph import StateGraph

from .agent_state import GraphState
from .constants import NodeName
from .deciders import check_response_quality
from .hallucination_grader import grade_hallucination
from .nemo_guards import execute_nemo_guardrails_check
from .node_util import no_op
from .presidio_guard import execute_presidio_check
from .response_grader import grade_response

logger = logging.getLogger(__name__)


def check_output_with_nemo(state: GraphState):
    """
    Determines .

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call

    """
    logger.info('---CHECK RESPONSE WITH NEMO GUARDRAILS---')
    question = state.question
    generation = state.generation

    messages = [{'role': 'user', 'content': question}, {'role': 'assistant', 'content': generation}]
    result = execute_nemo_guardrails_check('output_check', messages)

    triggered_rail = result['output_data']['triggered_output_rail']

    return {'nemo_output_check': 100 if triggered_rail else 0}


def check_output_with_presidio(state: GraphState):
    """
    Determines .

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call

    """
    logger.info('---CHECK RESPONSE WITH PRESIDIO---')
    generation = state.response

    result = execute_presidio_check(generation)

    result = [x for x in result if x.get('score', 0.0) < 0.2]
    result = [x for x in result if x.get('entity_type') not in ['PERSON', 'LOCATION', 'DATE_TIME']]

    violation_score = len(result)

    return {'presidio_output_check': 100 if violation_score else 0}


def build_response_guard_subgraph():
    """
    Build and return a StateGraph for the response guard subgraph.

    This subgraph is responsible for ensuring the quality and safety of the
    generated response by grading the answer, checking for hallucinations,
    and detecting sensitive or toxic content.

    Returns:
        A StateGraph instance for the response guard subgraph.

    """
    response_guard_subgraph = StateGraph(GraphState)

    response_guard_subgraph.add_node(NodeName.RESPONSE_GUARD_START, no_op('Enter Response Guard'))
    response_guard_subgraph.add_node(NodeName.RESPONSE_GUARD_DECISION, check_response_quality)

    response_guard_subgraph.add_node(NodeName.GRADE_RESPONSE, grade_response)
    response_guard_subgraph.add_node(NodeName.GRADE_HALLUCINATION, grade_hallucination)
    response_guard_subgraph.add_node(NodeName.CHECK_RESPONSE_WITH_NEMO, check_output_with_nemo)
    response_guard_subgraph.add_node(NodeName.CHECK_RESPONSE_WITH_PRESIDIO, check_output_with_presidio)

    response_guard_subgraph.set_entry_point(NodeName.RESPONSE_GUARD_START)

    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.GRADE_RESPONSE)
    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.GRADE_HALLUCINATION)
    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.CHECK_RESPONSE_WITH_PRESIDIO)
    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.CHECK_RESPONSE_WITH_NEMO)

    response_guard_subgraph.add_edge(
        [
            NodeName.GRADE_RESPONSE,
            NodeName.GRADE_HALLUCINATION,
            NodeName.CHECK_RESPONSE_WITH_NEMO,
            NodeName.CHECK_RESPONSE_WITH_PRESIDIO,
        ],
        NodeName.RESPONSE_GUARD_DECISION,
    )

    response_guard_subgraph.set_finish_point(NodeName.RESPONSE_GUARD_DECISION)
    return response_guard_subgraph
