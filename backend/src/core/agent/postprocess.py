import logging

from langchain_core.messages import AIMessage  # Add HumanMessage

from core.agent.agent_state import GraphState  # Add this import

logger = logging.getLogger(__name__)


def add_response_to_history(state: GraphState):
    """
    Capture generated response

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict)
    """
    logger.info('---ADD RESPONSE TO HISTORY---')
    answer = state.answer
    citations = state.citations

    content = [{'answer': answer, 'citations': citations}]

    # Update agent state with new AI-generation entries in the message histories.

    next_message_id = state.get('next_message_id', 0)
    message_id = str(next_message_id)
    next_message_id += 1

    state_updates = {
        'messages': [AIMessage(content=content, id=message_id)],
        'original_messages': [AIMessage(content=content, id=message_id)],
        'next_message_id': next_message_id,
    }
    return state_updates
