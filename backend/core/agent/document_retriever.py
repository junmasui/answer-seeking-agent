"""
This module provides the node that retreives documents
for answering an user question.

See https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#graph-state
"""

import logging

from ..providers.retriever import get_retriever


logger = logging.getLogger(__name__)



def retrieve_documents(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict): Updates with retrieved documents
    """
    logger.info('---RETRIEVE---')
    question = state['question']

    retriever = get_retriever()

    # Retrieval
    documents = retriever.invoke(question)

    # Update agent state with retrieved documents
    stateUpdates = { 'documents': documents }
    return stateUpdates

