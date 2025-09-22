from core_db.db_models import DbTrackedDocument
from core_db.providers.sql_database import DataDomain, get_sessionmaker
from sqlalchemy import func, select


def get_tracking_stats():
    """Return the count of records and maximum updated_date time in the tracking table."""
    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        stmt = select(func.count().label('doc_count'), func.max(DbTrackedDocument.update_time).label('max_update_time'))
        result = session.execute(stmt).first()
    return {'doc_count': result[0], 'max_update_time': result[1]}