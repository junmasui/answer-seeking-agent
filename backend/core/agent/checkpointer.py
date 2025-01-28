from ..providers.sql_database import get_connection_pool


from langgraph.checkpoint.postgres import PostgresSaver


from functools import cache


@cache
def get_checkpointer():
    connection_pool = get_connection_pool()


    with connection_pool.connection() as conn:
        conn.autocommit = True
        checkpointer = PostgresSaver(conn)
        checkpointer.setup()

    checkpointer = PostgresSaver(connection_pool)
    return checkpointer
