import uuid
from typing import Iterable

from sqlalchemy import delete

from core_db.db_models import DbTrackedDocumentChunk
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker


async def replace_document_chunks(doc_uuid: uuid.UUID | str, chunk_data: Iterable[tuple[str, int | None]]) -> None:
    """Replace tracked document chunks for a document."""
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.AGENT)

    async with sessionmaker() as session:
        async with session.begin():
            await session.execute(
                delete(DbTrackedDocumentChunk).where(DbTrackedDocumentChunk.tracked_document_id == doc_uuid)
            )

            for vector_id, page_number in chunk_data:
                session.add(
                    DbTrackedDocumentChunk(
                        id=uuid.uuid4(), tracked_document_id=doc_uuid, vector_id=vector_id, page_number=page_number
                    )
                )
