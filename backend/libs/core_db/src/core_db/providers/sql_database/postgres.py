"""This provides the vector store used by this application."""

from functools import cache

from core_public.status_models import PingResult, PingStatus
from psycopg_pool import AsyncConnectionPool
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from ...db_models.doc_mgr import DbTrackedDocument
from ...lib_config import get_lib_config
from .base import DataDomain

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = [
    'get_connection_str',
    'get_engine',
    'get_async_engine',
    'get_sessionmaker',
    'get_async_sessionmaker',
    'get_async_connection_pool',
    'ping_async_sql_database',
]


@cache
def get_connection_str(db_schema: DataDomain):
    """
    Get the PostgreSQL connection string for the specified database schema.

    Maps the DataDomain enum to the appropriate connection URL from configuration and validates that
    it uses the psycopg3 driver format.
    """
    config = get_lib_config()

    match db_schema:
        case DataDomain.AGENT:
            connection_url = config.postgres_agent_connection_url
        case DataDomain.VECTORS:
            raise NotImplementedError
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

    The engine is a global object created just once for a particular database server. It creates and
    holds connections to the database server
    """
    connection_str = get_connection_str(db_schema)

    engine = create_engine(connection_str)
    return engine


@cache
def get_async_engine(db_schema: DataDomain):
    """
    Returns a SQLAlchemy async engine for the database.

    The engine is a global object created just once for a particular database server. It creates and
    holds connections to the database server
    """
    connection_str = get_connection_str(db_schema)

    engine = create_async_engine(connection_str)
    return engine


@cache
def get_sessionmaker(db_schema: DataDomain):
    """
    Returns a SQLAlchemy sessionmaker object for the database.

    A sessionmaker is a factory for creating new Session objects. A Session object is like a
    connection with enhanced functionality for using the ORM paradigm (for examle, holding mappings
    between Python objects and database rows)
    """
    engine = get_engine(db_schema)

    session = sessionmaker(bind=engine)
    return session


@cache
def get_async_sessionmaker(db_schema: DataDomain):
    """
    Returns a SQLAlchemy async sessionmaker object for the database.

    A sessionmaker is a factory for creating new Session objects. A Session object is like a
    connection with enhanced functionality for using the ORM paradigm (for examle, holding mappings
    between Python objects and database rows)
    """
    engine = get_async_engine(db_schema)

    session = async_sessionmaker(bind=engine)
    return session


@cache
def get_async_connection_pool(db_schema: DataDomain):
    """
    Return an async database connection pool.

    This pool will be different from the one used by SQLAlchemy
    """
    connection_str = get_connection_str(db_schema)
    connection_str = connection_str.replace('+psycopg', '')

    pool = AsyncConnectionPool(conninfo=connection_str, min_size=2, max_size=10, open=False)
    return pool


async def ping_async_sql_database(db_schema: DataDomain) -> PingResult:
    """
    Pings the specified SQL database schema to check its health and connectivity.

    This function attempts to connect to the database and execute a simple query
    against the specified schema. For the 'AGENT' schema, it specifically checks
    for the existence of the 'agent' schema and the count of records in the
    tracked_documents table. For other schemas, a simple 'SELECT 1'
    is used as a basic connectivity test.

    Args:
        db_schema: The DataDomain schema to ping (e.g., AGENT, VECTORS, CHECKPOINTS).

    Returns:
        PingResult: An object containing the ping status (GOOD or BAD),
                    a descriptive message, and an optional error message if the ping failed.

    """
    try:
        engine = get_async_engine(db_schema)
        async with engine.connect() as connection:
            if db_schema == DataDomain.AGENT:
                # Check if the 'agent' schema exists
                schema_check_result = await connection.execute(
                    text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'agent';")
                )
                if not schema_check_result.fetchone():
                    # If the schema doesn't exist, we can't connect to it in a meaningful
                    # way for this check.
                    return PingResult(
                        status=PingStatus.BAD,
                        message=f"Schema '{db_schema.value}' does not exist.",
                        error=RuntimeError(f"Schema '{db_schema.value}' does not exist."),
                    )
                # If the schema exists, query for the count of records in the
                # tracked_documents table.
                table_name = DbTrackedDocument.__tablename__
                count_query = text(f'SELECT COUNT(*) FROM agent.{table_name}')
                record_count_result = await connection.execute(count_query)
                record_count = record_count_result.scalar_one_or_none()

                return PingResult(
                    status=PingStatus.GOOD,
                    message=f'Successfully connected to {db_schema.value} schema.',
                    statistics={'document_record_count': record_count if record_count is not None else 0},
                )
            else:
                # For other schemas, a simple SELECT 1 can be used as a basic check.
                await connection.execute(text('SELECT 1'))
        return PingResult(status=PingStatus.GOOD, message=f'Successfully connected to {db_schema.value} schema.')
    except Exception as e:
        # Log the exception for debugging purposes if a logger is available
        # logger.error(f"Error pinging database schema {db_schema.value}: {e}", exc_info=True)
        return PingResult(
            status=PingStatus.BAD,
            message=f'Failed to connect to {db_schema.value} schema due to an unexpected error.',
            error=str(e),
        )
