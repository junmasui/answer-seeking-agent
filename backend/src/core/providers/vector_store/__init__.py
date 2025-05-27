"""This provides the vector store used by this application."""

from global_config import get_global_config

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_vector_store', 'find_vectors_by_document_id', 'delete_vectors_by_document_id']

vector_store_type = get_global_config().vector_store_type

match vector_store_type:
    case 'pgvector':
        from .pgvector import delete_vectors_by_document_id, find_vectors_by_document_id, get_vector_store
    case 'weaviate':
        from .weaviate import delete_vectors_by_document_id, find_vectors_by_document_id, get_vector_store
    case _:
        raise ValueError(f'Unknown vector store type: {vector_store_type}')
