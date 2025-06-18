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
from ..lib_config import get_lib_config
from ..public_models import Answer, Citation
from .agent_state import GraphState
from .answer_generator import generate_answer
from .answer_grader import grade_answer
from .checkpointer import get_checkpointer
from .constants import NodeName, ResponseOverallGrade, RetrievalOverallGrade, UserInputGrade
from .deciders import (
    check_for_relevant_documents,
    check_if_safe_input,
    check_response_quality,
    gather_relevant_documents,
)
from .document_guards import check_retrieval_with_nemo, check_retrieval_with_presidio
from .document_retriever import query_documents
from .hallucination_grader import grade_hallucination
from .input_guards import check_input_with_nemo, check_input_with_presidio
from .postprocess import add_response_to_history
from .preprocess import add_input_to_history
from .question_rewriter import rewrite_question
from .response_guards import check_output_with_nemo, check_output_with_presidio
from .retrieval_grader import grade_document_relevancies

logger = logging.getLogger(__name__)

pp = pprint.PrettyPrinter(indent=2, width=120, underscore_numbers=True)


def redo_document_retrieval(_state: GraphState):
    """
    Set the answer_grade to 'redo document retrieval' to indicate that document retrieval should
    be redone.
    """
    return {'answer_grade': ResponseOverallGrade.REDO_DOCUMENT_RETRIEVAL}


def redo_answer_generation(_state: GraphState):
    """
    Set the answer_grade to 'redo answer generation' to indicate that answer generation should be
    redone.
    """
    return {'answer_grade': ResponseOverallGrade.REDO_ANSWER_GENERATION}


def accept_answer(_state: GraphState):
    """Set the answer_grade to 'accept answer' to indicate that the current answer is acceptable."""
    return {'answer_grade': ResponseOverallGrade.ACCEPT_ANSWER}


def no_op(_state: GraphState):
    """
    Does nothing.

    This is useful for defining a fan-out or a fan-in node.
    """
    logger.info('---No Op---')
    return {}


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
    if state.retrieval_grade in [RetrievalOverallGrade.NO_RELEVANT_DOCS]:
        return state.retrieval_grade
    return '__default__'


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
    if state.retrieval_grade in [RetrievalOverallGrade.REJECT_RETRIEVAL, RetrievalOverallGrade.RELEVANT_DOCS_FOUND]:
        return state.retrieval_grade
    return '__default__'


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
    if state.answer_grade in [ResponseOverallGrade.REDO_ANSWER_GENERATION]:
        return state.answer_grade
    return '__default__'


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
    if state.answer_grade in [
        ResponseOverallGrade.REDO_DOCUMENT_RETRIEVAL,
        ResponseOverallGrade.ACCEPT_ANSWER,
        ResponseOverallGrade.REJECT_ANSWER,
    ]:
        return state.answer_grade
    return '__default__'


def _get_uncompiled_agent_graph() -> StateGraph:
    """Define and return the uncompiled LangGraph agent graph structure."""
    # Build subgraph for input guards.
    input_guard_subgraph = _build_input_guard_subgraph()

    # Build subgraph for document retrieval.

    retrieval_subgraph = _build_retrieval_subgraph()

    # Build subgraph for answer generation.

    response_subgraph = _build_response_subgraph()

    # Build graph

    graph = StateGraph(GraphState)

    # Define the nodes
    graph.add_node(NodeName.BAD_INPUT, no_op)
    graph.add_node(NodeName.BAD_RETRIEVAL, no_op)
    graph.add_node(NodeName.BAD_RESPONSE, no_op)

    graph.add_node(NodeName.ADD_QUERY_TO_HISTORY, add_input_to_history)
    graph.add_node(NodeName.ADD_RESPONSE_TO_HISTORY, add_response_to_history)

    graph.add_node(NodeName.INPUT_GUARD, input_guard_subgraph.compile())

    graph.add_node(NodeName.RETRIEVE_DOCUMENTS, retrieval_subgraph.compile())
    graph.add_node(NodeName.GENERATE_ANSWER, response_subgraph.compile())

    # Build graph
    graph.add_edge(START, NodeName.INPUT_GUARD)
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
            RetrievalOverallGrade.RELEVANT_DOCS_FOUND: NodeName.GENERATE_ANSWER,
        },
    )
    graph.add_edge(NodeName.BAD_RETRIEVAL, END)

    graph.add_conditional_edges(
        NodeName.GENERATE_ANSWER,
        get_answer_grade,
        {
            ResponseOverallGrade.REDO_DOCUMENT_RETRIEVAL: NodeName.RETRIEVE_DOCUMENTS,
            ResponseOverallGrade.ACCEPT_ANSWER: NodeName.ADD_RESPONSE_TO_HISTORY,
            ResponseOverallGrade.REJECT_ANSWER: NodeName.BAD_RESPONSE,
        },
    )
    graph.add_edge(NodeName.ADD_RESPONSE_TO_HISTORY, END)
    graph.add_edge(NodeName.BAD_RESPONSE, END)

    return graph


