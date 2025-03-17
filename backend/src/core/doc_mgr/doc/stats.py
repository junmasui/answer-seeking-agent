import logging

from sqlalchemy import func

from sqlalchemy import select, func

from ...providers.sql_database import get_sessionmaker, DataDomain
from ...public_models import DocumentStats

from ..model import TrackedDocument



logger = logging.getLogger(__name__)

def get_document_statistics():

    table_stats = _get_tracking_stats()

    return DocumentStats(
        document_count = table_stats['doc_count'],
        table_updated_time = table_stats['max_update_time']
    )



def _get_tracking_stats():
    """Return the count of records and maximum updated_date time
    in the tracking table.
    """

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        stmt = select(
            func.count().label('doc_count'),
            func.max(TrackedDocument.update_time).label('max_update_time')
        )
        result = session.execute(stmt).first()
    return {
        'doc_count': result[0],
        'max_update_time': result[1]
    }
