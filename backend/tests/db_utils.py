import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from global_config import get_global_config


# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_connection_str', 'get_engine', 'get_sessionmaker', 'get_connection_pool']


def get_connection_str():
    config = get_global_config()

    connection_url = config.postgres_answers_connection_url

    # The connection string must use psycopg3!
    if not connection_url.scheme == 'postgresql+psycopg':
        raise ValueError

    # Convert away from PyDantic's custom type and to Python string.
    return str(connection_url)

@pytest.fixture(scope="session")
def get_engine():
    """Returns the SQLAlchemy engine for the database.

    The engine is a global object created just once for a particular database server.
    It creates and holds connections to the database server
    """
    connection_str = get_connection_str()

    engine = create_engine(connection_str)

    # Use yield so that we do clean up during the test tear-down.
    yield engine

    engine.dispose()

@pytest.fixture(scope="module")
def get_sessionmaker(get_engine):
    """Returns a sessionmaker object for the database.

    A sessionmaker is a factory for creating new Session objects.
    A Session object is like a connection with enhanced functionality for using
    the ORM paradigm (for examle, holding mappings between Python objects and database rows)
    """
    engine = get_engine()

    session = sessionmaker(bind=engine)

    # Use yield so that we do clean up during the test tear-down.
    yield session

    session.close()
