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
from .constants import NodeName, ResponseOverallGrade, RetrievalOverallGrade, UserInputGrade
from .deciders import (
    check_for_relevant_documents,
    check_if_safe_input,
    check_response_quality,
    gather_relevant_documents,
)
from .document_guards import detect_toxic_content
from .document_retriever import query_documents
from .hallucination_grader import grade_hallucination
from .input_guards import detect_privacy_violation, detect_prompt_injection, detect_toxic_input
from .postprocess import add_response_to_history
from .preprocess import add_input_to_history
from .question_rewriter import rewrite_question
from .response_guards import detect_sensitive_info, detect_toxic_response
from .retrieval_grader import grade_document_relevancies

logger = logging.getLogger(__name__)

pp = pprint.PrettyPrinter(indent=2, width=120, underscore_numbers=True)


def redo_document_retrieval(_state: GraphState):
    """
    Set the answer_grade to 'redo document retrieval' to indicate that document retrieval should
    be redone."""
    return {'answer_grade': ResponseOverallGrade.REDO_DOCUMENT_RETRIEVAL}


def redo_answer_generation(_state: GraphState):
    """
    Set the answer_grade to 'redo answer generation' to indicate that answer generation should be
    redone."""
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
    logger.info('---Extracting Input Grade: %s---', state.input_overall_grade)
    return state.input_overall_grade


def get_retrieval_grade_in_subgraph(state: GraphState):
    logger.info('---Extracting Retrieval Grade: %s---', state.retrieval_grade)
    if state.retrieval_grade in [RetrievalOverallGrade.NO_RELEVANT_DOCS]:
        return state.retrieval_grade
    return '__default__'


def get_retrieval_grade(state: GraphState):
    logger.info('---Extracting Retrieval Grade: %s---', state.retrieval_grade)
    if state.retrieval_grade in [RetrievalOverallGrade.REJECT_RETRIEVAL, RetrievalOverallGrade.RELEVANT_DOCS_FOUND]:
        return state.retrieval_grade
    return '__default__'


def get_answer_grade_in_subgraph(state: GraphState):
    logger.info('---Extracting Response Grade: %s---', state.answer_grade)
    if state.answer_grade in [ResponseOverallGrade.REDO_ANSWER_GENERATION]:
        return state.answer_grade
    return '__default__'


def get_answer_grade(state: GraphState):
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
    input_guard_subgraph = StateGraph(GraphState)

    input_guard_subgraph.add_node(NodeName.INPUT_GUARD_START, no_op)
    input_guard_subgraph.add_node(NodeName.INPUT_GUARD_DECISION, check_if_safe_input)

    input_guard_subgraph.add_node(NodeName.DETECT_PROMPT_INJECTION, detect_prompt_injection)
    input_guard_subgraph.add_node(NodeName.DETECT_PRIVACY_VIOLATION, detect_privacy_violation)
    input_guard_subgraph.add_node(NodeName.DETECT_TOXIC_INPUT, detect_toxic_input)

    input_guard_subgraph.set_entry_point(NodeName.INPUT_GUARD_START)

    input_guard_subgraph.add_edge(NodeName.INPUT_GUARD_START, NodeName.DETECT_PROMPT_INJECTION)
    input_guard_subgraph.add_edge(NodeName.INPUT_GUARD_START, NodeName.DETECT_PRIVACY_VIOLATION)
    input_guard_subgraph.add_edge(NodeName.INPUT_GUARD_START, NodeName.DETECT_TOXIC_INPUT)

    input_guard_subgraph.add_edge(
        [NodeName.DETECT_PROMPT_INJECTION, NodeName.DETECT_PRIVACY_VIOLATION, NodeName.DETECT_TOXIC_INPUT],
        NodeName.INPUT_GUARD_DECISION,
    )

    input_guard_subgraph.set_finish_point(NodeName.INPUT_GUARD_DECISION)
    return input_guard_subgraph


def _build_retrieval_guard_subgraph():
    retrieval_guard_subgraph = StateGraph(GraphState)

    retrieval_guard_subgraph.add_node(NodeName.RETRIEVAL_GUARD_START, no_op)
    retrieval_guard_subgraph.add_node(NodeName.GATHER_RELEVANT_DOCUMENTS, gather_relevant_documents)
    retrieval_guard_subgraph.add_node(NodeName.RETRIEVAL_GUARD_DECISION, check_for_relevant_documents)

    retrieval_guard_subgraph.add_node(NodeName.GRADE_RELEVANCIES, grade_document_relevancies)  # grade documents
    retrieval_guard_subgraph.add_node(NodeName.DETECT_TOXIC_CONTENT, detect_toxic_content)

    retrieval_guard_subgraph.set_entry_point(NodeName.RETRIEVAL_GUARD_START)

    retrieval_guard_subgraph.add_edge(NodeName.RETRIEVAL_GUARD_START, NodeName.GRADE_RELEVANCIES)
    retrieval_guard_subgraph.add_edge(NodeName.RETRIEVAL_GUARD_START, NodeName.DETECT_TOXIC_CONTENT)

    retrieval_guard_subgraph.add_edge(
        [NodeName.GRADE_RELEVANCIES, NodeName.DETECT_TOXIC_CONTENT], NodeName.GATHER_RELEVANT_DOCUMENTS
    )
    retrieval_guard_subgraph.add_edge(NodeName.GATHER_RELEVANT_DOCUMENTS, NodeName.RETRIEVAL_GUARD_DECISION)

    retrieval_guard_subgraph.set_finish_point(NodeName.RETRIEVAL_GUARD_DECISION)
    return retrieval_guard_subgraph


def _build_retrieval_subgraph():
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
    response_guard_subgraph = StateGraph(GraphState)

    response_guard_subgraph.add_node(NodeName.RESPONSE_GUARD_START, no_op)
    response_guard_subgraph.add_node(NodeName.RESPONSE_GUARD_DECISION, check_response_quality)

    response_guard_subgraph.add_node(NodeName.GRADE_ANSWER, grade_answer)  # grade answers
    response_guard_subgraph.add_node(NodeName.GRADE_HALLUCINATION, grade_hallucination)  # grade hallucination
    response_guard_subgraph.add_node(NodeName.DETECT_SENSITIVE_INFO, detect_sensitive_info)
    response_guard_subgraph.add_node(NodeName.DETECT_TOXIC_RESPONSE, detect_toxic_response)

    response_guard_subgraph.set_entry_point(NodeName.RESPONSE_GUARD_START)

    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.GRADE_ANSWER)
    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.GRADE_HALLUCINATION)
    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.DETECT_SENSITIVE_INFO)
    response_guard_subgraph.add_edge(NodeName.RESPONSE_GUARD_START, NodeName.DETECT_TOXIC_RESPONSE)

    response_guard_subgraph.add_edge(
        [
            NodeName.GRADE_ANSWER,
            NodeName.GRADE_HALLUCINATION,
            NodeName.DETECT_SENSITIVE_INFO,
            NodeName.DETECT_TOXIC_RESPONSE,
        ],
        NodeName.RESPONSE_GUARD_DECISION,
    )

    response_guard_subgraph.set_finish_point(NodeName.RESPONSE_GUARD_DECISION)
    return response_guard_subgraph


def _build_response_subgraph():
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
