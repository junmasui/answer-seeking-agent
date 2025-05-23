"""
This provides the vector store used by this application.
"""

import os

from global_config import get_global_config

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_vector_store']

vector_store_type = get_global_config().vector_store_type

match vector_store_type:
    case 'pgvector':
        from .pgvector import get_vector_store
    case 'weaviate':
        from .weaviate import get_vector_store
    case _:
        raise ValueError(f'Unknown vector store type: {vector_store_type}')
