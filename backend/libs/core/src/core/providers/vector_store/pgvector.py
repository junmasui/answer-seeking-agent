"""This provides the vector store used by this application."""

import logging
import uuid
from functools import cache

from core_public.status_models import PingResult
from langchain_postgres import PGVector
from sqlalchemy import MetaData, select

from ...lib_config import get_lib_config
from ...signals import reset_data_handler, start_up_handler
from ..embeddings import get_embeddings
from ..sql_database import DataDomain, get_engine, get_sessionmaker, ping_sql_database

#
# See https://python.langchain.com/docs/integrations/vectorstores/pgvector/
#

logger = logging.getLogger(__name__)


@cache
def get_vector_store():
    """
    Get the cached PGVector vector store instance.

    Creates and returns a PGVector instance configured with embeddings and connected to the vectors
    database for storing and retrieving document embeddings.
    """
    engine = get_engine(DataDomain.VECTORS)

    collection_name = 'searchable_docs'

    embeddings = get_embeddings()

    vector_store = PGVector(embeddings=embeddings, collection_name=collection_name, connection=engine)

    return vector_store


@cache
def _get_reflected_metadata():
    """
    Get reflected metadata for vector store tables from the custom schema.

    Returns a MetaData object containing the langchain_pg_embedding and langchain_pg_collection
    tables reflected from the vectors database schema.
    """
    schema_name = get_lib_config().postgres_vectors_schema
    engine = get_engine(DataDomain.VECTORS)

    # Initialize metadata with schema context
    metadata = MetaData(schema=schema_name)

    # Reflect specific tables from the custom schema
    metadata.reflect(engine, only=['langchain_pg_embedding', 'langchain_pg_collection'], schema=schema_name)
    return metadata


@cache
def _get_reflected_embedding_table():
    """
    Get the reflected langchain_pg_embedding table from the custom schema.

    Returns the SQLAlchemy Table object for the langchain_pg_embedding table using schema-qualified
    name resolution from the reflected metadata.
    """
    schema_name = get_lib_config().postgres_vectors_schema
    metadata = _get_reflected_metadata()

    # Get table references using schema-qualified names
    embedding_table = metadata.tables[f'{schema_name}.langchain_pg_embedding']
    return embedding_table


def find_vectors_by_document_id(doc_id: uuid.UUID):
    """
    Find vector embedding UUIDs associated with a specific document ID.

    Returns a list of vector embedding UUID strings that belong to the specified parent document by
    querying the custom metadata field 'parent_document_id'.
    """
    embedding_table = _get_reflected_embedding_table()

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        # Build a select statement filtering on cmetadata ->> 'parent_document_id'
        stmt = select(embedding_table.c.uuid).where(
            embedding_table.c.cmetadata.op('->>')('parent_document_id') == str(doc_id)
        )

        # Execute the query
        result = session.execute(stmt)

        # `fetchall` must be called inside the session context.
        return [str(row[0]) for row in result.fetchall()]


def delete_vectors_by_document_id(doc_id: uuid.UUID):
    """
    Delete all vector embeddings associated with a specific document ID.

    Finds and removes all vector embeddings that belong to the specified parent document from the
    vector store by first querying for their IDs.
    """
    vector_ids = find_vectors_by_document_id(doc_id)

    vector_store = get_vector_store()

    if len(vector_ids) > 0:
        vector_store.delete(ids=vector_ids)


@start_up_handler
async def startup(sender):
    """
    Initialize the vector store database schema on application startup.

    Creates the vector extension, tables, and collection if they don't exist. Only runs on non-
    worker processes to avoid duplicate initialization.
    """
    if sender.is_worker:
        return

    vector_store = get_vector_store()

    vector_store.create_vector_extension()
    vector_store.create_tables_if_not_exists()
    vector_store.create_collection()


@reset_data_handler
async def reset(sender):
    """
    Reset the vector store by dropping and recreating all tables and collections.

    Called during data reset operations to clean up all vector store data. Only runs on non-worker
    processes to avoid conflicts.
    """
    if sender.is_worker:
        return

    vector_store = get_vector_store()

    vector_store.drop_tables()

    vector_store.create_vector_extension()
    vector_store.create_tables_if_not_exists()
    vector_store.create_collection()


def ping_vector_store():
    """Pings the vector store to check its health."""
    ping_result: PingResult = ping_sql_database(DataDomain.VECTORS)
    return ping_result
