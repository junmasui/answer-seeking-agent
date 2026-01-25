import uuid
from typing import Sequence

from sqlalchemy import select

from core_db.db_models import DbTrackedDocumentChunk
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker


async def list_document_chunks(doc_uuid: uuid.UUID | str) -> Sequence[DbTrackedDocumentChunk]:
    """Return tracked document chunks for a document."""
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        stmt = select(DbTrackedDocumentChunk).where(DbTrackedDocumentChunk.tracked_document_id == doc_uuid)
        result = await session.execute(stmt)
        return result.scalars().all()


async def list_document_chunk_vector_ids(doc_uuid: uuid.UUID | str) -> list[str]:
    """Return vector IDs for tracked document chunks."""
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        stmt = select(DbTrackedDocumentChunk.vector_id).where(DbTrackedDocumentChunk.tracked_document_id == doc_uuid)
        result = await session.execute(stmt)
        return [row[0] for row in result.fetchall()]
