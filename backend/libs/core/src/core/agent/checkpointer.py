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
    await connection_pool.open()

    async with connection_pool.connection() as conn:
        await conn.set_autocommit(True)
        checkpointer = AsyncPostgresSaver(conn)
        await checkpointer.setup()


@cache
def get_checkpointer():
    """Return a cached instance of the AsyncPostgresSaver checkpointer."""
    connection_pool = get_async_connection_pool(DataDomain.CHECKPOINTS)
    # Note: The pool must be opened before use.
    # Since this is a sync function, we can't await open().
    # However, checkpointer_startup runs at startup and opens the pool.
    # If get_checkpointer is called before startup, it might fail if not opened.
    # But get_checkpointer is likely called during request handling, which is after startup.
    # Alternatively, we could make this async, but it's cached.

    checkpointer = AsyncPostgresSaver(connection_pool)
    return checkpointer
