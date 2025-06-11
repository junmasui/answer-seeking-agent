import logging

from sqlalchemy import MetaData, text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

from ..lib_config import get_lib_config
from ..providers.sql_database import DataDomain, get_engine
from .base import DECLARED_METADATA

logger = logging.getLogger(__name__)


def create_tables_if_not_exists():
    """
    Create database tables if they do not already exist.

    This function checks the current state of the database. If the database
    has not been initialized, it creates all tables. If the database has been
    initialized but the schema version differs from the expected version, it
    runs Alembic migrations to update the schema. It also logs any detected
    differences between the declared SQLAlchemy models and the actual database schema.
    """
    logger.info('creating tables that are absent')

    engine = get_engine(DataDomain.ANSWERS)

    actual_schema_version = get_current_version(engine)
    expected_schema_version = get_head_revision()

    initialize = False
    migrate = False
    if actual_schema_version is None:
        logger.info('Database not yet initialized')
        initialize = True
    elif actual_schema_version != expected_schema_version:
        logger.info('Migration revisions differ')
        migrate = True
    else:
        differences = get_schema_differences(engine)

        # Analyze the differences
        if differences:
            logger.info('Actual and declared schemas differ')
            for diff in differences:
                diff_op = diff[0]
                diff_obj = diff[-1]
                if isinstance(diff_obj, str):
                    obj_name = diff_obj
                else:
                    obj_name = getattr(diff_obj, 'name', '')

                diff_table = getattr(diff_obj, 'table', None)
                table_name = getattr(diff_table, 'name', None)
                schema_name = getattr(diff_table, 'schema', None)

                if len(diff) >= 3:
                    schema_name = diff[1] if schema_name is None else schema_name
                    table_name = diff[2] if table_name is None else table_name

                logger.info('DB difference: %s %s %s %s', diff_op, obj_name, table_name, schema_name)

    if initialize:
        _create_tables_if_new(engine)
    if migrate:
        _run_migrations(engine)


def get_current_version(engine):
    """Return the current Alembic version applied to the database."""
    reflected_metadata = MetaData(schema='answers')
    reflected_metadata.reflect(bind=engine)

    if reflected_metadata.tables is None or len(reflected_metadata.tables) == 0:
        logger.info('database is empty.')
        return None

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
            return session.execute(text('SELECT version_num FROM alembic_version')).scalar()
        except NoResultFound:
            return None  # No migrations applied


def get_head_revision():
    """Return the head Alembic version of the defined migration steps."""
    alembic_ini = get_lib_config().alembic_ini_path
    alembic_cfg = Config(file_=str(alembic_ini))
    script = ScriptDirectory.from_config(alembic_cfg)
    head_revision = script.get_current_head()
    return head_revision


def get_schema_differences(engine):
    """
    Compare the declared database schema with the actual database schema.

    Uses Alembic's autogenerate functionality to detect differences between
    the SQLAlchemy metadata and the actual database schema, including
    table structure, columns, and server defaults.
    """
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
        },
    )

    # Compare the declared metadata with the actual database schema
    #
    # See https://alembic.sqlalchemy.org/en/latest/api/autogenerate.html#getting-diffs
    differences = compare_metadata(context, metadata)

    return differences


def _create_tables_if_new(engine):
    """
    Create database tables for a new/empty database and initialize Alembic tracking.

    Only creates tables if the database is empty (no reflected tables except alembic_version).
    After creating tables, stamps the database with the current Alembic head revision.
    """
    reflected_metadata = MetaData(schema='answers')
    reflected_metadata.reflect(bind=engine)

    reflected_tables = reflected_metadata.tables

    # Remove the alembic migration table from the reflected tables list.
    # Although not in the declared schema, this will show up in the actual schema,
    # and its appearance will cause the migrations to be short-circuited.
    if reflected_tables is not None:
        reflected_tables = [table for table in reflected_tables if table not in ['answers.alembic_version']]

    if reflected_tables is not None and len(reflected_tables) > 0:
        logger.info('database is not empty. use formal migration tools.')
        return

    alembic_ini = get_lib_config().alembic_ini_path
    alembic_cfg = Config(file_=str(alembic_ini))

    logger.info('initializing database tables.')

    # Create database tables.
    DECLARED_METADATA.create_all(engine)

    # Prepare this database for future upgrades by writing the alembic metadata.
    #
    # See https://alembic.sqlalchemy.org/en/latest/cookbook.html#building-an-up-to-date-database-from-scratch
    command.stamp(alembic_cfg, 'head')

    logger.info('initialized database tables.')


def _run_migrations(engine):
    """
    Run Alembic database migrations to upgrade to the latest schema version.

    Executes all pending migrations from the current database version to the head revision.
    Logs warnings if migration errors occur but allows the process to continue.
    """
    alembic_ini = get_lib_config().alembic_ini_path
    alembic_cfg = Config(file_=str(alembic_ini))

    # Upgrade to latest version
    logger.info('upgrading database.')
    try:
        command.upgrade(alembic_cfg, 'head')
    except Exception as ex:
        logger.warning('Error in migration', exc_info=ex)
    logger.info('upgraded database.')


def drop_all_tables():
    """Drops all tables for model objects defined with this module's `Base`."""
    logger.info('dropping all registered tables')
    engine = get_engine(DataDomain.ANSWERS)

    DECLARED_METADATA.drop_all(engine)

    # Reset the Alembic migration table. If this table remains populated, our migration detection
    # logic will prevent the recreation of the registered tables.
    with engine.connect() as conn:
        conn.execute(text('TRUNCATE TABLE "alembic_version" RESTART IDENTITY CASCADE'))
        conn.commit()
