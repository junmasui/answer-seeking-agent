"""
This provides the embedding model used by this application.
"""

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_connection_str', 'get_engine', 'get_sessionmaker', 'get_connection_pool', 'DataDomain']

# For now, there is only one database provider
from .base import DataDomain
from .postgres import get_connection_pool, get_connection_str, get_engine, get_sessionmaker
