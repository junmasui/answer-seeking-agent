"""
This provides the vector store used by this application.
"""
import os

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_vector_store']

# For now, there is only one vector store provider.
from .pgvector import get_vector_store
