import logging

from .agent_state import GraphState
from .nemo_guards import execute_nemo_guardrails_check
from .presidio_guard import execute_presidio_check

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
    generation = state.answer

    result = execute_presidio_check(generation)

    violation_score = len(result)

    return {'presidio_output_check': 100 if violation_score else 0}
