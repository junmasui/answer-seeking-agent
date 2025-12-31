import logging
from functools import cache

from core_db.providers.sql_database import DataDomain, get_async_connection_pool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from ..signals import start_up_handler

logger = logging.getLogger(__name__)


@start_up_handler
async def checkpointer_startup(sender):
    """Set up database objects for the LangGraph checkpointer on application startup."""
    if sender.is_worker:
        return

    logger.info('Setting up checkpointer database objects')

    connection_pool = get_async_connection_pool(DataDomain.CHECKPOINTS)

    async with connection_pool.connection() as conn:
        await conn.set_autocommit(True)
        checkpointer = AsyncPostgresSaver(conn)
        await checkpointer.setup()


@cache
def get_checkpointer():
    """Return a cached instance of the AsyncPostgresSaver checkpointer."""
    connection_pool = get_async_connection_pool(DataDomain.CHECKPOINTS)

    checkpointer = AsyncPostgresSaver(connection_pool)
    return checkpointer
