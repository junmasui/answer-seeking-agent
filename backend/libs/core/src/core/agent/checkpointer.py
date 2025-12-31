import logging
from functools import cache

from core_db.providers.sql_database import DataDomain, get_async_connection_pool, get_connection_pool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from ..signals import start_up_handler

logger = logging.getLogger(__name__)


@start_up_handler
def checkpointer_startup(sender):
    """Set up database objects for the LangGraph checkpointer on application startup."""
    if sender.is_worker:
        return

    logger.info('Setting up checkpointer database objects')

    connection_pool = get_connection_pool(DataDomain.CHECKPOINTS)

    with connection_pool.connection() as conn:
        conn.autocommit = True
        checkpointer = PostgresSaver(conn)
        checkpointer.setup()


@cache
def get_checkpointer():
    """Return a cached instance of the AsyncPostgresSaver checkpointer."""
    connection_pool = get_async_connection_pool(DataDomain.CHECKPOINTS)

    checkpointer = AsyncPostgresSaver(connection_pool)
    return checkpointer