def _build_input_guard_subgraph():
    """
    Build and return a StateGraph for the input guard subgraph.

    This subgraph handles input validation tasks like prompt injection,
    privacy violation, and toxic input detection.

    Returns:
        A StateGraph instance for the input guard subgraph.

    """
    input_guard_subgraph = StateGraph(GraphState)

    input_guard_subgraph.add_node(NodeName.INPUT_GUARD_START, no_op)
    input_guard_subgraph.add_node(NodeName.INPUT_GUARD_DECISION, check_if_safe_input)

    input_guard_subgraph.add_node(NodeName.CHECK_INPUT_WITH_NEMO, check_input_with_nemo)
    input_guard_subgraph.add_node(NodeName.CHECK_INPUT_WITH_PRESIDIO, check_input_with_presidio)

    input_guard_subgraph.set_entry_point(NodeName.INPUT_GUARD_START)

    input_guard_subgraph.add_edge(NodeName.INPUT_GUARD_START, NodeName.CHECK_INPUT_WITH_NEMO)
    input_guard_subgraph.add_edge(NodeName.INPUT_GUARD_START, NodeName.CHECK_INPUT_WITH_PRESIDIO)

    input_guard_subgraph.add_edge(
        [NodeName.CHECK_INPUT_WITH_NEMO, NodeName.CHECK_INPUT_WITH_PRESIDIO], NodeName.INPUT_GUARD_DECISION
    )

    input_guard_subgraph.set_finish_point(NodeName.INPUT_GUARD_DECISION)
    return input_guard_subgraph


def _build_retrieval_guard_subgraph():
    """
    Build and return a StateGraph for the retrieval guard subgraph.

    This subgraph handles tasks related to document retrieval, such as
    grading relevancies and detecting toxic content.

    Returns:
        A StateGraph instance for the retrieval guard subgraph.

    """
    retrieval_guard_subgraph = StateGraph(GraphState)

    retrieval_guard_subgraph.add_node(NodeName.RETRIEVAL_GUARD_START, no_op)
    retrieval_guard_subgraph.add_node(NodeName.GATHER_RELEVANT_DOCUMENTS, gather_relevant_documents)
    retrieval_guard_subgraph.add_node(NodeName.RETRIEVAL_GUARD_DECISION, check_for_relevant_documents)

    retrieval_guard_subgraph.add_node(NodeName.GRADE_RELEVANCIES, grade_document_relevancies)  # grade documents
    retrieval_guard_subgraph.add_node(NodeName.CHECK_RETRIEVAL_WITH_NEMO, check_retrieval_with_nemo)
    retrieval_guard_subgraph.add_node(NodeName.CHECK_RETRIEVAL_WITH_PRESIDIO, check_retrieval_with_presidio)

    retrieval_guard_subgraph.set_entry_point(NodeName.RETRIEVAL_GUARD_START)

    retrieval_guard_subgraph.add_edge(NodeName.RETRIEVAL_GUARD_START, NodeName.GRADE_RELEVANCIES)
    retrieval_guard_subgraph.add_edge(NodeName.RETRIEVAL_GUARD_START, NodeName.CHECK_RETRIEVAL_WITH_NEMO)
    retrieval_guard_subgraph.add_edge(NodeName.RETRIEVAL_GUARD_START, NodeName.CHECK_RETRIEVAL_WITH_PRESIDIO)

    retrieval_guard_subgraph.add_edge(
        [NodeName.GRADE_RELEVANCIES, NodeName.CHECK_RETRIEVAL_WITH_NEMO, NodeName.CHECK_RETRIEVAL_WITH_PRESIDIO],
        NodeName.GATHER_RELEVANT_DOCUMENTS,
    )
    retrieval_guard_subgraph.add_edge(NodeName.GATHER_RELEVANT_DOCUMENTS, NodeName.RETRIEVAL_GUARD_DECISION)

    retrieval_guard_subgraph.set_finish_point(NodeName.RETRIEVAL_GUARD_DECISION)
    return retrieval_guard_subgraph


