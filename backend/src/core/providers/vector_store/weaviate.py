"""
This provides the vector store used by this application.
"""

import os
from functools import cache
import logging

from langchain_core.documents import Document
from langchain_weaviate import WeaviateVectorStore
from langchain_core.embeddings import Embeddings

from weaviate import WeaviateClient, connect_to_local
from weaviate.classes.config import Configure, Property, DataType, Tokenization, VectorDistances, VectorFilterStrategy
from weaviate.classes.init import AdditionalConfig, Timeout, Auth
from weaviate.classes.query import Filter
from weaviate.connect import ConnectionParams

from global_config import get_global_config

from ..embeddings import get_embeddings
from ...signals import start_up_handler, reset_data_handler

#
# See https://python.langchain.com/docs/integrations/vectorstores/pgvector/
#

logger = logging.getLogger(__name__)


_COLLECTION_NAME = 'Agent'
_TEXT_KEY = 'content'


@cache
def _get_client():
    config = get_global_config()

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
    if not client.collections.exists(_COLLECTION_NAME):
        # Create collection with ACORN filter strategy
        client.collections.create(
            'Agent',
            properties=[
                # Property(name='id', data_type=DataType.UUID,
                #          index_filterable=True, index_range_filters=False, index_searchable=False),
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
def get_vector_store():
    embeddings = get_embeddings()

    client = _get_client()

    vector_store = WeaviateVectorStore(
        client=client, index_name=_COLLECTION_NAME, text_key=_TEXT_KEY, embedding=embeddings
    )

    return vector_store


@start_up_handler
def startup(sender):
    if sender.is_worker:
        return

    get_vector_store()


@reset_data_handler
def reset(sender):
    if sender.is_worker:
        return

    client = _get_client()

    client.collections.delete(_COLLECTION_NAME)

    _create_collection(client)
