import logging

from core.agent.agent_state import GraphState

logger = logging.getLogger(__name__)


def detect_prompt_injection(state: GraphState):
    """
    Determines .

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call
    """
    logger.info('---CHECK PROMPT INJECTIONS---')
    _question = state.question

    return {
        'injection_detected': 0  # "techniques_found": [],  "confidence": 100
    }


def detect_privacy_violation(state: GraphState):
    """
    Determines .

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call
    """
    logger.info('---CHECK PRIVACY VIOLATION---')
    _question = state.question

    return {
        'privacy_violation_detected': 0  #  "pii_types_detected": [],  "confidence": 100
    }


def detect_toxic_input(state: GraphState):
    """
    Determines .

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call
    """
    logger.info('---CHECK TOXIC INPUT---')
    _question = state.question

    return {
        'toxic_input_detected': 0  # "categories_found": [],  "confidence": 100
    }
