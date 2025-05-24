"""
This provides the vector store used by this application.
"""

import logging
from functools import cache

from langchain_postgres import PGVector

from ...signals import reset_data_handler, start_up_handler
from ..embeddings import get_embeddings
from ..sql_database import DataDomain, get_engine

#
# See https://python.langchain.com/docs/integrations/vectorstores/pgvector/
#

logger = logging.getLogger(__name__)


@cache
def get_vector_store():
    engine = get_engine(DataDomain.VECTORS)

    collection_name = 'searchable_docs'

    embeddings = get_embeddings()

    vector_store = PGVector(embeddings=embeddings, collection_name=collection_name, connection=engine)

    return vector_store


@start_up_handler
def startup(sender):
    if sender.is_worker:
        return

    vector_store = get_vector_store()

    vector_store.create_vector_extension()
    vector_store.create_tables_if_not_exists()
    vector_store.create_collection()


@reset_data_handler
def reset(sender):
    if sender.is_worker:
        return

    vector_store = get_vector_store()

    vector_store.drop_tables()

    vector_store.create_vector_extension()
    vector_store.create_tables_if_not_exists()
    vector_store.create_collection()
