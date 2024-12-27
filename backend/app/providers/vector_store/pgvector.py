"""
This provides the vector store used by this application.
"""
import os
from functools import cache
import string

from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector

from ..embeddings import get_embeddings
from ..sql_database import get_engine

#
# See https://python.langchain.com/docs/integrations/vectorstores/pgvector/
#

@cache
def get_vector_store():

    engine = get_engine()

    collection_name = 'searchable_docs'

    embeddings = get_embeddings()

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=engine,
    )

    return vector_store

