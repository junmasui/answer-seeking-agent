"""This module provides the LLM-based agent."""

import logging
import pprint
import uuid
from functools import cache
from typing import Optional

from core_public import AgentResponse, Citation
from langgraph.errors import GraphRecursionError
from langgraph.pregel import Pregel

from ..doc_mgr import list_document_sets
from ..lib_config import get_lib_config
from .checkpointer import get_checkpointer
from .rag_graph import get_agent_graph

logger = logging.getLogger(__name__)

pp = pprint.PrettyPrinter(indent=2, width=120, underscore_numbers=True)


@cache
def get_compiled_agent_graph() -> Pregel:
    """
    Return a compiled Pregel agent graph.

    The graph is built using _get_uncompiled_agent_graph and compiled
    with a checkpointer. The result is cached to avoid recompilation
    on subsequent calls.

    Returns:
        A compiled Pregel agent graph.

    """
    uncompiled_graph = get_agent_graph()

    # Create a checkpointer
    checkpointer = get_checkpointer()

    # Compile the graph with a checkpointer
    compiled_graph = uncompiled_graph.compile(checkpointer=checkpointer, name='agent_graph')
    return compiled_graph


def get_mermaid_graph():
    """
    Return a mermaid graph of the agent.

    NOTE: When the `xray=True` is causing exceptions to be raised, then perform a
    meticulous inspection of the agent graph and subgraphs. The exception might be
    coming from a graph edge that is infrequently selected and leads to some deadends.
    This would allow live testing to pass (because it's infrequent) but would
    raise errors in visualization (because all paths are examined for rendering purposes).
    """
    graph = get_compiled_agent_graph()
    drawable_graph = graph.get_graph(xray=True)
    mermaid_graph = drawable_graph.draw_mermaid()

    return mermaid_graph


async def process_input(user_input: str, thread_id: Optional[uuid.UUID], user_id: Optional[uuid.UUID | str]):
    """
    Seek a response to the user's input using the agent graph.

    This involves retrieving documents, generating a response, and applying guardrails.
    """
    logger.info('user input: %s  thread_id: %s', user_input, thread_id)

    config = get_lib_config()

    if not thread_id:
        thread_id = uuid.uuid4()
    elif isinstance(thread_id, str):
        thread_id = uuid.UUID(hex=thread_id)

    result = await list_document_sets(is_public=True)
    doc_set_ids = [doc_set.id for doc_set in result.document_sets]

    graph = get_compiled_agent_graph()
    logger.info('streaming_mode: %s', graph.stream_mode)

    # See https://langchain-ai.github.io/langgraph/cloud/how-tos/stream_updates/

    logger.info('\n=============================\n=\n=\n=\n=')
    graph_input = {'input': user_input, 'document_set_ids': doc_set_ids}
    # Capture into a dict, not TypedDict. We want to make zero assumptions about the
    # graph's stream output's keys. In other words, the set of keys is dynamic not static.
    # And because we are not static, we avoid TypedDict and its subclasses (ex: GraphState).
    latest_value = {}
    try:
        user_id_str = user_id.hex if isinstance(user_id, uuid.UUID) else str(user_id) if user_id else None

        # configurable.thread_id is required by the LangGraph checkpointer for
        # conversation-state persistence — it is NOT a tracing concern.
        # All tracing / observability context lives in metadata and is
        # picked up automatically by the CustomInstrumentor monkey-patch on
        # Pregel.astream (which injects the OpenTelemetryCallbackHandler and
        # sets agent.* span attributes from metadata).
        run_config = {
            'recursion_limit': 30,
            'configurable': {
                'thread_id': thread_id.hex,
            },
            'metadata': {
                'thread_id': thread_id.hex,
                'user_id': user_id_str or '',
                'session_id': thread_id.hex,
                'input_preview': user_input[:500],
                'document_set_count': len(doc_set_ids),
            },
        }

        async for output in graph.astream(input=graph_input, config=run_config):
            for key, value in output.items():
                # Node
                logger.info("Node '%s':", key)
                if isinstance(value, dict):
                    latest_value.update(value)
    except GraphRecursionError as e:
        logger.error('Graph recursion error', exc_info=e)
    except Exception as e:
        logger.error('General error', exc_info=e)
    logger.info('\n=\n=\n=\n=\n=============================')

    # If we haven't assigned the response yet, then pull it from the
    # generated output.
    response_text = latest_value.get('response', '')
    citations = []

    if response_text:
        citations = latest_value.get('citations', [])
        citations = [
            Citation(
                doc_uuid=citation['doc_id'],
                text=citation['text'],
                source_url=citation.get('source_url'),
                page_number=citation.get('page_number'),
                file_name=citation.get('file_name'),
            )
            for citation in citations
        ]
    else:
        # If there was no generate output (for example, because there was an error),
        # then set it to a hard-wired generic response.
        response_text = 'I cannot find a response to this input at this moment'

    logger.info('response: %s', response_text)
    return AgentResponse(input=user_input, response=response_text, citations=citations, thread_id=thread_id, user_id=user_id)
