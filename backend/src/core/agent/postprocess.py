
import logging


from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)


def postprocess(state):
    """
    Capture raw question

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict)
    """
    logger.info('---POSTPROCESS---')

    answer = state['generation']

    # Update agent state with new AI-generation entries in the message histories.

    next_message_id = state.get('next_message_id', 0)
    message_id = str(next_message_id)
    next_message_id += 1

    stateUpdates = {
        'messages': [ AIMessage(content=answer, id=message_id) ],
        'original_messages': [ AIMessage(content=answer, id=message_id) ],
        'next_message_id': next_message_id
    }
    return stateUpdates