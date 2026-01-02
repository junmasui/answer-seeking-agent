import early_init  # noqa: I001, F401 ## loading this module configures environment and logging


import asyncio
from sqlalchemy import pool
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_engine_from_config

# Autogeneration support for Postgres functions, views, etc

# Autogeneration support for Posgres enums

from alembic import context

# Access to our configuration .. which includes the Postgres connection string
from core_db.lib_config import get_lib_config

# This import will load our declared schema
import core_db.db_models

db_url = get_lib_config().postgres_answers_connection_url

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

config.set_main_option('sqlalchemy.url', str(db_url))

target_metadata = core_db.db_models.DECLARED_METADATA

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def is_database_empty(engine):
    """
    Check if the database connected to the given engine is empty or only contains the Alembic
    version table.

    Returns True if the database is considered empty, False otherwise.
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return len(tables) == 0 or tables == ['alembic_version']


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={'paramstyle': 'named'}
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    if is_database_empty(connection):
        print('Database is empty. Skipping migration generation.')
    else:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with the context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


#
# Alembic Execution Modes:
#
# 1. Offline Mode (--sql):
#    - "Generate a SQL script"
#    - Does NOT connect to the database.
#    - Reads the URL to determine the SQL dialect (e.g., Postgres).
#    - Prints raw SQL commands (CREATE TABLE...) to stdout or a file.
#    - Synchronous because it is purely CPU-bound text processing.
#
# 2. Online Mode (Default):
#    - "Apply changes to the database"
#    - Connects to the live database to inspect current state and execute SQL.
#    - Asynchronous to align with the project's AsyncEngine architecture.
#    - Uses `run_sync` to bridge the async connection to Alembic's internal synchronous logic.
#

if context.is_offline_mode():
    run_migrations_offline()
else:
    try:
        loop = asyncio.get_running_loop()
        # Event loop is already running, use nest_asyncio to allow nested loops
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.run(run_migrations_online())
    except RuntimeError:
        # No running loop, proceed normally
        asyncio.run(run_migrations_online())
