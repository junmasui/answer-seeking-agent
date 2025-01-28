"""
This provides the embedding model used by this application.
"""
# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_embeddings']

# For now, there is only one embeddings provider
from .huggingface import get_embeddings
