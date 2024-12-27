import logging

from langchain_core.messages import HumanMessage


logger = logging.getLogger(__name__)


def preprocess(state):
    """
    Capture raw question

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict)
    """
    logger.info('---PREPROCESS---')

    question = state['question']

    # Update agent state with new user-input entries in the message histories.

    next_message_id = state.get('next_message_id', 0)
    message_id = str(next_message_id)
    next_message_id += 1

    stateUpdates = {
        'messages': [ HumanMessage(content=question, id=message_id) ],
        'original_messages': [ HumanMessage(content=question, id=message_id) ],
        'next_message_id': next_message_id
    }

    return stateUpdates

