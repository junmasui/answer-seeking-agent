"""
This provides the retriever used by this application.

Retrievers support many types of systems,
including text search engines (commonly BM25), vectorstores (commonly HNSW),
graph databases, and relational databases. 
"""

from functools import cache

from ..vector_store import get_vector_store

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_retriever']

@cache
def get_retriever():
    vector_store = get_vector_store()

    return vector_store.as_retriever()
