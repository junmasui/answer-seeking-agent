import logging

from langgraph.graph import StateGraph

from core.agent.constants import NodeName
from core.agent.deciders import check_if_safe_input
from core.agent.node_util import no_op

from .agent_state import GraphState
from .nemo_guards import execute_nemo_guardrails_check
from .presidio_guard import execute_presidio_check

logger = logging.getLogger(__name__)


def check_input_with_nemo(state: GraphState):
    """
    Determines .

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call

    """
    logger.info('---CHECK INPUT WITH NEMO GUARDRAILS---')
    question = state.question

    result = execute_nemo_guardrails_check('input_check', [{'role': 'user', 'content': question}])

    triggered_rail = result['output_data']['triggered_input_rail']

    return {'nemo_input_check': 100 if triggered_rail else 0}


def check_input_with_presidio(state: GraphState):
    """
    Determines .

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call

    """
    logger.info('---CHECK INPUT WITH PRESIDIO---')
    question = state.question

    result = execute_presidio_check(question)

    result = [x for x in result if x.get('score', 0.0) < 0.2]
    result = [x for x in result if x.get('entity_type') not in ['PERSON', 'LOCATION', 'DATE_TIME']]

    violation_score = len(result)

    return {'presidio_input_check': 100 if violation_score else 0}


def build_input_guard_subgraph():
    """
    Build and return a StateGraph for the input guard subgraph.

    This subgraph handles input validation tasks like prompt injection,
    privacy violation, and toxic input detection.

    Returns:
        A StateGraph instance for the input guard subgraph.

    """
    input_guard_subgraph = StateGraph(GraphState)

    input_guard_subgraph.add_node(NodeName.INPUT_GUARD_START, no_op('Enter Input Guard'))
    input_guard_subgraph.add_node(NodeName.INPUT_GUARD_DECISION, check_if_safe_input)

    input_guard_subgraph.add_node(NodeName.CHECK_INPUT_WITH_NEMO, check_input_with_nemo)
    input_guard_subgraph.add_node(NodeName.CHECK_INPUT_WITH_PRESIDIO, check_input_with_presidio)

    input_guard_subgraph.set_entry_point(NodeName.INPUT_GUARD_START)

    input_guard_subgraph.add_edge(NodeName.INPUT_GUARD_START, NodeName.CHECK_INPUT_WITH_NEMO)
    input_guard_subgraph.add_edge(NodeName.INPUT_GUARD_START, NodeName.CHECK_INPUT_WITH_PRESIDIO)

    input_guard_subgraph.add_edge(
        [NodeName.CHECK_INPUT_WITH_NEMO, NodeName.CHECK_INPUT_WITH_PRESIDIO], NodeName.INPUT_GUARD_DECISION
    )

    input_guard_subgraph.set_finish_point(NodeName.INPUT_GUARD_DECISION)
    return input_guard_subgraph
