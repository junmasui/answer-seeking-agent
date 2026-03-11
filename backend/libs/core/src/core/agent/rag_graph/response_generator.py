"""
This module provides the node that generates a response from the retrieved documents.

See https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#graph-state
"""

import logging

from ...providers.chat_llm import get_chat_llm
from ..internal_models import AgentPromptName
from .agent_state import GraphState
from .decorator_util import arunnable
from .prompt_util import get_chat_prompt
from .response_citation_parser import ResponseCitationParser

logger = logging.getLogger(__name__)


async def response_generator():
    """
    Create a response generation chain for RAG (Retrieval-Augmented Generation).

    Combines a chat prompt, language model, and response citation parser to generate response from
    retrieved documents with proper citation extraction.
    """
    prompt = await get_chat_prompt(prompt_name=AgentPromptName.GENERATE_RESPONSE)

    # LLM
    llm = get_chat_llm()

    # # Post-processing
    # def format_docs(docs):
    #     return '\n\n'.join(doc.page_content for doc in docs)

    # Chain
    rag_chain = prompt | llm | ResponseCitationParser()

    rag_chain = rag_chain.with_config({'run_name': 'response_generator'})

    return rag_chain


@arunnable
async def generate_response(state: GraphState):
    """
    Generate a response using the RAG agent.

    Args:
        state (dict): The current graph state

    Returns:
        dict: Updates to the graph state with the generated response and citations

    """
    logger.info('---GENERATE RESPONSE---')
    user_input = state.input
    documents = state.documents
    history = state.messages
    response_generation_count = state.response_generation_count

    chain = await response_generator()

    logger.info('Response generation count %d', response_generation_count)

    # RAG generation
    result = await chain.ainvoke(
        input={'documents': documents, 'chat_history': history, 'user_input': user_input},
        config={'configurable': {'documents': documents}, 'metadata': {'chain_name': generate_response.name}},
    )

    # Update state with generated output
    state_updates = {
        'generation': result['generation'],
        'response': result['response'],
        'citations': result['citations'],
        'response_generation_count': response_generation_count + 1,
    }
    return state_updates
