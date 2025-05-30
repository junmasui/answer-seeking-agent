"""This module provides the LLM-based agent."""

import logging
import pprint
import uuid
from functools import cache
from typing import Optional

from langfuse.callback import CallbackHandler
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.pregel import Pregel

from ..doc_mgr import list_document_sets
from ..public_models import Answer, Citation
from .agent_state import GraphState
from .answer_generator import generate_answer
from .answer_grader import grade_answer
from .checkpointer import get_checkpointer
from .deciders import check_for_answer_relevancy, check_for_halluciation, check_for_relevant_documents
from .document_retriever import query_documents
from .hallucination_grader import grade_hallucination
from .postprocess import add_response_to_history
from .preprocess import add_input_to_history
from .question_rewriter import rewrite_question
from .retrieval_grader import grade_documents

logger = logging.getLogger(__name__)

pp = pprint.PrettyPrinter(indent=2, width=120, underscore_numbers=True)


def redo_document_retrieval(_state):
    """Set the answer_grade to 'redo document retrieval' to indicate that document retrieval should be redone."""
    return {'answer_grade': 'redo document retrieval'}


def redo_answer_generation(_state):
    """Set the answer_grade to 'redo answer generation' to indicate that answer generation should be redone."""
    return {'answer_grade': 'redo answer generation'}


def accept_answer(_state):
    """Set the answer_grade to 'accept answer' to indicate that the current answer is acceptable."""
    return {'answer_grade': 'accept answer'}


def get_answer_grade(state):
    """Return the current answer_grade from the state."""
    return state['answer_grade']


def _get_uncompiled_agent_graph() -> StateGraph:
    """Define and return the uncompiled LangGraph agent graph structure."""
    # Build subgraph for document retrieval.

    retrieval_subgraph = StateGraph(GraphState)

    retrieval_subgraph.add_node('query_documents', query_documents)  # retrieve
    retrieval_subgraph.add_node('grade_documents', grade_documents)  # grade documents
    retrieval_subgraph.add_node('rewrite_query', rewrite_question)  # rewrite_query

    retrieval_subgraph.set_entry_point('query_documents')
    retrieval_subgraph.add_edge('query_documents', 'grade_documents')
    retrieval_subgraph.add_conditional_edges(
        'grade_documents',
        check_for_relevant_documents,
        {'no relevant docs': 'rewrite_query', 'relevant docs found': END},
    )
    retrieval_subgraph.add_edge('rewrite_query', 'query_documents')

    # Build subgraph for answer guardrails.

    guardrail_subgraph = StateGraph(GraphState)
    guardrail_subgraph.add_node('grade_hallucination', grade_hallucination)  # grade hallucination
    guardrail_subgraph.add_node('grade_answer', grade_answer)  # grade answers
    guardrail_subgraph.add_node('accept_answer', accept_answer)  # accept answer
    guardrail_subgraph.add_node('redo_document_retrieval', redo_document_retrieval)  # redo document retrieval
    guardrail_subgraph.add_node('redo_answer_generation', redo_answer_generation)  # redo answer generation

    guardrail_subgraph.set_entry_point('grade_hallucination')

    guardrail_subgraph.add_conditional_edges(
        'grade_hallucination',
        check_for_halluciation,
        {'is hallucinating': 'redo_answer_generation', 'not hallucinating': 'grade_answer'},
    )
    guardrail_subgraph.set_finish_point('redo_answer_generation')

    guardrail_subgraph.add_conditional_edges(
        'grade_answer', check_for_answer_relevancy, {'useful': 'accept_answer', 'not useful': 'redo_document_retrieval'}
    )
    guardrail_subgraph.set_finish_point('accept_answer')
    guardrail_subgraph.set_finish_point('redo_document_retrieval')

    # Build graph

    graph = StateGraph(GraphState)

    # Define the nodes
    graph.add_node('add_query_to_history', add_input_to_history)  # capture
    graph.add_node('add_response_to_history', add_response_to_history)  # capture

    graph.add_node('retrieve_documents', retrieval_subgraph.compile())  # retrieve
    graph.add_node('generate_answer', generate_answer)  # generate answer from documents
    graph.add_node('apply_guardrails', guardrail_subgraph.compile())  # guard

    # Build graph
    graph.add_edge(START, 'add_query_to_history')
    graph.add_edge('add_query_to_history', 'retrieve_documents')

    graph.add_edge('retrieve_documents', 'generate_answer')

    graph.add_edge('generate_answer', 'apply_guardrails')

    graph.add_conditional_edges(
        'apply_guardrails',
        get_answer_grade,
        {
            'redo document retrieval': 'retrieve_documents',
            'redo answer generation': 'generate_answer',
            'accept answer': 'add_response_to_history',
        },
    )

    graph.add_edge('add_response_to_history', END)

    return graph


