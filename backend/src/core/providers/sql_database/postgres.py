"""This provides the vector store used by this application."""

from functools import cache

from psycopg_pool import ConnectionPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from global_config import get_global_config

from .base import DataDomain

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_connection_str', 'get_engine', 'get_sessionmaker', 'get_connection_pool']


@cache
def get_connection_str(db_schema: DataDomain):
    """
    Get the PostgreSQL connection string for the specified database schema.

    Maps the DataDomain enum to the appropriate connection URL from configuration
    and validates that it uses the psycopg3 driver format.
    """
    config = get_global_config()

    match db_schema:
        case DataDomain.ANSWERS:
            connection_url = config.postgres_answers_connection_url
        case DataDomain.VECTORS:
            connection_url = config.postgres_vectors_connection_url
        case DataDomain.CHECKPOINTS:
            connection_url = config.postgres_checkpoints_connection_url
        case _:
            raise ValueError('unknown AppDbSchema value', db_schema)

    # The connection string must use psycopg3!
    if not connection_url.scheme == 'postgresql+psycopg':
        raise ValueError

    # Convert away from PyDantic's custom type and to Python string.
    return str(connection_url)


@cache
def get_engine(db_schema: DataDomain):
    """
    Returns a SQLAlchemy engine for the database.

    The engine is a global object created just once for a particular database server.
    It creates and holds connections to the database server
    """
    connection_str = get_connection_str(db_schema)

    engine = create_engine(connection_str)
    return engine


@cache
def get_sessionmaker(db_schema: DataDomain):
    """
    Returns a SQLAlchemy sessionmaker object for the database.

    A sessionmaker is a factory for creating new Session objects.
    A Session object is like a connection with enhanced functionality for using
    the ORM paradigm (for examle, holding mappings between Python objects and database rows)
    """
    engine = get_engine(db_schema)

    session = sessionmaker(bind=engine)
    return session


@cache
def get_connection_pool(db_schema: DataDomain):
    """
    Return a database connection pool. This pool will be different from
    the one used by SQLAlchemy
    """
    connection_str = get_connection_str(db_schema)
    connection_str = connection_str.replace('+psycopg', '')

    pool = ConnectionPool(conninfo=connection_str, min_size=2, max_size=10)
    pool.open()

    return pool
