"""
This module provides the node that retreives documents for answering an user question.

See https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#graph-state
"""

import logging
import pprint

from langchain_core.documents import Document
from weaviate.classes.query import Filter

from core.agent.agent_state import GraphState

from ..lib_config import get_lib_config
from ..providers.retriever import get_retriever

logger = logging.getLogger(__name__)

pp = pprint.PrettyPrinter(indent=2, width=120, underscore_numbers=True)


def query_documents(state: GraphState):
    """
    Retrieve documents.

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict): Updates with retrieved documents

    """
    logger.info('---RETRIEVE---')
    question = state.question

    kwargs = {}

    doc_set_ids = state.document_set_ids
    vector_store_type = get_lib_config().vector_store_type

    match vector_store_type:
        case 'pgvector':
            if doc_set_ids and len(doc_set_ids) > 0:
                doc_set_ids = [str(x) for x in doc_set_ids]
                kwargs['filter'] = {'document_set_id': {'$in': doc_set_ids}}
        case 'weaviate':
            if doc_set_ids and len(doc_set_ids) > 0:
                # Create a weaviate-specific Filter object. This will be passed into
                # the weaviate API thru the key-word arguments of the call stack.
                # A code review shows that no conversion is made from a generic dict to
                # a weaviate-specific Filter object.
                where_filter = Filter.by_property('document_set_id').contains_any(doc_set_ids)
                kwargs['filters'] = where_filter

                # Return the chunk ID's.
                kwargs['return_uuids'] = True
        case _:
            raise ValueError(f'Unknown vector store type: {vector_store_type}')

    retriever = get_retriever()

    # Retrieval
    documents = retriever.invoke(question, **kwargs)

    # Remove irrelevant metadata. It's stuff that we don't need for processing
    # or evaluation.
    def _clean_up_retrieved(x: Document):
        """Remove irrelevant metadata and ensure document ID is properly set."""
        if 'orig_elements' in x.metadata:
            del x.metadata['orig_elements']

        if 'id' not in x:
            # The weaviate retrieve will include the object's id in the
            # `metdata` dictionary under the `uuid` key.
            if 'uuid' in x.metadata:
                x.id = x.metadata['uuid']
            elif 'id' in x.metadata:
                x.id = x.metadata['id']

        return x

    documents = [_clean_up_retrieved(x) for x in documents]

    logger.info('---RETRIEVED %d DOCUMENTS---', len(documents))
    
    for idx, doc in enumerate(documents):
        logger.info('document %d:\n%s', idx, doc)

    # Update agent state with retrieved documents
    state_updates = {'documents': documents}
    return state_updates
