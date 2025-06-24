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

from core.agent.input_guard import build_input_guard_subgraph
from core.agent.node_util import no_op
from core.agent.response_guard import build_response_guard_subgraph
from core.agent.retrieval_guard import build_retrieval_guard_subgraph

from ..doc_mgr import list_document_sets
from ..lib_config import get_lib_config
from ..public_models import Answer, Citation
from .agent_state import GraphState
from .checkpointer import get_checkpointer
from .constants import NodeName, ResponseOverallGrade, RetrievalOverallGrade, UserInputGrade
from .deciders import gather_relevant_documents
from .document_retriever import query_documents
from .postprocess import add_response_to_history
from .preprocess import add_input_to_history
from .query_rewriter import rewrite_question
from .response_generator import generate_response
from .state_resetter import reset_state_on_start

logger = logging.getLogger(__name__)

pp = pprint.PrettyPrinter(indent=2, width=120, underscore_numbers=True)


def get_input_grade(state: GraphState):
    """
    Extract and return the input overall grade from the current state.

    Args:
        state: The current graph state.

    Returns:
        The input overall grade.

    """
    logger.info('---Extracting Input Grade: %s---', state.input_overall_grade)
    return state.input_overall_grade


def get_retrieval_grade_in_subgraph(state: GraphState):
    """
    Extract and return the retrieval grade from the current state, for use within a subgraph.

    It returns the specific grade if it indicates no relevant documents were found,
    otherwise defaults to a general value.

    Args:
        state: The current graph state.

    Returns:
        The retrieval grade or a default value.

    """
    logger.info('---Extracting Retrieval Grade: %s---', state.retrieval_grade)

    KICK_DECISION_TO_MAIN = '__default__'

    if state.retrieval_grade == RetrievalOverallGrade.RELEVANT_DOCS_FOUND:
        return KICK_DECISION_TO_MAIN

    if state.retrieval_grade == RetrievalOverallGrade.NO_RELEVANT_DOCS:
        # If the document retrieval attempts are still under the maximum,
        # then try again.
        config = get_lib_config()
        if state.query_rewrite_count < config.max_query_rewrites:
            return RetrievalOverallGrade.NO_RELEVANT_DOCS

        logger.warning('Maximum rewrite attempts reached. Exiting retrieval subgraph.')
        return KICK_DECISION_TO_MAIN

    return KICK_DECISION_TO_MAIN


def get_retrieval_grade(state: GraphState):
    """
    Extract and return the retrieval grade from the current state.

    It returns specific grades for rejection or successful finding of relevant documents,
    otherwise defaults to a general value.

    Args:
        state: The current graph state.

    Returns:
        The retrieval grade or a default value.

    """
    logger.info('---Extracting Retrieval Grade: %s---', state.retrieval_grade)

    # These 2 grades are definitive opinions from the subgraph regarding
    # the next node. Hence we simply accept the informed opinions.
    if state.retrieval_grade in [RetrievalOverallGrade.REJECT_RETRIEVAL, RetrievalOverallGrade.RELEVANT_DOCS_FOUND]:
        return state.retrieval_grade

    # When no documents were retrieved, we cannot generate a document-grounded response.
    # Thus we do not go to the response generation phase.
    if state.retrieval_grade == RetrievalOverallGrade.NO_RELEVANT_DOCS:
        return RetrievalOverallGrade.REJECT_RETRIEVAL

    return RetrievalOverallGrade.REJECT_RETRIEVAL


def get_answer_grade_in_subgraph(state: GraphState):
    """
    Extract and return the answer grade from the current state, for use within a subgraph.

    It returns the specific grade if it indicates answer generation needs to be redone,
    otherwise defaults to a general value.

    Args:
        state: The current graph state.

    Returns:
        The answer grade or a default value.

    """
    logger.info('---Extracting Response Grade: %s---', state.answer_grade)

    KICK_DECISION_TO_MAIN = '__default__'

    if state.answer_grade == ResponseOverallGrade.ACCEPT_RESPONSE:
        return KICK_DECISION_TO_MAIN

    if state.answer_grade == ResponseOverallGrade.REDO_RESPONSE_GENERATION:
        # If the response generation attempts are still under the maximum,
        # then try again.
        config = get_lib_config()
        logger.info(
            'Response generation comparison %d ? %d',
            state.response_generation_count,
            config.max_response_generation_attempts,
        )
        if state.response_generation_count < config.max_response_generation_attempts:
            return ResponseOverallGrade.REDO_RESPONSE_GENERATION

        logger.warning('Maximum generate attempts reached. Exiting retrieval subgraph.')
        return KICK_DECISION_TO_MAIN

    return KICK_DECISION_TO_MAIN


