import logging

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

    result = [x for x in result if x.get('score',0.) < 0.2 ]
    result = [x for x in result if x.get('entity_type') not in ['PERSON', 'LOCATION', 'DATE_TIME']]

    violation_score = len(result)

    return {'presidio_input_check': 100 if violation_score else 0}