def _build_retrieval_subgraph():
    """
    Build and return a StateGraph for the document retrieval subgraph.

    This subgraph manages the process of querying documents, applying
    retrieval guards, and rewriting queries if necessary.

    Returns:
        A StateGraph instance for the retrieval subgraph.

    """
    # Build subgraph for retrieved document guards.
    retrieval_guard_subgraph = _build_retrieval_guard_subgraph()

    retrieval_subgraph = StateGraph(GraphState)

    retrieval_subgraph.add_node(NodeName.QUERY_DOCUMENTS, query_documents)  # retrieve
    retrieval_subgraph.add_node(NodeName.RETRIEVAL_GUARD, retrieval_guard_subgraph.compile())
    retrieval_subgraph.add_node(NodeName.GATHER_RELEVANT_DOCUMENTS, gather_relevant_documents)
    retrieval_subgraph.add_node(NodeName.REWRITE_QUERY, rewrite_question)  # rewrite_query
    retrieval_subgraph.add_node(NodeName.RETRIEVAL_EXIT, no_op)

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


def _build_response_guard_subgraph():
    """
    Build and return a StateGraph for the response guard subgraph.

    This subgraph is responsible for ensuring the quality and safety of the
    generated response by grading the answer, checking for hallucinations,
    and detecting sensitive or toxic content.

    Returns:
        A StateGraph instance for the response guard subgraph.

    """
    response_guard_subgraph = StateGraph(GraphState)

    response_guard_subgraph.add_node(NodeName.RESPONSE_GUARD_START, no_op)
    response_guard_subgraph.add_node(NodeName.RESPONSE_GUARD_DECISION, check_response_quality)

    response_guard_subgraph.add_node(NodeName.GRADE_ANSWER, grade_answer)  # grade answers
    response_guard_subgraph.add_node(NodeName.GRADE_HALLUCINATION, grade_hallucination)  # grade hallucination
    response_guard_subgraph.add_node(NodeName.CHECK_RESPONSE_WITH_NEMO, check_output_with_nemo)
    response_guard_subgraph.add_node(NodeName.CHECK_RESPONSE_WITH_PRESIDIO, check_output_with_presidio)

    response_guard_subgraph.set_entry_point(NodeName.RESPONSE_GUARD_START)

    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.GRADE_ANSWER)
    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.GRADE_HALLUCINATION)
    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.CHECK_RESPONSE_WITH_PRESIDIO)
    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.CHECK_RESPONSE_WITH_NEMO)

    response_guard_subgraph.add_edge(
        [
            NodeName.GRADE_ANSWER,
            NodeName.GRADE_HALLUCINATION,
            NodeName.CHECK_RESPONSE_WITH_NEMO,
            NodeName.CHECK_RESPONSE_WITH_PRESIDIO,
        ],
        NodeName.RESPONSE_GUARD_DECISION,
    )

    response_guard_subgraph.set_finish_point(NodeName.RESPONSE_GUARD_DECISION)
    return response_guard_subgraph


def _build_response_subgraph():
    """
    Build and return a StateGraph for the response generation subgraph.

    This subgraph handles generating an answer and applying response guards
    to ensure its quality.

    Returns:
        A StateGraph instance for the response generation subgraph.

    """
    # Build subgraph for response guards.
    response_guard_subgraph = _build_response_guard_subgraph()

    response_subgraph = StateGraph(GraphState)
    response_subgraph.add_node(NodeName.GENERATE_ANSWER, generate_answer)
    response_subgraph.add_node(NodeName.RESPONSE_GUARD, response_guard_subgraph.compile())
    response_subgraph.add_node(NodeName.RESPONSE_EXIT, no_op)

    response_subgraph.set_entry_point(NodeName.GENERATE_ANSWER)

    response_subgraph.add_edge(NodeName.GENERATE_ANSWER, NodeName.RESPONSE_GUARD)

    response_subgraph.add_conditional_edges(
        NodeName.RESPONSE_GUARD,
        get_answer_grade_in_subgraph,
        {ResponseOverallGrade.REDO_ANSWER_GENERATION: NodeName.GENERATE_ANSWER, '__default__': NodeName.RESPONSE_EXIT},
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


def seek_answer(user_input: str, thread_id: Optional[uuid.UUID], user_id: Optional[str]):
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
        if langfuse_handler is not None:
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
    answer = latest_value.get('answer', '')
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
