"""
This module provides the LLM-based agent.
"""

from typing import Optional
from functools import cache
import logging
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError


from .agent_state import GraphState
from .checkpointer import get_checkpointer
from .deciders import decide_to_generate, grade_generation_v_documents_and_question
from .document_retriever import retrieve_documents
from .postprocess import postprocess
from .preprocess import preprocess
from .retrieval_grader import grade_documents
from .answer_generator import generate_answer
from .question_rewriter import rewrite_question

from ..public_models import Answer


logger = logging.getLogger(__name__)



@cache
def get_agent_graph():

    # Build graph

    graph_builder = StateGraph(GraphState)

    # Define the nodes
    graph_builder.add_node('preprocess', preprocess)  # capture
    graph_builder.add_node('postprocess', postprocess)  # capture

    graph_builder.add_node('retrieve', retrieve_documents)  # retrieve
    graph_builder.add_node('grade_documents', grade_documents)  # grade documents
    graph_builder.add_node('generate', generate_answer)  # generatae
    graph_builder.add_node('rewrite_query', rewrite_question)  # rewrite_query

    # Build graph
    graph_builder.add_edge(START, 'preprocess')
    graph_builder.add_edge('preprocess', 'retrieve')
    graph_builder.add_edge('retrieve', 'grade_documents')
    graph_builder.add_conditional_edges(
        'grade_documents',
        decide_to_generate,
        {
            'rewrite_query': 'rewrite_query',
            'generate': 'generate',
        },
    )
    graph_builder.add_edge('rewrite_query', 'retrieve')
    graph_builder.add_conditional_edges(
        'generate',
        grade_generation_v_documents_and_question,
        {
            'not supported': 'generate',
            'useful': 'postprocess',
            'not useful': 'rewrite_query',
        },
    )
    graph_builder.add_edge('postprocess', END)

    # Create a checkpointer
    checkpointer = get_checkpointer()

    # Compile the graph with a checkpointer
    graph = graph_builder.compile(checkpointer=checkpointer)
    return graph

def seek_answer(user_input: str, thread_id: Optional[uuid.UUID]):

    logger.info('user input: %s  thread_id: %s', user_input, thread_id)

    if not thread_id:
        thread_id = uuid.uuid4()
    elif isinstance(thread_id, str):
        thread_id = uuid.UUID(hex=thread_id)

    graph = get_agent_graph()
    logger.info('streaming_mode: %s', graph.stream_mode)

    # See https://langchain-ai.github.io/langgraph/cloud/how-tos/stream_updates/

    input = {
        'question': user_input
    }
    # Capture into a dict, not TypedDict. We want to make zero assumptions about the
    # graph's stream output's keys. In other words, the set of keys is dynamic not static.
    # And because we are not static, we avoid TypedDict and its subclasses (ex: GraphState).
    latest_value = {}
    answer = None
    try:
        run_config = {'recursion_limit': 15, 'configurable': {'thread_id': thread_id.hex}}
        for output in graph.stream(input=input, config=run_config):
            for key, value in output.items():
                # Node
                logger.info("Node '%s':", key)
                latest_value.update(value)
            logger.info('\n---\n')
    except GraphRecursionError as e:
        logger.error('Graph recursion error: %s', e)
    except Exception as e:
        logger.error('General error: %s', e)

    # If we haven't assigned the answer yet, then pull it from the
    # generated output.
    if answer is None:
        answer = latest_value.get('generation', None)

    # If there was no generate output (for example, because there was an error),
    # then set it to a hard-wired generic answer.
    if answer is None:
        answer = 'I cannot find the answer to this question at this moment'

    logger.info('answer: %s', answer)
    return Answer(
        question = user_input,
        answer = answer,
        thread_id = thread_id
    )
