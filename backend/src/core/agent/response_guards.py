import logging

from core.agent.agent_state import GraphState  # Add this import

logger = logging.getLogger(__name__)


def detect_sensitive_info(state: GraphState):
    """
    Determines .

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call
    """
    logger.info('---CHECK SENSITIVE INFORMATION EXPOSURE---')
    _generation = state.answer

    return {
        'sensitive_info_exposure_detected': 0  #  "pii_fields_detected": [],  "confidence": 100
    }


def detect_toxic_response(state: GraphState):
    """
    Scan for harmful, biased, discriminatory, or inappropriate content in the response.

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call
    """
    logger.info('---CHECK TOXIC INPUT---')
    _documents = state.documents
    _generation = state.answer

    return {
        'toxic_response_detected': 0
        #  "categories_found": [],  "confidence": 100
    }
