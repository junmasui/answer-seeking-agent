import logging
import pprint
from typing import Generator

import pytest
from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

from global_config import get_global_config

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_connection_str', 'sql_engine', 'reflected_metadata', 'auto_mapped_classes', 'get_sessionmaker']

logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=2, width=120)


def get_connection_str():
    config = get_global_config()

    connection_url = config.postgres_answers_connection_url

    # The connection string must use psycopg3!
    if not connection_url.scheme == 'postgresql+psycopg':
        raise ValueError

    # Convert away from PyDantic's custom type and to Python string.
    return str(connection_url)


@pytest.fixture(scope='module')
def sql_engine() -> Generator[Engine, None, None]:
    """Returns the SQLAlchemy engine for the database.

    The engine is a global object created just once for a particular database server.
    It creates and holds connections to the database server
    """
    connection_str = get_connection_str()

    engine = create_engine(connection_str)

    # Use yield so that we do clean up during the test tear-down.
    yield engine

    engine.dispose()


@pytest.fixture(scope='module')
def sql_sessionmaker(sql_engine) -> Generator[sessionmaker, None, None]:
    """Returns a SQLAlchemy sessionmaker object for the database.

    A sessionmaker is a factory for creating new Session objects.
    A Session object is like a connection with enhanced functionality for using
    the ORM paradigm (for examle, holding mappings between Python objects and database rows)
    """
    maker = sessionmaker(bind=sql_engine)

    yield maker


@pytest.fixture(scope='module')
def reflected_metadata(sql_engine) -> Generator[MetaData, None, None]:
    """Returns a Metadata object for the database."""
    metadata = MetaData(schema='answers')

    metadata.reflect(bind=sql_engine)

    # # Convert the tables attribute to a plain dict. The original reflected
    # # attribute is of type FacadeDict and is read-only
    # metadata.tables = dict(metadata.tables)

    # # Explicitly override column metadata known to be a custom datatype.
    # # The normal reflection mechanism does not know our custom datatypes.
    # if 'answers.tracked_documents' in metadata.tables:
    #     reflected_table = Table(
    #         'tracked_documents',
    #         metadata,
    #         Column('status', type_=DbDocumentStatus),
    #         autoload_with=sql_engine,
    #         extend_existing=True
    #     )
    #     metadata.tables['answers.tracked_documents'] = reflected_table

    # if 'answers.agent_prompt' in metadata.tables:
    #     reflected_table = Table(
    #         'agent_prompt',
    #         metadata,
    #         Column('status', type_=DbPromptStatus),
    #         autoload_with=sql_engine,
    #         extend_existing=True
    #     )
    #     metadata.tables['answers.agent_prompt'] = reflected_table

    yield metadata


@pytest.fixture(scope='module')
def auto_mapped_classes(sql_engine, reflected_metadata) -> Generator[dict[str, type], None, None]:
    """Returns the default automap base class for an automap schema."""

    # produce a set of mappings from this MetaData.
    Base = automap_base(metadata=reflected_metadata)

    # calling prepare() just sets up mapped classes and relationships.
    Base.prepare()

    classes = dict(Base.classes.items())

    # Use yield so that we do clean up during the test tear-down.
    yield classes
