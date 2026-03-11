"""
Rewrite user input for better document retrieval relevancy.

This module provides the node that rewrites the user input for more relevant document retrieval.

See: Input Re-writer in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""

import logging

from langchain_core.output_parsers import StrOutputParser

from ...providers.chat_llm import get_chat_llm
from ..internal_models import AgentPromptName
from .agent_state import GraphState
from .decorator_util import arunnable
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)


async def get_input_rewriter():
    """
    Initializes and returns an input rewriting chain.

    The chain consists of a language model, a prompt for rewriting input, and an output parser.
    It's configured to run with the name 'input_rewriter'.
    """
    # LLM
    llm = get_chat_llm()

    rewrite_prompt = await get_chat_prompt(prompt_name=AgentPromptName.REWRITE_INPUT)

    chain = rewrite_prompt | llm | StrOutputParser()

    chain = chain.with_config({'run_name': 'input_rewriter'})

    return chain


@arunnable
async def rewrite_input(state: GraphState):
    """
    Transform the query to produce a better input.

    Args:
        state (dict): The current graph state

    Returns:
        dict: Updates to the graph state with the rewritten input

    """
    logger.info('---TRANSFORM QUERY---')
    user_input = state.input
    query_rewrite_count = state.query_rewrite_count

    input_rewriter = await get_input_rewriter()

    # Re-write input
    better_input = await input_rewriter.ainvoke(
        input={'user_input': user_input}, config={'metadata': {'chain_name': rewrite_input.name}}
    )

    # Update agent state with rewritten input.
    messages = [msg for msg in state.messages if msg.type == 'human']
    if len(messages) > 1:
        # Keep only the last human message
        messages = [messages[-1]]

    message = messages[-1]
    updated_message = message.model_copy(update={'content': better_input})

    state_updates = {
        'input': better_input,
        'messages': [updated_message],
        'query_rewrite_count': query_rewrite_count + 1,
    }

    return state_updates
