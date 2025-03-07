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

    kwargs = {}

    doc_set_ids = state['document_set_ids']
    doc_set_ids = [str(x) for x in doc_set_ids]
    if doc_set_ids and len(doc_set_ids) > 0:
        kwargs['filter'] = {
            'document_set_id': {
                '$in': doc_set_ids
            }
        }

    retriever = get_retriever()

    # Retrieval
    documents = retriever.invoke(question, **kwargs)

    # Update agent state with retrieved documents
    stateUpdates = { 'documents': documents }
    return stateUpdates

