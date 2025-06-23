import logging

from langchain_core.messages import AIMessage  # Add HumanMessage

from core.agent.agent_state import GraphState  # Add this import

logger = logging.getLogger(__name__)


def add_response_to_history(state: GraphState):
    """
    Capture generated response.

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict)

    """
    logger.info('---ADD RESPONSE TO HISTORY---')
    response = state.response
    citations = state.citations

    # The content of an AIMessage should be a string. Store only the answer
    # intho this field. This avoid serialization issues with the LLM API.
    content = response

    # Store citations in additional_kwargs to preserve them in history
    # without breaking the LLM's expected input format.
    additional_kwargs = {'citations': citations}

    # Claim the next message id.
    next_message_id = x if (x := state.next_message_id) is not None else 0
    message_id = str(next_message_id)
    next_message_id += 1

    # Update agent state with new AI-generation entries in the message histories.
    state_updates = {
        'messages': [AIMessage(content=content, id=message_id, additional_kwargs=additional_kwargs)],
        'original_messages': [AIMessage(content=content, id=message_id, additional_kwargs=additional_kwargs)],
        'next_message_id': next_message_id,
    }
    return state_updates