def get_answer_grade(state: GraphState):
    """
    Extract and return the answer grade from the current state.

    It returns specific grades for redoing document retrieval, accepting the answer,
    or rejecting the answer, otherwise defaults to a general value.

    Args:
        state: The current graph state.

    Returns:
        The answer grade or a default value.

    """
    logger.info('---Extracting Response Grade: %s---', state.answer_grade)

    # These 2 grades are definitive opinions from the subgraph regarding
    # the next node. Hence we simply accept the informed opinions.
    if state.answer_grade in [ResponseOverallGrade.REJECT_RESPONSE, ResponseOverallGrade.ACCEPT_RESPONSE]:
        return state.answer_grade

    # No acceptable answer was generated, despite retrying.
    if state.answer_grade == ResponseOverallGrade.REDO_RESPONSE_GENERATION:
        return ResponseOverallGrade.REJECT_RESPONSE

    if state.answer_grade == ResponseOverallGrade.REDO_DOCUMENT_RETRIEVAL:
        # If the document retrieval attempts reached the
        # maximum number of attempts, then we should reject the retrieval.
        config = get_lib_config()
        logger.info('Query rewrite comparison %d ? %d', state.query_rewrite_count, config.max_query_rewrites)
        if state.query_rewrite_count < config.max_query_rewrites:
            return ResponseOverallGrade.REDO_DOCUMENT_RETRIEVAL

        logger.warning('Maximum rewrite attempts reached. Exiting graph.')

    return ResponseOverallGrade.REJECT_RESPONSE


def _get_uncompiled_agent_graph() -> StateGraph:
    """Define and return the uncompiled LangGraph agent graph structure."""
    # Build subgraph for input guards.
    input_guard_subgraph = build_input_guard_subgraph()

    # Build subgraph for document retrieval.

    retrieval_subgraph = _build_retrieval_subgraph()

    # Build subgraph for answer generation.

    response_subgraph = _build_response_subgraph()

    # Build graph

    graph = StateGraph(GraphState)

    # Define the nodes
    graph.add_node(NodeName.BAD_INPUT, no_op('Bad input'))
    graph.add_node(NodeName.BAD_RETRIEVAL, no_op('Bad Retrieval'))
    graph.add_node(NodeName.BAD_RESPONSE, no_op('Bad Response'))

    graph.add_node(NodeName.RESET_STATE_ON_START, reset_state_on_start)
    graph.add_node(NodeName.ADD_QUERY_TO_HISTORY, add_input_to_history)
    graph.add_node(NodeName.ADD_RESPONSE_TO_HISTORY, add_response_to_history)

    graph.add_node(NodeName.INPUT_GUARD, input_guard_subgraph.compile())

    graph.add_node(NodeName.RETRIEVE_DOCUMENTS, retrieval_subgraph.compile())
    graph.add_node(NodeName.GENERATE_RESPONSE, response_subgraph.compile())

    # Build graph
    graph.add_edge(START, NodeName.RESET_STATE_ON_START)
    graph.add_edge(NodeName.RESET_STATE_ON_START, NodeName.INPUT_GUARD)
    graph.add_conditional_edges(
        NodeName.INPUT_GUARD,
        get_input_grade,
        {
            UserInputGrade.ACCEPT_USER_INPUT: NodeName.ADD_QUERY_TO_HISTORY,
            UserInputGrade.REJECT_USER_INPUT: NodeName.BAD_INPUT,
        },
    )
    graph.add_edge(NodeName.BAD_INPUT, END)

    graph.add_edge(NodeName.ADD_QUERY_TO_HISTORY, NodeName.RETRIEVE_DOCUMENTS)

    graph.add_conditional_edges(
        NodeName.RETRIEVE_DOCUMENTS,
        get_retrieval_grade,
        {
            RetrievalOverallGrade.REJECT_RETRIEVAL: NodeName.BAD_RETRIEVAL,
            RetrievalOverallGrade.RELEVANT_DOCS_FOUND: NodeName.GENERATE_RESPONSE,
        },
    )
    graph.add_edge(NodeName.BAD_RETRIEVAL, END)

    graph.add_conditional_edges(
        NodeName.GENERATE_RESPONSE,
        get_answer_grade,
        {
            ResponseOverallGrade.REDO_DOCUMENT_RETRIEVAL: NodeName.RETRIEVE_DOCUMENTS,
            ResponseOverallGrade.ACCEPT_RESPONSE: NodeName.ADD_RESPONSE_TO_HISTORY,
            ResponseOverallGrade.REJECT_RESPONSE: NodeName.BAD_RESPONSE,
        },
    )
    graph.add_edge(NodeName.ADD_RESPONSE_TO_HISTORY, END)
    graph.add_edge(NodeName.BAD_RESPONSE, END)

    return graph


