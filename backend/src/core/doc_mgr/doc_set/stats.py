import logging

from sqlalchemy import func

from sqlalchemy import select, func

from ...providers.sql_database import get_sessionmaker
from ...public_models import DocumentSetStats

from ..model import TrackedDocumentSet



logger = logging.getLogger(__name__)

def get_document_set_statistics():

    table_stats = _get_document_set_stats()

    return DocumentSetStats(
        document_set_count = table_stats['doc_set_count'],
        table_updated_time = table_stats['max_update_time']
    )



def _get_document_set_stats():
    """Return the count of records and maximum updated_date time
    in the document set table.
    """

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:
        stmt = select(
            func.count().label('doc_set_count'),
            func.max(TrackedDocumentSet.update_time).label('max_update_time')
        )
        result = session.execute(stmt).first()
    return {
        'doc_set_count': result[0],
        'max_update_time': result[1]
    }
