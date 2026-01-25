"""This provides the vector store used by this application."""

import logging
from functools import cache

import uuid

from core_db.doc_mgr.doc_chunk.query import list_document_chunk_vector_ids
from core_db.providers.sql_database import DataDomain, get_async_engine, ping_async_sql_database
from core_public.status_models import PingResult
from langchain_postgres import PGVector
from sqlalchemy import MetaData

from ...lib_config import get_lib_config
from ...signals import reset_data_handler, start_up_handler
from ..embeddings import get_embeddings

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
    engine = get_async_engine(DataDomain.VECTORS)

    collection_name = 'searchable_docs'

    embeddings = get_embeddings()

    vector_store = PGVector(embeddings=embeddings, collection_name=collection_name, connection=engine)

    return vector_store


_METADATA_CACHE = None


async def _get_reflected_metadata():
    """
    Get reflected metadata for vector store tables from the custom schema.

    Returns a MetaData object containing the langchain_pg_embedding and langchain_pg_collection
    tables reflected from the vectors database schema.
    """
    global _METADATA_CACHE
    if _METADATA_CACHE:
        return _METADATA_CACHE

    schema_name = get_lib_config().postgres_vectors_schema
    engine = get_async_engine(DataDomain.VECTORS)

    # Initialize metadata with schema context
    metadata = MetaData(schema=schema_name)

    def _reflect(conn):
        # Reflect specific tables from the custom schema
        metadata.reflect(conn, only=['langchain_pg_embedding', 'langchain_pg_collection'], schema=schema_name)
        return metadata

    async with engine.connect() as conn:
        await conn.run_sync(_reflect)

    _METADATA_CACHE = metadata
    return metadata


async def _get_reflected_embedding_table():
    """
    Get the reflected langchain_pg_embedding table from the custom schema.

    Returns the SQLAlchemy Table object for the langchain_pg_embedding table using schema-qualified
    name resolution from the reflected metadata.
    """
    schema_name = get_lib_config().postgres_vectors_schema
    metadata = await _get_reflected_metadata()

    # Get table references using schema-qualified names
    embedding_table = metadata.tables[f'{schema_name}.langchain_pg_embedding']
    return embedding_table


async def find_vectors_by_document_id(doc_id: uuid.UUID):
    """
    Find vector embedding UUIDs associated with a specific document ID.

    Returns a list of vector embedding UUID strings that belong to the specified tracked document by
    querying the tracked document chunks table.
    """
    return await list_document_chunk_vector_ids(doc_id)


async def delete_vectors_by_document_id(doc_id: uuid.UUID):
    """
    Delete all vector embeddings associated with a specific document ID.

    Finds and removes all vector embeddings that belong to the specified parent document from the
    vector store by first querying for their IDs.
    """
    vector_ids = await find_vectors_by_document_id(doc_id)

    vector_store = get_vector_store()

    if len(vector_ids) > 0:
        await vector_store.adelete(ids=vector_ids)


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

    # Use async methods for setup since we are using an async engine.
    await vector_store.acreate_vector_extension()
    await vector_store.acreate_tables_if_not_exists()
    await vector_store.acreate_collection()


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


async def ping_vector_store():
    """Pings the vector store to check its health."""
    ping_result: PingResult = await ping_async_sql_database(DataDomain.VECTORS)
    return ping_result
