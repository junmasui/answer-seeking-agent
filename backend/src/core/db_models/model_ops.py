import logging

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import MetaData, text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

from global_config import get_global_config

from ..providers.sql_database import get_engine, get_sessionmaker, DataDomain

from .base import DECLARED_METADATA


logger = logging.getLogger(__name__)



def create_tables_if_not_exists():
    """Creates tables for model objects defined with this module's `Base`.
    """
    logger.info('creating tables that are absent')

    engine = get_engine(DataDomain.ANSWERS)

    if get_current_version(engine) != get_head_revision():
        logger.info('CHECK THAT MIGRATIONS HAVE BEEN APPLIED')
    else:
        differences = get_schema_differences(engine)

        # Analyze the differences
        if differences:
            logger.info('CHECK THAT MIGRATION STEPS HAVE BEEN DEFINED')
            for diff in differences:
                op = diff[0]
                obj_name = getattr(diff[1], 'name') if diff[1] is not None else ''
                logger.info('DB difference: %s %s', op, obj_name)

    _create_tables_if_new(engine)
    _run_migrations(engine)


def get_current_version(engine):
    """Return the current Alembic version applied to the database.
    """

    reflected_metadata = MetaData(schema='answers')
    reflected_metadata.reflect(bind=engine)

    if reflected_metadata.tables is None or len(reflected_metadata.tables) == 0:
        logger.info('database is empty.')
        return  None

    session_maker = sessionmaker(bind=engine)
    with session_maker() as session:
        try:
            # There is not a lot of good official documentation at https://alembic.sqlalchemy.org/
            # regarding the table `alembic_version`. Specifically, there is a lack of documentation
            # regarding the number of records in the table `alembic_version`
            #
            # The best available information is at https://alembic.sqlalchemy.org/en/latest/cookbook.html#create-revision-migrations
            # where the examples show the trace:
            #  * SELECT alembic_version.version_num FROM alembic_version
            # The lack of a WHERE clause suggests that this table has only one record.
            return session.execute(text("SELECT version_num FROM alembic_version")).scalar()
        except NoResultFound:
            return None  # No migrations applied

def get_head_revision():
    """Return the head Alembic version of the defined migration steps.
    """
    alembic_ini = get_global_config().alembic_ini_path
    alembic_cfg = Config(file_=str(alembic_ini))
    script = ScriptDirectory.from_config(alembic_cfg)
    head_revision = script.get_current_head()
    return head_revision

def get_schema_differences(engine):

    # Declared metadata.
    metadata = DECLARED_METADATA

    # Connect to the database for the actual metadata.
    connection = engine.connect()
    
    # Configure the migration context
    context = MigrationContext.configure(
        connection,
        opts={
            'compare_type': True,
            # If true, server default comparison is enabled.
            # See: https://alembic.sqlalchemy.org/en/latest/api/runtime.html#alembic.runtime.environment.EnvironmentContext.configure.params.compare_server_default
            'compare_server_default': True,
            # If True, autogenerate will scan across all schemas located by the SQLAlchemy
            # See: https://alembic.sqlalchemy.org/en/latest/api/runtime.html#alembic.runtime.environment.EnvironmentContext.configure.params.include_schemas
            'include_schemas': False,
        }
    )
    
    # Compare the declared metadata with the actual database schema
    #
    # See https://alembic.sqlalchemy.org/en/latest/api/autogenerate.html#getting-diffs
    differences = compare_metadata(context, metadata)
    
    return differences

def _create_tables_if_new(engine):

    reflected_metadata = MetaData(schema='answers')
    reflected_metadata.reflect(bind=engine)

    if reflected_metadata.tables is not None and len(reflected_metadata.tables) > 0:
        logger.info('database is not empty. use formal migration tools.')
        return 


    alembic_ini = get_global_config().alembic_ini_path
    alembic_cfg = Config(file_=str(alembic_ini))

    logger.info('initializing database tables.')

    # Create database tables, indexes, etc.
    DECLARED_METADATA.create_all(engine)

    # Prepare this database for future upgrades by writing the alembic metadata.
    #
    # See https://alembic.sqlalchemy.org/en/latest/cookbook.html#building-an-up-to-date-database-from-scratch
    command.stamp(alembic_cfg, 'head')

    logger.info('initialized database tables.')

def _run_migrations(engine):

    alembic_ini = get_global_config().alembic_ini_path
    alembic_cfg = Config(file_=str(alembic_ini))

    # Upgrade to latest version
    logger.info('upgrading database.')
    try:
        command.upgrade(alembic_cfg, 'head')
    except Exception as ex:
        logger.warning('Error in migration', exc_info=ex)
    logger.info('upgraded database.')



def drop_all_tables():
    """Drops all tables for model objects defined with this module's `Base`.
    """
    logger.info('dropping all registered tables')
    engine = get_engine(DataDomain.ANSWERS)

    DECLARED_METADATA.drop_all(engine)


