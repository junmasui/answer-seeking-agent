import logging

from sqlalchemy import func, select

from ...db_models import DbTrackedDocument
from ...providers.sql_database import DataDomain, get_sessionmaker
from ...public_models import DocumentStats

logger = logging.getLogger(__name__)


def get_document_statistics():
    """
    Get statistics about the tracked documents table.

    Returns a DocumentStats object containing the total count of documents and the last update time
    from the tracking table.
    """
    table_stats = _get_tracking_stats()

    return DocumentStats(document_count=table_stats['doc_count'], table_updated_time=table_stats['max_update_time'])


def _get_tracking_stats():
    """Return the count of records and maximum updated_date time in the tracking table."""
    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        stmt = select(func.count().label('doc_count'), func.max(DbTrackedDocument.update_time).label('max_update_time'))
        result = session.execute(stmt).first()
    return {'doc_count': result[0], 'max_update_time': result[1]}
