"""
This module provides the node that rewrites the user questions so that the document retrieval
returns with better relevancy.

See: Question Re-writer in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""

import logging

from langchain_core.output_parsers import StrOutputParser

from ...providers.chat_llm import get_chat_llm
from ..internal_models import AgentPromptName
from .agent_state import GraphState
from .decorator_util import runnable
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)


def get_question_rewriter():
    """
    Initializes and returns a question rewriting chain.

    The chain consists of a language model, a prompt for rewriting questions, and an output parser.
    It's configured to run with the name 'question_rewriter'.
    """
    # LLM
    llm = get_chat_llm()

    rewrite_prompt = get_chat_prompt(prompt_name=AgentPromptName.REWRITE_QUERY)

    chain = rewrite_prompt | llm | StrOutputParser()

    chain = chain.with_config({'run_name': 'question_rewriter'})

    return chain


@runnable
def rewrite_question(state: GraphState):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        dict: Updates to the graph state with the rewritten question

    """
    logger.info('---TRANSFORM QUERY---')
    question = state.question
    query_rewrite_count = state.query_rewrite_count

    question_rewriter = get_question_rewriter()

    # Re-write question
    better_question = question_rewriter.invoke(
        input={'question': question}, config={'metadata': {'chain_name': rewrite_question.name}}
    )

    # Update agent state with rewritten question.
    messages = [msg for msg in state.messages if msg.type == 'human']
    if len(messages) > 1:
        # Keep only the last human message
        messages = [messages[-1]]

    message = messages[-1]
    updated_message = message.model_copy(update={'content': better_question})

    state_updates = {
        'question': better_question,
        'messages': [updated_message],
        'query_rewrite_count': query_rewrite_count + 1,
    }

    return state_updates
