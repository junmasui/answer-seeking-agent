import logging

from core_db.db_models import DbTrackedDocumentSet
from core_db.providers.sql_database import DataDomain, get_sessionmaker
from core_public import DocumentSetStats
from sqlalchemy import func, select

logger = logging.getLogger(__name__)


def get_document_set_statistics():
    """
    Get statistics about the document sets table.

    Returns a DocumentSetStats object containing the total count of document sets and the last
    update time from the tracking table.
    """
    table_stats = _get_document_set_stats()

    return DocumentSetStats(
        document_set_count=table_stats['doc_set_count'], table_updated_time=table_stats['max_update_time']
    )


def _get_document_set_stats():
    """Return the count of records and maximum updated_date time in the document set table."""
    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        stmt = select(
            func.count().label('doc_set_count'), func.max(DbTrackedDocumentSet.update_time).label('max_update_time')
        )
        result = session.execute(stmt).first()
    return {'doc_set_count': result[0], 'max_update_time': result[1]}