def _build_retrieval_subgraph():
    """
    Build and return a StateGraph for the document retrieval subgraph.

    This subgraph manages the process of querying documents, applying
    retrieval guards, and rewriting queries if necessary.

    Returns:
        A StateGraph instance for the retrieval subgraph.

    """
    # Build subgraph for retrieved document guards.
    retrieval_guard_subgraph = build_retrieval_guard_subgraph()

    retrieval_subgraph = StateGraph(GraphState)

    retrieval_subgraph.add_node(NodeName.QUERY_DOCUMENTS, query_documents)
    retrieval_subgraph.add_node(NodeName.RETRIEVAL_GUARD, retrieval_guard_subgraph.compile())
    retrieval_subgraph.add_node(NodeName.GATHER_RELEVANT_DOCUMENTS, gather_relevant_documents)
    retrieval_subgraph.add_node(NodeName.REWRITE_QUERY, rewrite_question)
    retrieval_subgraph.add_node(NodeName.RETRIEVAL_EXIT, no_op('Exit Retrieval Subgraph'))

    retrieval_subgraph.set_entry_point(NodeName.QUERY_DOCUMENTS)
    retrieval_subgraph.add_edge(NodeName.QUERY_DOCUMENTS, NodeName.RETRIEVAL_GUARD)
    retrieval_subgraph.add_edge(NodeName.RETRIEVAL_GUARD, NodeName.GATHER_RELEVANT_DOCUMENTS)
    retrieval_subgraph.add_conditional_edges(
        NodeName.GATHER_RELEVANT_DOCUMENTS,
        get_retrieval_grade_in_subgraph,
        {RetrievalOverallGrade.NO_RELEVANT_DOCS: NodeName.REWRITE_QUERY, '__default__': NodeName.RETRIEVAL_EXIT},
    )
    retrieval_subgraph.add_edge(NodeName.REWRITE_QUERY, NodeName.QUERY_DOCUMENTS)
    retrieval_subgraph.set_finish_point(NodeName.RETRIEVAL_EXIT)
    return retrieval_subgraph


def _build_response_subgraph():
    """
    Build and return a StateGraph for the response generation subgraph.

    This subgraph handles generating an answer and applying response guards
    to ensure its quality.

    Returns:
        A StateGraph instance for the response generation subgraph.

    """
    # Build subgraph for response guards.
    response_guard_subgraph = build_response_guard_subgraph()

    response_subgraph = StateGraph(GraphState)
    response_subgraph.add_node(NodeName.GENERATE_RESPONSE, generate_response)
    response_subgraph.add_node(NodeName.RESPONSE_GUARD, response_guard_subgraph.compile())
    response_subgraph.add_node(NodeName.RESPONSE_EXIT, no_op('Exit Response Subgraph'))

    response_subgraph.set_entry_point(NodeName.GENERATE_RESPONSE)

    response_subgraph.add_edge(NodeName.GENERATE_RESPONSE, NodeName.RESPONSE_GUARD)

    response_subgraph.add_conditional_edges(
        NodeName.RESPONSE_GUARD,
        get_answer_grade_in_subgraph,
        {
            ResponseOverallGrade.REDO_RESPONSE_GENERATION: NodeName.GENERATE_RESPONSE,
            '__default__': NodeName.RESPONSE_EXIT,
        },
    )
    response_subgraph.set_finish_point(NodeName.RESPONSE_EXIT)
    return response_subgraph


@cache
def get_agent_graph() -> Pregel:
    """
    Return a compiled Pregel agent graph.

    The graph is built using _get_uncompiled_agent_graph and compiled
    with a checkpointer. The result is cached to avoid recompilation
    on subsequent calls.

    Returns:
        A compiled Pregel agent graph.

    """
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

    graph = get_agent_graph()
    logger.info('streaming_mode: %s', graph.stream_mode)

    # Initialize Langfuse CallbackHandler for Langchain (tracing)
    if config.enable_langfuse_tracing:
        callback_kwargs = {'session_id': thread_id.hex, 'sample_rate': 1.0}
        if user_id is not None:
            callback_kwargs['user_id'] = user_id.hex if isinstance(user_id, uuid.UUID) else user_id
        langfuse_handler = CallbackHandler(**callback_kwargs)

    # See https://langchain-ai.github.io/langgraph/cloud/how-tos/stream_updates/

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
        if langfuse_handler is not None:
            run_config['callbacks'] = [langfuse_handler]
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
