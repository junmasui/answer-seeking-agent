"""
This module provides the LLM-based agent.
"""

from typing import Optional
from functools import cache
import logging
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.pregel import Pregel
from langgraph.errors import GraphRecursionError

from langfuse.callback import CallbackHandler

from .agent_state import GraphState
from .checkpointer import get_checkpointer
from .deciders import decide_to_generate, grade_generation_v_documents_and_question
from .document_retriever import retrieve_documents
from .postprocess import postprocess
from .preprocess import preprocess
from .retrieval_grader import grade_documents
from .answer_generator import generate_answer
from .question_rewriter import rewrite_question

from ..public_models import Answer, Citation


logger = logging.getLogger(__name__)



@cache
def get_agent_graph() -> Pregel:

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

def seek_answer(user_input: str, thread_id: Optional[uuid.UUID], user_id: Optional[str]):

    logger.info('user input: %s  thread_id: %s', user_input, thread_id)

    if not thread_id:
        thread_id = uuid.uuid4()
    elif isinstance(thread_id, str):
        thread_id = uuid.UUID(hex=thread_id)

    graph = get_agent_graph()
    logger.info('streaming_mode: %s', graph.stream_mode)

    # Initialize Langfuse CallbackHandler for Langchain (tracing)
    langfuse_handler = CallbackHandler(session_id=thread_id.hex, user_id=user_id, sample_rate=1.0)


    # See https://langchain-ai.github.io/langgraph/cloud/how-tos/stream_updates/

    input = {
        'question': user_input
    }
    # Capture into a dict, not TypedDict. We want to make zero assumptions about the
    # graph's stream output's keys. In other words, the set of keys is dynamic not static.
    # And because we are not static, we avoid TypedDict and its subclasses (ex: GraphState).
    latest_value = {}
    try:
        extra_data = {'thread_id': thread_id.hex}
        if user_id:
            extra_data['user_id'] = user_id
        run_config = {'recursion_limit': 15, 'configurable': extra_data}
        run_config['callbacks'] = [ langfuse_handler ]
        for output in graph.stream(input=input, config=run_config):
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

    citations = [Citation(doc_uuid=citation['doc_id'],
                          text=citation['text'],
                          page_number=citation.get('page_number'),
                          file_name=citation.get('file_name'))
                 for citation in citations]

    logger.info('answer: %s', answer)
    return Answer(
        question = user_input,
        answer = answer,
        citations = citations,
        thread_id = thread_id,
        user_id = user_id
    )
