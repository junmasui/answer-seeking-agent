"""This module provides the LLM-based agent."""

import logging
import pprint
import uuid
from functools import cache
from typing import Optional

from langgraph.errors import GraphRecursionError
from langgraph.pregel import Pregel

from ..doc_mgr import list_document_sets
from ..lib_config import get_lib_config
from ..public_models import Answer, Citation
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


def seek_answer(user_input: str, thread_id: Optional[uuid.UUID], user_id: Optional[uuid.UUID | str]):
    """
    Seek an answer to the user's input using the agent graph.

    This involves retrieving documents, generating an answer, and applying guardrails.
    """
    logger.info('user input: %s  thread_id: %s', user_input, thread_id)

    config = get_lib_config()

    if not thread_id:
        thread_id = uuid.uuid4()
    elif isinstance(thread_id, str):
        thread_id = uuid.UUID(hex=thread_id)

    result = list_document_sets(is_public=True)
    doc_set_ids = [doc_set.id for doc_set in result.document_sets]

    graph = get_compiled_agent_graph()
    logger.info('streaming_mode: %s', graph.stream_mode)

    # Initialize telemetry callback handlers
    callback_handlers = []

    # Langfuse handler (legacy, will be deprecated)
    if config.enable_langfuse_tracing:
        callback_kwargs = {'session_id': thread_id.hex, 'sample_rate': 1.0}
        if user_id is not None:
            callback_kwargs['user_id'] = user_id.hex if isinstance(user_id, uuid.UUID) else user_id
        # Currently commented out for migration
        # langfuse_handler = CallbackHandler(**callback_kwargs)
        # callback_handlers.append(langfuse_handler)

    # OpenTelemetry/OpenLLMetry handler (new implementation)
    if config.enable_opentelemetry:
        from core.telemetry import get_callback_handler

        # Get callback handler (None if using OpenLLMetry auto-instrumentation)
        otel_handler = get_callback_handler(
            session_id=thread_id.hex,
            user_id=user_id.hex if isinstance(user_id, uuid.UUID) else user_id,
            sample_rate=config.otel_trace_sample_rate,
        )

        if otel_handler:
            callback_handlers.append(otel_handler)

        # Set session/user context for OpenLLMetry (if available)
        try:
            from core.telemetry.openllmetry import is_openllmetry_initialized, set_session_id, set_user_id

            if is_openllmetry_initialized():
                set_session_id(thread_id.hex)
                if user_id:
                    set_user_id(user_id.hex if isinstance(user_id, uuid.UUID) else user_id)
        except ImportError:
            pass  # OpenLLMetry not available

    # See https://langchain-ai.github.io/langgraph/cloud/how-tos/stream_updates/

    logger.info('\n=============================\n=\n=\n=\n=')
    graph_input = {'question': user_input, 'document_set_ids': doc_set_ids}
    # Capture into a dict, not TypedDict. We want to make zero assumptions about the
    # graph's stream output's keys. In other words, the set of keys is dynamic not static.
    # And because we are not static, we avoid TypedDict and its subclasses (ex: GraphState).
    latest_value = {}
    try:
        extra_data = {'thread_id': thread_id.hex}
        if user_id:
            extra_data['user_id'] = user_id.hex
        run_config = {'recursion_limit': 30, 'configurable': extra_data}
        if callback_handlers:
            run_config['callbacks'] = callback_handlers
        for output in graph.stream(input=graph_input, config=run_config):
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

    # If we haven't assigned the answer yet, then pull it from the
    # generated output.
    answer = latest_value.get('response', '')
    citations = []

    if answer:
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
        # then set it to a hard-wired generic answer.
        answer = 'I cannot find the answer to this question at this moment'

    logger.info('answer: %s', answer)
    return Answer(question=user_input, answer=answer, citations=citations, thread_id=thread_id, user_id=user_id)
