from sqlalchemy import func, select

from core_db.db_models import DbTrackedDocument
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker


async def get_tracking_stats():
    """Return the count of records and maximum updated_date time in the tracking table."""
    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        stmt = select(func.count().label('doc_count'), func.max(DbTrackedDocument.update_time).label('max_update_time'))
        result = await session.execute(stmt)
        result = result.first()
    return {'doc_count': result[0], 'max_update_time': result[1]}
