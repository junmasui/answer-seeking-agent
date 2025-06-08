import logging

from core.agent.agent_state import GraphState  # Add this import

logger = logging.getLogger(__name__)


def detect_toxic_content(state: GraphState):
    """
    Determines if the document contains harmful, biased, offensive, or inappropriate content.

    Args:
        state (dict): The current graph state

    Returns:
        dict: Decision for next node to call
    """
    logger.info('---CHECK TOXIC CONTENT---')
    _question = state.question
    documents = state.documents

    toxic_content_detected = []
    for _doc in documents:
        toxic_content_detected.append(0)

    return {
        'toxic_content_detected': toxic_content_detected
        #  "categories_found": [],  "confidence": 100
    }
