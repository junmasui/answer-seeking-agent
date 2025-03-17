import logging
from functools import cache


from langgraph.checkpoint.postgres import PostgresSaver


from ..providers.sql_database import get_connection_pool, DataDomain

from ..signals import start_up_handler



logger = logging.getLogger(__name__)

@start_up_handler
def checkpointer_startup(sender):
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
    connection_pool = get_connection_pool(DataDomain.CHECKPOINTS)

    checkpointer = PostgresSaver(connection_pool)
    return checkpointer
