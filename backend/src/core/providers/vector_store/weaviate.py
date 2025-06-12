"""This provides the vector store used by this application."""

import logging
import uuid
from functools import cache

from langchain_weaviate import WeaviateVectorStore
from weaviate import connect_to_local
from weaviate.classes.config import Configure, DataType, Property, Tokenization, VectorDistances, VectorFilterStrategy
from weaviate.classes.init import AdditionalConfig, Auth, Timeout
from weaviate.classes.query import Filter

from ...lib_config import get_lib_config
from ...signals import reset_data_handler, start_up_handler
from ..embeddings import get_embeddings
from ..status_models import PingResult, PingStatus

#
# See https://python.langchain.com/docs/integrations/vectorstores/pgvector/
#

logger = logging.getLogger(__name__)


_COLLECTION_NAME = 'DocEmbeddings'
_TEXT_KEY = 'content'


@cache
def _get_client():
    """
    Return a Weaviate client instance, creating it if necessary.

    This function is cached to ensure only one client is created. It also ensures the
    'DocEmbeddings' collection exists.
    """
    config = get_lib_config()

    client_secret = Auth.api_key(config.weaviate_api_key)

    client = connect_to_local(
        host=config.weaviate_host,
        port=config.weaviate_http_port,
        grpc_port=config.weaviate_grpc_port,
        additional_config=AdditionalConfig(
            timeout=Timeout(init=30, query=60, insert=120)  # Values in seconds
        ),
        auth_credentials=client_secret,
    )

    _create_collection(client)

    return client


def _create_collection(client):
    """
    Create the 'DocEmbeddings' collection in Weaviate if it doesn't already exist.

    Defines the schema for the collection, including properties and vector index configuration.
    """
    if not client.collections.exists(_COLLECTION_NAME):
        # Create collection with ACORN filter strategy
        client.collections.create(
            _COLLECTION_NAME,
            properties=[
                Property(
                    name=_TEXT_KEY,
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_range_filters=False,
                    index_searchable=True,
                    tokenization=Tokenization.WORD,
                ),
                Property(
                    name='content_type',
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_range_filters=False,
                    index_searchable=True,
                    tokenization=Tokenization.FIELD,
                ),
                Property(
                    name='document_id',
                    data_type=DataType.UUID,
                    index_filterable=True,
                    index_range_filters=False,
                    index_searchable=False,
                ),
                Property(
                    name='document_set_id',
                    data_type=DataType.UUID,
                    index_filterable=True,
                    index_range_filters=False,
                    index_searchable=False,
                ),
                Property(
                    name='filetype',
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_range_filters=False,
                    index_searchable=True,
                    tokenization=Tokenization.FIELD,
                ),
                Property(
                    name='file_directory',
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_range_filters=False,
                    index_searchable=True,
                    tokenization=Tokenization.FIELD,
                ),
                Property(
                    name='filename',
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_range_filters=False,
                    index_searchable=True,
                    tokenization=Tokenization.FIELD,
                ),
                Property(
                    name='relative_path',
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_range_filters=False,
                    index_searchable=True,
                    tokenization=Tokenization.FIELD,
                ),
                Property(
                    name='source_url',
                    data_type=DataType.TEXT,
                    index_filterable=True,
                    index_range_filters=False,
                    index_searchable=True,
                    tokenization=Tokenization.FIELD,
                ),
                # Add other properties as needed
            ],
            vector_index_config=Configure.VectorIndex.hnsw(
                distance_metric=VectorDistances.COSINE,
                ef_construction=128,  # Tune based on your needs
                max_connections=64,  # Tune based on your needs
                filter_strategy=VectorFilterStrategy.ACORN,  # Enable ACORN strategy
            ),
        )


@cache
def _get_collection():
    """
    Return the Weaviate 'Agent' collection instance.

    This function is cached to ensure only one collection reference is created.
    """
    client = _get_client()

    collection = client.collections.get(_COLLECTION_NAME)

    return collection


@cache
def get_vector_store():
    """
    Return a WeaviateVectorStore instance, configured with embeddings and the Weaviate client.

    This function is cached to ensure only one vector store is created.
    """
    embeddings = get_embeddings()

    client = _get_client()

    vector_store = WeaviateVectorStore(
        client=client, index_name=_COLLECTION_NAME, text_key=_TEXT_KEY, embedding=embeddings
    )

    return vector_store


def find_vectors_by_document_id(doc_id: uuid.UUID):
    """
    Find vector embedding UUIDs associated with a specific document ID.

    Returns a list of vector embedding UUID strings that belong to the specified parent document by
    querying the custom metadata field 'parent_document_id'.
    """
    collection = _get_collection()

    ids = []
    batch_size = 50
    offset = 0
    while True:
        query_response = collection.query.fetch_objects(
            filters=Filter.by_property('document_id').equal(str(doc_id)), limit=batch_size, offset=offset
        )

        if len(query_response.objects) == 0:
            break

        batch_ids = [obj.uuid for obj in query_response.objects]
        ids.extend(batch_ids)
        offset = offset + batch_size

    return ids


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


def ping_vector_store() -> PingResult:
    """
    Pings the Weaviate vector store to check its health and connectivity.

    This function attempts to connect to the Weaviate instance and performs a health check.
    It verifies if the server is live and if the designated collection exists.

    Returns:
        PingResult: An object containing the ping status (GOOD or BAD),
                    a descriptive message, and an optional error message if the ping failed.
    """
    try:
        client = _get_client()
        if client.is_live():
            # Additionally, check if the collection exists as a more thorough check
            if client.collections.exists(_COLLECTION_NAME):
                collection = client.collections.get(_COLLECTION_NAME)
                count_response = collection.aggregate.over_all(total_count=True)
                count = count_response.total_count
                return PingResult(
                    status=PingStatus.GOOD,
                    message=f"Weaviate server is live and collection '{_COLLECTION_NAME}' exists with {count} records.",
                    statistics={'vector_count': count},
                )
            else:
                return PingResult(
                    status=PingStatus.BAD,
                    message=f"Weaviate server is live but collection '{_COLLECTION_NAME}' does not exist.",
                )
        else:
            return PingResult(status=PingStatus.BAD, message='Weaviate server is not live.')
    except Exception as e:
        logger.error('Weaviate ping failed', exc_info=e)
        return PingResult(
            status=PingStatus.BAD, message='Failed to connect to Weaviate or perform check.', error=str(e)
        )


@start_up_handler
def startup(sender):
    """Initialize the vector store on application startup if not a worker process."""
    if sender.is_worker:
        return

    get_vector_store()


@reset_data_handler
def reset(sender):
    """Reset the Weaviate collection by deleting and recreating it if not a worker process."""
    if sender.is_worker:
        return

    client = _get_client()

    client.collections.delete(_COLLECTION_NAME)

    _create_collection(client)