@cache
def get_agent_graph() -> Pregel:
    uncompiled_graph = _get_uncompiled_agent_graph()

    # Create a checkpointer
    checkpointer = get_checkpointer()

    # Compile the graph with a checkpointer
    compiled_graph = uncompiled_graph.compile(checkpointer=checkpointer)
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
    graph = get_agent_graph()
    drawable_graph = graph.get_graph(xray=True)
    mermaid_graph = drawable_graph.draw_mermaid()

    return mermaid_graph


def seek_answer(user_input: str, thread_id: Optional[uuid.UUID], user_id: Optional[str]):
    """
    Seek an answer to the user's input using the agent graph.
    This involves retrieving documents, generating an answer, and applying guardrails.
    """
    logger.info('user input: %s  thread_id: %s', user_input, thread_id)

    if not thread_id:
        thread_id = uuid.uuid4()
    elif isinstance(thread_id, str):
        thread_id = uuid.UUID(hex=thread_id)

    result = list_document_sets(is_public=True)
    doc_set_ids = [doc_set.id for doc_set in result.document_sets]

    graph = get_agent_graph()
    logger.info('streaming_mode: %s', graph.stream_mode)

    # Initialize Langfuse CallbackHandler for Langchain (tracing)
    langfuse_handler = CallbackHandler(session_id=thread_id.hex, user_id=user_id, sample_rate=1.0)

    # See https://langchain-ai.github.io/langgraph/cloud/how-tos/stream_updates/

    graph_input = {'question': user_input, 'document_set_ids': doc_set_ids}
    # Capture into a dict, not TypedDict. We want to make zero assumptions about the
    # graph's stream output's keys. In other words, the set of keys is dynamic not static.
    # And because we are not static, we avoid TypedDict and its subclasses (ex: GraphState).
    latest_value = {}
    try:
        extra_data = {'thread_id': thread_id.hex}
        if user_id:
            extra_data['user_id'] = user_id
        run_config = {'recursion_limit': 30, 'configurable': extra_data}
        run_config['callbacks'] = [langfuse_handler]
        for output in graph.stream(input=graph_input, config=run_config):
            for key, value in output.items():
                # Node
                logger.info("Node '%s':", key)
                latest_value.update(value)
    except GraphRecursionError as e:
        logger.error('Graph recursion error', exc_info=e)
    except Exception as e:
        logger.error('General error', exc_info=e)

    # If we haven't assigned the answer yet, then pull it from the
    # generated output.
    answer = latest_value.get('answer', None)
    citations = []
    if answer is not None:
        citations = latest_value.get('citations', [])

    # If there was no generate output (for example, because there was an error),
    # then set it to a hard-wired generic answer.
    if answer is None:
        answer = 'I cannot find the answer to this question at this moment'
        citations = []

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

    logger.info('answer: %s', answer)
    return Answer(question=user_input, answer=answer, citations=citations, thread_id=thread_id, user_id=user_id)
