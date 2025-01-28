"""
This provides the vector store used by this application.
"""
import os
from functools import cache
import string
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from psycopg_pool import ConnectionPool

from global_config import get_global_config

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_connection_str', 'get_engine', 'get_sessionmaker', 'get_connection_pool']

@cache
def get_connection_str():
    config = get_global_config()
    # Remember to URL decode the value!
    template = urllib.parse.unquote(str(config.postgres_connection_url))
    template = string.Template(template)

    connection_str = template.safe_substitute({
        'BACKEND_POSTGRES_USER_NAME': config.postgres_user_name,
        'BACKEND_POSTGRES_USER_PASSWORD': urllib.parse.quote_plus(config.postgres_user_password),
    })

    # The connection string must use psycopg3!
    if not connection_str.startswith('postgresql+psycopg://'):
        raise ValueError

    return connection_str

@cache
def get_engine():
    """Returns the SQLAlchemy engine for the database.

    The engine is a global object created just once for a particular database server.
    It creates and holds connections to the database server
    """
    connection_str = get_connection_str()

    engine = create_engine(connection_str)
    return engine

@cache
def get_sessionmaker():
    """Returns a sessionmaker object for the database.

    A sessionmaker is a factory for creating new Session objects.
    A Session object is like a connection with enhanced functionality for using
    the ORM paradigm (for examle, holding mappings between Python objects and database rows)
    """
    engine = get_engine()

    session = sessionmaker(bind=engine)
    return session

@cache
def get_connection_pool():
    """Return a database connection pool. This pool will be different from
    the one used by SQLAlchemy
    """
    connection_str = get_connection_str()
    connection_str = connection_str.replace('+psycopg', '')

    pool = ConnectionPool(conninfo=connection_str, min_size=2, max_size=10)
    pool.open()

    return pool
