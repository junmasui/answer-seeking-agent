import logging

from langchain_core.messages import HumanMessage

from .agent_state import GraphState

logger = logging.getLogger(__name__)


def prepare_state(state: GraphState):
    state_updates = {
        'response': '',
        'citations': [],
        'query_rewrite_count': 0,
        'response_generation_count': 0,
        'input_overall_grade': None,
        'nemo_input_check': None,
        'presidio_input_check': None,
        'retrieval_grade': None,
        'document_relevancy': None,
        'nemo_retrieval_check': None,
        'presidio_retrieval_check': None,
        'answer_grade': None,
        'grounded_in_facts': None,
        'answer_addresses_question': None,
        'nemo_output_check': None,
        'presidio_output_check': None,
    }

    return state_updates


def add_input_to_history(state: GraphState):
    """
    Capture raw question.

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict)

    """
    logger.info('---ADD INPUT TO CHAT HISTORY---')

    question = state.question

    # Update agent state with new user-input entries in the message histories.

    next_message_id = x if (x := state.next_message_id) is not None else 0
    message_id = str(next_message_id)
    next_message_id += 1

    state_updates = {
        'messages': [HumanMessage(content=question, id=message_id)],
        'original_messages': [HumanMessage(content=question, id=message_id)],
        'next_message_id': next_message_id,
    }

    return state_updates
